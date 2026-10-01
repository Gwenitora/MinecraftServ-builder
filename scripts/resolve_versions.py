#!/usr/bin/env python3
"""
Resolveur de versions pour MinecraftServ-builder.

Interroge les API officielles de chaque loader et produit une liste de
"jobs" de build pour GitHub Actions (matrix), avec les tags Docker
associés.

Usage:
    python resolve_versions.py --loader paper --mode daily  > matrix.json
    python resolve_versions.py --loader forge --mode backfill --limit 200 > matrix.json

Modes:
    daily     -> ne renvoie que les versions "mouvantes" utiles à rafraichir
                 chaque jour (latest / snapshot / experimental de chaque
                 profondeur) + les versions MC jamais vues auparavant
                 (comparées à --state-file, un simple fichier texte listant
                 les tags déjà publiés).
    backfill  -> renvoie TOUTES les versions connues du loader (utile pour
                 le job manuel "backfill-all" qui reconstruit l'historique
                 complet, exécuté par petits lots via --limit/--offset).

Séparateur version-loader dans les tags: "_" (ex: 1.21.2_40.1.80)
"""
import argparse
import datetime
import json
import re
import sys
import urllib.parse
import urllib.request

UA = {"User-Agent": "MinecraftServ-builder/1.0 (+https://github.com/Gwenitora/MinecraftServ-builder)"}
SEP = "_"


def http_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def http_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def url_segment(s):
    """Encode un segment de chemin d'URL (ex: 'id' de version Minecraft
    interpolé dans un template). Certains identifiants Mojang/loader
    contiennent des espaces ("1.14 Pre-Release 1") ou d'autres caractères
    invalides dans une URL/requête HTTP brute (curl les rejette avec
    "Malformed input to a URL function")."""
    return urllib.parse.quote(s, safe="")


# ---------------------------------------------------------------------------
# Classification générique
# ---------------------------------------------------------------------------

def mc_channel_from_type(t):
    """Mappe le type Mojang vers un des 3 canaux exposés en tag Docker."""
    if t == "release":
        return "latest"
    if t == "snapshot":
        return "snapshot"
    # old_beta / old_alpha -> versions historiques/expérimentales de MC
    return "experimental"


def loader_channel_from_string(v):
    v = v.lower()
    if any(k in v for k in ("beta", "rc", "pre", "alpha", "snapshot", "unstable", "craftmine")):
        return "experimental"
    return "latest"


def sanitize_tag(tag):
    """Un tag Docker n'autorise que [A-Za-z0-9_.-] et doit commencer par un
    alphanumérique/underscore. Certains identifiants de version (ex: Mojang
    "1.14 Pre-Release 1", "3D Shareware v1.34") contiennent des espaces ou
    d'autres caractères invalides : on les remplace plutôt que de laisser
    `docker buildx build -t ...` planter sur un tag malformé."""
    t = re.sub(r"[^A-Za-z0-9_.-]", "-", tag)
    if not re.match(r"^[A-Za-z0-9_]", t):
        t = "v" + t
    return t


def _mc_version_tuple(mc_version):
    """Parse le préfixe numérique pointé d'une version MC ("1.5.2" -> (1,5,2)).
    Retourne None si non parsable (snapshots/alias non numériques)."""
    parts = []
    for p in mc_version.split("."):
        if not p.isdigit():
            return None
        parts.append(int(p))
    return tuple(parts) if parts else None


def depth_tags(mc_version):
    """1.21.2 -> ['1', '1.21', '1.21.2'] ; 26.3 -> ['26', '26.3']
    Ignoré si une partie n'est pas purement numérique (pre/rc/snapshots)."""
    parts = mc_version.split(".")
    if not all(p.isdigit() for p in parts):
        return []
    out = []
    for i in range(1, len(parts) + 1):
        out.append(".".join(parts[:i]))
    return out


def java_for_mc(mc_version):
    """Heuristique Java requise selon la version MC (releases modernes)."""
    parts = re.findall(r"\d+", mc_version)
    nums = [int(p) for p in parts[:3]] if parts else []
    if not nums:
        return "21"
    major = nums[0]
    minor = nums[1] if len(nums) > 1 else 0
    # nouveau schéma calendaire (>= 20.x hors "1.x") -> Java 21
    if major >= 20 and major != 1:
        return "21"
    if major == 1:
        if minor >= 21:
            return "21"
        if minor >= 18:
            return "17"
        if minor >= 17:
            return "17"
        if minor >= 12:
            return "11"
        return "8"
    return "21"


