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
import json
import re
import sys
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
    # nouveau schéma calendaire (>= 26.x) -> Java 21
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


# ---------------------------------------------------------------------------
# Providers: chacun retourne une liste de
# {mc_version, mc_channel, java, loaders: [{id, channel, build_args}]}
# ---------------------------------------------------------------------------

def provider_vanilla():
    data = http_json("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json")
    out = []
    for v in data["versions"]:
        ch = mc_channel_from_type(v["type"])
        out.append({
            "mc_version": v["id"],
            "mc_channel": ch,
            "java": java_for_mc(v["id"]),
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


def provider_spigot():
    return _provider_buildtools()


def provider_bukkit():
    return _provider_buildtools()


def _provider_buildtools():
    out = []
    for mc in _spigot_bukkit_versions():
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
            builds = http_json(f"https://fill.papermc.io/v3/projects/paper/versions/{mc}/builds")
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


def provider_neoforge():
    data = http_json("https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge")
    out = {}
    for v in data["versions"]:
        m = re.match(r"^(\d+)\.(\d+)\.", v)
        if not m:
            continue
        major, minor = m.group(1), m.group(2)
        mc = f"1.{major}" if minor == "0" else f"1.{major}.{minor}"
        ch = loader_channel_from_string(v)
        entry = out.setdefault(mc, {"mc_version": mc, "mc_channel": "latest", "java": java_for_mc(mc), "loaders": []})
        entry["loaders"].append({
            "id": v, "channel": ch,
            "build_args": {"INSTALLER_URL": f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{v}/neoforge-{v}-installer.jar"},
        })
    return list(out.values())


def _provider_forge_like(metadata_url, installer_url_tpl):
    xml = http_text(metadata_url)
    versions = re.findall(r"<version>([^<]+)</version>", xml)
    out = {}
    for v in versions:
        if "-" not in v:
            continue
        mc, loader = v.split("-", 1)
        ch = loader_channel_from_string(loader)
        entry = out.setdefault(mc, {"mc_version": mc, "mc_channel": "latest", "java": java_for_mc(mc), "loaders": []})
        entry["loaders"].append({
            "id": loader, "channel": ch,
            "build_args": {"INSTALLER_URL": installer_url_tpl.format(full=v)},
        })
    return list(out.values())


def provider_fabric():
    return _provider_fabric_like(
        "https://meta.fabricmc.net/v2/versions/game",
        "https://meta.fabricmc.net/v2/versions/loader",
        "https://meta.fabricmc.net/v2/versions/installer",
        "https://meta.fabricmc.net/v2/versions/loader/{game}/{loader}/{installer}/server/jar",
    )


def provider_quilt():
    return _provider_fabric_like(
        "https://meta.quiltmc.org/v3/versions/game",
        "https://meta.quiltmc.org/v3/versions/loader",
        "https://meta.quiltmc.org/v3/versions/installer",
        "https://meta.quiltmc.org/v3/versions/loader/{game}/{loader}/{installer}/server/jar",
    )


def _provider_fabric_like(game_url, loader_url, installer_url, jar_url_tpl):
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
                "build_args": {"JAR_URL": jar_url_tpl.format(game=mc, loader=l["version"], installer=stable_installer)},
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
    """entries: sortie d'un provider. Retourne une liste de jobs matrix."""
    # index par mc_version pour calculer les tags de profondeur "-snapshot"/"-experimental"
    by_channel = {"latest": [], "snapshot": [], "experimental": []}
    for e in entries:
        by_channel[e["mc_channel"]].append(e)
    for v in by_channel.values():
        v.sort(key=lambda e: e["mc_version"], reverse=True)

    # dernière version release connue par profondeur, pour rattacher les
    # tags -snapshot/-experimental d'une profondeur donnée à la même branche
    jobs = {}

    def add_job(mc_version, loader_id, java, tags, build_args):
        key = (mc_version, loader_id)
        j = jobs.setdefault(key, {
            "loader": loader_name, "mc_version": mc_version, "loader_version": loader_id,
            "java": java, "build_args": build_args, "tags": set(),
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

        add_job(mc, default_loader["id"], e["java"], tags, default_loader["build_args"])

        # --- mots-clés de canal côté loader: "<mc>_latest" (alias du tag nu)
        # et "<mc>_experimental" quand un build expérimental du loader existe
        # réellement pour cette version de Minecraft.
        add_job(mc, default_loader["id"], e["java"], {f"{mc}{SEP}latest"}, default_loader["build_args"])
        exp_keyword_loader = pick_loader_strict(loaders, "experimental")
        if exp_keyword_loader:
            add_job(mc, exp_keyword_loader["id"], e["java"], {f"{mc}{SEP}experimental"}, exp_keyword_loader["build_args"])

        # --- variantes explicites de version de loader: mc_loader
        if mode == "backfill":
            for l in loaders:
                if l is default_loader:
                    continue
                add_job(mc, l["id"], e["java"], {f"{mc}{SEP}{l['id']}"}, l["build_args"])
        # en mode daily on limite aux loaders "latest"/"experimental" les plus récents
        elif mode == "daily":
            exp_loader = pick_default_loader(loaders, "experimental")
            if exp_loader and exp_loader is not default_loader:
                add_job(mc, exp_loader["id"], e["java"], {f"{mc}{SEP}{exp_loader['id']}"}, exp_loader["build_args"])

    # --- tags globaux mouvants: latest / snapshot / experimental
    if global_latest_mc:
        e = global_latest_mc
        dl = pick_default_loader(e["loaders"], "latest")
        if dl:
            add_job(e["mc_version"], dl["id"], e["java"], {"latest", f"latest{SEP}latest"}, dl["build_args"])
        exp = pick_loader_strict(e["loaders"], "experimental")
        if exp:
            add_job(e["mc_version"], exp["id"], e["java"], {f"latest{SEP}experimental"}, exp["build_args"])
    if global_snapshot_mc:
        e = global_snapshot_mc
        dl = pick_default_loader(e["loaders"], "latest")
        if dl:
            add_job(e["mc_version"], dl["id"], e["java"], {"snapshot", f"snapshot{SEP}latest"}, dl["build_args"])
        exp = pick_loader_strict(e["loaders"], "experimental")
        if exp:
            add_job(e["mc_version"], exp["id"], e["java"], {f"snapshot{SEP}experimental"}, exp["build_args"])
    if global_experimental_mc:
        e = global_experimental_mc
        dl = pick_default_loader(e["loaders"], "latest")
        if dl:
            add_job(e["mc_version"], dl["id"], e["java"], {"experimental", f"experimental{SEP}latest"}, dl["build_args"])

    # --- tags de profondeur -snapshot / -experimental: on rattache la
    # dernière version snapshot/experimental connue à chaque profondeur de la
    # dernière release (best-effort, cf. README pour les limites de cette heuristique)
    if global_latest_mc:
        depths = depth_tags(global_latest_mc["mc_version"])
        if global_snapshot_mc:
            dl = pick_default_loader(global_snapshot_mc["loaders"], "latest")
            if dl:
                add_job(global_snapshot_mc["mc_version"], dl["id"], global_snapshot_mc["java"],
                        {f"{d}-snapshot" for d in depths}, dl["build_args"])
        if global_experimental_mc:
            dl = pick_default_loader(global_experimental_mc["loaders"], "latest")
            if dl:
                add_job(global_experimental_mc["mc_version"], dl["id"], global_experimental_mc["java"],
                        {f"{d}-experimental" for d in depths}, dl["build_args"])

    result = list(jobs.values())

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

    for j in result:
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
    jobs.sort(key=lambda j: (j["mc_version"], j["loader_version"]))

    if args.limit is not None:
        jobs = jobs[args.offset:args.offset + args.limit]

    json.dump({"include": jobs}, sys.stdout)


if __name__ == "__main__":
    main()