def version_sort_key(v):
    """Clé de tri approximative basée sur les nombres présents dans la
    chaîne de version (ex: '1.21.2' -> (1, 21, 2, 0, 0, 0)). Sert de repli
    quand aucune date de publication réelle n'est disponible."""
    nums = [int(x) for x in re.findall(r"\d+", v)]
    nums = (nums + [0] * 6)[:6]
    return tuple(nums)


def entry_sort_key(e):
    """Clé de tri chronologique d'une entrée (mc_version). Utilise la date
    de sortie réelle quand elle est connue (vanilla, via Mojang), sinon
    l'ordre naturel des numéros de version."""
    rt = e.get("release_time")
    ts = 0.0
    if rt:
        try:
            ts = datetime.datetime.fromisoformat(rt.replace("Z", "+00:00")).timestamp()
        except Exception:
            ts = 0.0
    return (ts, version_sort_key(e["mc_version"]))


def job_sort_key(e, loader_id):
    return entry_sort_key(e) + (version_sort_key(loader_id),)


# ---------------------------------------------------------------------------
# Providers: chacun retourne une liste de
# {mc_version, mc_channel, java, loaders: [{id, channel, build_args}]}
# ---------------------------------------------------------------------------

# Avant la 1.2.5 (29/03/2012), le manifeste Mojang ne publie aucun jar
# serveur dédié (champ "downloads.server" absent) : tout old_alpha, tout
# old_beta, et les releases 1.0 à 1.2.4 n'ont qu'un client. Vérifié
# exhaustivement sur les 35 versions old_alpha + les releases 1.0-1.2.4 : le
# champ est systématiquement absent avant, systématiquement présent à partir
# de 1.2.5. On exclut donc ces versions plutôt que de planter le build (le
# Dockerfile ferait échouer un `curl` sur une URL "null").
VANILLA_MIN_RELEASE_TIME = "2012-03-29T22:00:00+00:00"


def _parse_iso(ts):
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def provider_vanilla():
    data = http_json("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json")
    cutoff = _parse_iso(VANILLA_MIN_RELEASE_TIME)
    out = []
    for v in data["versions"]:
        rt = v.get("releaseTime")
        if rt and _parse_iso(rt) < cutoff:
            continue
        ch = mc_channel_from_type(v["type"])
        out.append({
            "mc_version": v["id"],
            "mc_channel": ch,
            "java": java_for_mc(v["id"]),
            "release_time": rt,
            "loaders": [{
                "id": v["id"],
                "channel": ch,
                "build_args": {"MANIFEST_URL": v["url"]},
            }],
        })
    return out


def _spigot_bukkit_versions():
    html = http_text("https://hub.spigotmc.org/versions/")
    ids = re.findall(r'href="([\w.\-]+)\.json"', html)
    return sorted({i for i in ids if i != "latest"})


# "1.8" et "1.8.3" dépendent (via spigot-api) de
# net.md-5:bungeecord-chat:1.8-SNAPSHOT. Ce snapshot n'a jamais été promu en
# release et a depuis été purgé de tous les dépôts Sonatype/mirrors connus
# (oss.sonatype.org, hub.spigotmc.org, repo.phoenix616.dev... tous en 404) :
# la résolution Maven échoue donc définitivement. "1.8.4" à "1.8.8"
# partagent le même BuildData (build "582b", vérifié via
# hub.spigotmc.org/versions/<v>.json) et compilent sans problème (testé:
# 1.8.4 et 1.8.8) ; seules "1.8" (build legacy) et "1.8.3" (build "422") ont
# un pin différent et cassé. CraftBukkit (bukkit), qui ne dépend pas de
# bungeecord-chat, n'est pas affecté.
SPIGOT_BROKEN_VERSIONS = {"1.8", "1.8.3"}


def provider_spigot():
    return _provider_buildtools(exclude=SPIGOT_BROKEN_VERSIONS)


def provider_bukkit():
    return _provider_buildtools()


def _provider_buildtools(exclude=frozenset()):
    out = []
    for mc in _spigot_bukkit_versions():
        if mc in exclude:
            continue
        ch = "latest"
        if re.search(r"(pre|rc)", mc):
            ch = "snapshot"
        out.append({
            "mc_version": mc,
            "mc_channel": ch,
            "java": java_for_mc(mc),
            "loaders": [{"id": mc, "channel": ch, "build_args": {"BUILDTOOLS_REV": mc}}],
        })
    return out


def provider_paper():
    data = http_json("https://fill.papermc.io/v3/projects/paper")
    out = []
    for family, versions in data["versions"].items():
        for mc in versions:
            ch = "snapshot" if re.search(r"(pre|rc)", mc) else "latest"
            builds = http_json(f"https://fill.papermc.io/v3/projects/paper/versions/{url_segment(mc)}/builds")
            loaders = []
            for b in builds:
                dl = b.get("downloads", {}).get("server:default")
                if not dl:
                    continue
                lch = "latest" if b.get("channel", "STABLE").upper() == "STABLE" else "experimental"
                loaders.append({"id": str(b["id"]), "channel": lch, "build_args": {"JAR_URL": dl["url"]}})
            if loaders:
                out.append({"mc_version": mc, "mc_channel": ch, "java": java_for_mc(mc), "loaders": loaders})
    return out


def provider_forge():
    return _provider_forge_like(
        "https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml",
        installer_url_tpl="https://maven.minecraftforge.net/net/minecraftforge/forge/{full}/forge-{full}-installer.jar",
    )


# "20.4.0-beta" embarque un installeur dont la vérification de connectivité
# réseau (net.minecraftforge.installer.SimpleInstaller.getIps) interroge
# entre autres "authserver.mojang.com" ; ce nom a un CNAME vers une
# distribution CloudFront aujourd'hui supprimée (NXDOMAIN confirmé), donc la
# vérification échoue toujours et l'installeur plante avec un
# NullPointerException avant même de démarrer l'installation. Toutes les
# autres versions testées autour (20.2.3-beta, 20.3.1-beta, 20.5.0-beta,
# 20.6.1-beta, 20.4.167, 21.0.0-beta) construisent sans problème : c'est un
# artefact isolé et définitivement cassé en amont, pas un bug de notre côté.
NEOFORGE_BROKEN_VERSIONS = {"20.4.0-beta"}


def provider_neoforge():
    data = http_json("https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge")
    out = {}
    for v in data["versions"]:
        if v in NEOFORGE_BROKEN_VERSIONS:
            continue
        m = re.match(r"^(\d+)\.(\d+)\.", v)
        if not m:
            continue
        major, minor = m.group(1), m.group(2)
        mc = f"1.{major}" if minor == "0" else f"1.{major}.{minor}"
        ch = loader_channel_from_string(v)
        entry = out.setdefault(mc, {"mc_version": mc, "mc_channel": "latest", "java": java_for_mc(mc), "loaders": []})
        entry["loaders"].append({
            "id": v, "channel": ch,
            "build_args": {"INSTALLER_URL": f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{url_segment(v)}/neoforge-{url_segment(v)}-installer.jar"},
        })
    return list(out.values())


# Avant MC 1.5.2, Forge ne publiait pas de "-installer.jar" mais des
# "-server.zip"/"-client.zip" (format legacy, binaire patché différemment).
# Ces versions ne peuvent pas être construites par notre Dockerfile actuel
# (basé sur l'installeur) et sont donc explicitement exclues plutôt que de
# planter le build. Vérifié: 1.5.2-7.8.0.684 est la 1ère build avec un
# installer.jar (200), tout ce qui est strictement avant 1.5.2 renvoie 404.
#
# MC 1.5.2 elle-même est en plus exclue : son FML ("relauncher") télécharge
# au 1er lancement des libs (argo, guava, scala-library, deobfuscation
# data...) depuis http://files.minecraftforge.net/fmllibs/, un hôte
# définitivement mort (404 confirmé) — le serveur ne peut donc jamais
# démarrer, même si le build Docker réussit. À partir de 1.6.x ces libs sont
# embarquées directement (testé/validé en local sur 1.6.1/1.6.2/1.6.4).
MIN_FORGE_INSTALLER_MC = (1, 6, 0)


# Avant 1.13, Forge utilise l'ancien "FML/launchwrapper" qui repose sur un
# cast explicite vers java.net.URLClassLoader (system classloader). Retiré
# en Java 9+ (remplacé par un classloader interne non castable), ce qui
# plante le serveur au démarrage avec un ClassCastException, même si le
# build Docker réussit (vérifié en local sur 1.12.2 avec Java 11 : crash
# immédiat "AppClassLoader cannot be cast to URLClassLoader"). On force donc
# Java 8 pour toutes ces versions, indépendamment de l'heuristique générale
# `java_for_mc` (qui elle vaut pour Vanilla/Bukkit/Spigot, pas affectés par
# ce problème spécifique à l'ancien launcher Forge).
FORGE_LEGACY_LAUNCHER_MAX_MC = (1, 13, 0)


def _provider_forge_like(metadata_url, installer_url_tpl):
    xml = http_text(metadata_url)
    versions = re.findall(r"<version>([^<]+)</version>", xml)
    out = {}
    for v in versions:
        if "-" not in v:
            continue
        mc, loader = v.split("-", 1)
        mc_tuple = _mc_version_tuple(mc)
        if mc_tuple is not None and mc_tuple < MIN_FORGE_INSTALLER_MC:
            continue
        java = "8" if mc_tuple is not None and mc_tuple < FORGE_LEGACY_LAUNCHER_MAX_MC else java_for_mc(mc)
        ch = loader_channel_from_string(loader)
        entry = out.setdefault(mc, {"mc_version": mc, "mc_channel": "latest", "java": java, "loaders": []})
        entry["loaders"].append({
            "id": loader, "channel": ch,
            "build_args": {"INSTALLER_URL": installer_url_tpl.format(full=url_segment(v))},
        })
    return list(out.values())


def provider_fabric():
    """Fabric expose un endpoint officiel qui fournit directement le jar
    serveur fusionné (loader + mappings intermédiaires), vérifié fonctionnel."""
    game_url = "https://meta.fabricmc.net/v2/versions/game"
    loader_url = "https://meta.fabricmc.net/v2/versions/loader"
    installer_url = "https://meta.fabricmc.net/v2/versions/installer"
    jar_url_tpl = "https://meta.fabricmc.net/v2/versions/loader/{game}/{loader}/{installer}/server/jar"

    games = http_json(game_url)
    loaders = http_json(loader_url)
    installers = http_json(installer_url)
    stable_installer = next((i["version"] for i in installers if i.get("stable")), installers[0]["version"])
    out = []
    for g in games:
        mc = g["version"]
        ch = "latest" if g.get("stable") else "snapshot"
        entries = []
        for l in loaders:
            lch = "latest" if l.get("stable") else "experimental"
            entries.append({
                "id": l["version"], "channel": lch,
                "build_args": {"JAR_URL": jar_url_tpl.format(game=url_segment(mc), loader=url_segment(l["version"]), installer=url_segment(stable_installer))},
            })
        out.append({"mc_version": mc, "mc_channel": ch, "java": java_for_mc(mc), "loaders": entries})
    return out


def provider_quilt():
    """Quilt n'expose PAS d'endpoint "server/jar" prêt à l'emploi (contrairement
    à Fabric) : il faut exécuter le quilt-installer au moment du build, qui
    télécharge lui-même le serveur vanilla et merge le loader
    (cf. docker/quilt/Dockerfile). On fournit donc juste l'URL de
    l'installeur ; MC_VERSION/LOADER_VERSION sont déjà passés par ailleurs.
    Les entrées du loader n'ont pas de champ "stable" exploitable dans cette
    API (contrairement à Fabric) : on déduit le canal du nom de version."""
    games = http_json("https://meta.quiltmc.org/v3/versions/game")
    loaders = http_json("https://meta.quiltmc.org/v3/versions/loader")
    installers = http_json("https://meta.quiltmc.org/v3/versions/installer")
    installer_url_by_version = {i["version"]: i["url"] for i in installers}
    stable_installer = installers[0]["version"]
    installer_url = installer_url_by_version[stable_installer]

    out = []
    for g in games:
        mc = g["version"]
        ch = "latest" if g.get("stable") else "snapshot"
        entries = []
        for l in loaders:
            lch = loader_channel_from_string(l["version"])
            entries.append({
                "id": l["version"], "channel": lch,
                "build_args": {"INSTALLER_URL": installer_url},
            })
        out.append({"mc_version": mc, "mc_channel": ch, "java": java_for_mc(mc), "loaders": entries})
    return out



PROVIDERS = {
    "vanilla": provider_vanilla,
    "paper": provider_paper,
    "bukkit": provider_bukkit,
    "spigot": provider_spigot,
    "forge": provider_forge,
    "neoforge": provider_neoforge,
    "fabric": provider_fabric,
    "quilt": provider_quilt,
}


# ---------------------------------------------------------------------------
# Construction des tags + jobs de build
# ---------------------------------------------------------------------------

def pick_default_loader(loaders, channel):
    """Loader 'par défaut' d'un canal donné = le plus récent de ce canal,
    sinon le plus récent tout court (fallback)."""
    cand = [l for l in loaders if l["channel"] == channel]
    pool = cand or loaders
    return pool[0] if pool else None


def pick_loader_strict(loaders, channel):
    """Comme pick_default_loader mais sans fallback: None si le canal
    demandé n'existe pas réellement pour ce loader (ex: pas de build
    'experimental' publié pour une version de Minecraft donnée)."""
    cand = [l for l in loaders if l["channel"] == channel]
    return cand[0] if cand else None


def build_jobs(loader_name, entries, mode, known_tags):
    """entries: sortie d'un provider. Retourne une liste de jobs matrix,
    triée par ordre chronologique d'apparition (plus ancien -> plus récent)."""
    # index par mc_version pour calculer les tags de profondeur "-snapshot"/"-experimental"
    by_channel = {"latest": [], "snapshot": [], "experimental": []}
    for e in entries:
        by_channel[e["mc_channel"]].append(e)
    for v in by_channel.values():
        v.sort(key=entry_sort_key, reverse=True)

    # dernière version release connue par profondeur, pour rattacher les
    # tags -snapshot/-experimental d'une profondeur donnée à la même branche
    jobs = {}

    def add_job(mc_version, loader_id, java, tags, build_args, sort_key):
        key = (mc_version, loader_id)
        j = jobs.setdefault(key, {
            "loader": loader_name, "mc_version": mc_version, "loader_version": loader_id,
            "java": java, "build_args": build_args, "tags": set(), "_sort_key": sort_key,
        })
        j["tags"].update(tags)

    global_latest_mc = by_channel["latest"][0] if by_channel["latest"] else None
    global_snapshot_mc = by_channel["snapshot"][0] if by_channel["snapshot"] else None
    global_experimental_mc = by_channel["experimental"][0] if by_channel["experimental"] else None

    for e in entries:
        mc = e["mc_version"]
        loaders = e["loaders"]
        default_loader = pick_default_loader(loaders, "latest")
        if not default_loader:
            continue

        # --- tag exact sans version de loader précisée = loader latest de cette mc version
        tags = {mc}
        # --- profondeurs (seulement pour les mc versions numériques pures, canal release)
        depths = depth_tags(mc) if e["mc_channel"] == "latest" else []
        for d in depths:
            tags.add(d)
            tags.add(f"{d}-latest")

        add_job(mc, default_loader["id"], e["java"], tags, default_loader["build_args"], job_sort_key(e, default_loader["id"]))

        # --- mots-clés de canal côté loader: "<mc>_latest" (alias du tag nu)
        # et "<mc>_experimental" quand un build expérimental du loader existe
        # réellement pour cette version de Minecraft.
        add_job(mc, default_loader["id"], e["java"], {f"{mc}{SEP}latest"}, default_loader["build_args"], job_sort_key(e, default_loader["id"]))
        exp_keyword_loader = pick_loader_strict(loaders, "experimental")
        if exp_keyword_loader:
            add_job(mc, exp_keyword_loader["id"], e["java"], {f"{mc}{SEP}experimental"}, exp_keyword_loader["build_args"], job_sort_key(e, exp_keyword_loader["id"]))

        # --- variantes explicites de version de loader: mc_loader
        if mode == "backfill":
            for l in loaders:
                if l is default_loader:
                    continue
                add_job(mc, l["id"], e["java"], {f"{mc}{SEP}{l['id']}"}, l["build_args"], job_sort_key(e, l["id"]))
        # en mode daily on limite aux loaders "latest"/"experimental" les plus récents
        elif mode == "daily":
            exp_loader = pick_default_loader(loaders, "experimental")
            if exp_loader and exp_loader is not default_loader:
                add_job(mc, exp_loader["id"], e["java"], {f"{mc}{SEP}{exp_loader['id']}"}, exp_loader["build_args"], job_sort_key(e, exp_loader["id"]))

    # --- tags globaux mouvants: latest / snapshot / experimental
    if global_latest_mc:
        e = global_latest_mc
        dl = pick_default_loader(e["loaders"], "latest")
        if dl:
            add_job(e["mc_version"], dl["id"], e["java"], {"latest", f"latest{SEP}latest"}, dl["build_args"], job_sort_key(e, dl["id"]))
        exp = pick_loader_strict(e["loaders"], "experimental")
        if exp:
            add_job(e["mc_version"], exp["id"], e["java"], {f"latest{SEP}experimental"}, exp["build_args"], job_sort_key(e, exp["id"]))
    if global_snapshot_mc:
        e = global_snapshot_mc
        dl = pick_default_loader(e["loaders"], "latest")
        if dl:
            add_job(e["mc_version"], dl["id"], e["java"], {"snapshot", f"snapshot{SEP}latest"}, dl["build_args"], job_sort_key(e, dl["id"]))
        exp = pick_loader_strict(e["loaders"], "experimental")
        if exp:
            add_job(e["mc_version"], exp["id"], e["java"], {f"snapshot{SEP}experimental"}, exp["build_args"], job_sort_key(e, exp["id"]))
    if global_experimental_mc:
        e = global_experimental_mc
        dl = pick_default_loader(e["loaders"], "latest")
        if dl:
            add_job(e["mc_version"], dl["id"], e["java"], {"experimental", f"experimental{SEP}latest"}, dl["build_args"], job_sort_key(e, dl["id"]))

    # --- tags de profondeur -snapshot / -experimental: on rattache la
    # dernière version snapshot/experimental connue à chaque profondeur de la
    # dernière release (best-effort, cf. README pour les limites de cette heuristique)
    if global_latest_mc:
        depths = depth_tags(global_latest_mc["mc_version"])
        if global_snapshot_mc:
            dl = pick_default_loader(global_snapshot_mc["loaders"], "latest")
            if dl:
                add_job(global_snapshot_mc["mc_version"], dl["id"], global_snapshot_mc["java"],
                        {f"{d}-snapshot" for d in depths}, dl["build_args"], job_sort_key(global_snapshot_mc, dl["id"]))
        if global_experimental_mc:
            dl = pick_default_loader(global_experimental_mc["loaders"], "latest")
            if dl:
                add_job(global_experimental_mc["mc_version"], dl["id"], global_experimental_mc["java"],
                        {f"{d}-experimental" for d in depths}, dl["build_args"], job_sort_key(global_experimental_mc, dl["id"]))

    result = list(jobs.values())
    for j in result:
        j["tags"] = {sanitize_tag(t) for t in j["tags"]}

    if mode == "daily":
        # ne garde que les jobs touchant au moins un tag encore jamais publié,
        # ou un tag mouvant (toujours republié pour rester à jour)
        moving = {"latest", "snapshot", "experimental"}
        filtered = []
        for j in result:
            j_tags = j["tags"]
            if j_tags & moving:
                filtered.append(j)
                continue
            if any(t.endswith(("-latest", "-snapshot", "-experimental")) for t in j_tags):
                filtered.append(j)
                continue
            if any(t not in known_tags for t in j_tags):
                filtered.append(j)
        result = filtered

    # ordre chronologique d'apparition (plus ancien -> plus récent) : essentiel
    # pour un build séquentiel où un échec doit arrêter les versions suivantes.
    result.sort(key=lambda j: j["_sort_key"])
    for j in result:
        j.pop("_sort_key", None)
        j["tags"] = sorted(j["tags"])
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loader", required=True, choices=PROVIDERS.keys())
    ap.add_argument("--mode", default="daily", choices=["daily", "backfill"])
    ap.add_argument("--state-file", default=None, help="fichier texte listant les tags déjà publiés (1 par ligne)")
    ap.add_argument("--limit", type=int, default=None, help="limite le nombre de jobs renvoyés (pagination backfill)")
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args()

    known_tags = set()
    if args.state_file:
        try:
            with open(args.state_file, encoding="utf-8") as f:
                known_tags = {l.strip() for l in f if l.strip()}
        except FileNotFoundError:
            pass

    entries = PROVIDERS[args.loader]()
    jobs = build_jobs(args.loader, entries, args.mode, known_tags)

    if args.limit is not None:
        jobs = jobs[args.offset:args.offset + args.limit]

    json.dump({"include": jobs}, sys.stdout)


if __name__ == "__main__":
    main()
