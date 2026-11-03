#!/usr/bin/env python3
"""
Version resolver for MinecraftServ-builder.

Queries the official API of each loader and produces a list of build
"jobs" for GitHub Actions (matrix), with the associated Docker tags.

Usage:
    python resolve_versions.py --loader paper --mode daily  > matrix.json
    python resolve_versions.py --loader forge --mode backfill --limit 200 > matrix.json

Modes:
    daily     -> only returns what needs refreshing every day: jobs carrying
                 a moving tag (latest / snapshot / experimental and the depth
                 tags of the active branch) + every tag never published
                 before (compared against --state-file, a plain text file
                 listing the already published tags).
    backfill  -> returns EVERY known version of the loader (used by the
                 manual backfill run that rebuilds the full history, in
                 small batches via --limit/--offset).

Separator between version and loader in tags: "_" (e.g. 1.21.2_40.1.80)
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
    """Encodes a URL path segment (e.g. a Minecraft version 'id'
    interpolated into a template). Some Mojang/loader identifiers contain
    spaces ("1.14 Pre-Release 1") or other characters that are invalid in a
    raw URL/HTTP request (curl rejects them with "Malformed input to a URL
    function")."""
    return urllib.parse.quote(s, safe="")


# ---------------------------------------------------------------------------
# Generic classification
# ---------------------------------------------------------------------------

def mc_channel_from_type(t):
    """Maps the Mojang type to one of the 3 channels exposed as Docker tags."""
    if t == "release":
        return "latest"
    if t == "snapshot":
        return "snapshot"
    # old_beta / old_alpha -> historical/experimental MC versions
    return "experimental"


def loader_channel_from_string(v):
    v = v.lower()
    if any(k in v for k in ("beta", "rc", "pre", "alpha", "snapshot", "unstable", "craftmine")):
        return "experimental"
    return "latest"


def sanitize_tag(tag):
    """A Docker tag only allows [A-Za-z0-9_.-] and must start with an
    alphanumeric character or an underscore. Some version identifiers (e.g.
    Mojang "1.14 Pre-Release 1", "3D Shareware v1.34") contain spaces or
    other invalid characters: they are replaced rather than letting
    `docker buildx build -t ...` fail on a malformed tag."""
    t = re.sub(r"[^A-Za-z0-9_.-]", "-", tag)
    if not re.match(r"^[A-Za-z0-9_]", t):
        t = "v" + t
    return t


def _mc_version_tuple(mc_version):
    """Parses the dotted numeric prefix of an MC version ("1.5.2" -> (1,5,2)).
    Returns None if it cannot be parsed (snapshots/non-numeric aliases)."""
    parts = []
    for p in mc_version.split("."):
        if not p.isdigit():
            return None
        parts.append(int(p))
    return tuple(parts) if parts else None


def depth_tags(mc_version):
    """1.21.2 -> ['1', '1.21', '1.21.2'] ; 26.3 -> ['26', '26.3']
    Skipped if a part is not purely numeric (pre/rc/snapshots)."""
    parts = mc_version.split(".")
    if not all(p.isdigit() for p in parts):
        return []
    out = []
    for i in range(1, len(parts) + 1):
        out.append(".".join(parts[:i]))
    return out


def java_for_mc(mc_version):
    """Heuristic for the Java version required by an MC version (modern releases)."""
    parts = re.findall(r"\d+", mc_version)
    nums = [int(p) for p in parts[:3]] if parts else []
    if not nums:
        return "21"
    major = nums[0]
    minor = nums[1] if len(nums) > 1 else 0
    # new calendar scheme (>= 20.x, not "1.x") -> Java 21
    if major >= 20 and major != 1:
        return "21"
    if major == 1:
        if minor >= 21:
            return "21"
        # 1.20.5 and 1.20.6 require Java 21 (class file version 65):
        # with Java 17 the server crashes on startup.
        patch = nums[2] if len(nums) > 2 else 0
        if minor == 20 and patch >= 5:
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
    """Approximate sort key based on the numbers found in the version
    string (e.g. '1.21.2' -> (1, 21, 2, 0, 0, 0)). Used as a fallback when
    no real release date is available."""
    nums = [int(x) for x in re.findall(r"\d+", v)]
    nums = (nums + [0] * 6)[:6]
    return tuple(nums)


def entry_sort_key(e):
    """Chronological sort key of an entry (mc_version). Uses the real
    release date when known (vanilla, via Mojang), otherwise the natural
    order of the version numbers."""
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
# Providers: each one returns a list of
# {mc_version, mc_channel, java, loaders: [{id, channel, build_args}]}
# ---------------------------------------------------------------------------

# Before 1.2.5 (2012-03-29), the Mojang manifest publishes no dedicated
# server jar ("downloads.server" field missing): every old_alpha, every
# old_beta, and the 1.0 to 1.2.4 releases only have a client. Checked
# exhaustively on the 35 old_alpha versions + the 1.0-1.2.4 releases: the
# field is always missing before, always present from 1.2.5 on. These
# versions are therefore excluded rather than failing the build (the
# Dockerfile would fail a `curl` on a "null" URL).
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


# "1.8" and "1.8.3" depend (through spigot-api) on
# net.md-5:bungeecord-chat:1.8-SNAPSHOT. That snapshot was never promoted to
# a release and has since been purged from every known Sonatype repository
# and mirror (oss.sonatype.org, hub.spigotmc.org, repo.phoenix616.dev... all
# 404): Maven resolution therefore fails for good. "1.8.4" to "1.8.8" share
# the same BuildData (build "582b", checked via
# hub.spigotmc.org/versions/<v>.json) and compile fine (tested: 1.8.4 and
# 1.8.8); only "1.8" (legacy build) and "1.8.3" (build "422") have a
# different, broken pin. CraftBukkit (bukkit), which does not depend on
# bungeecord-chat, is not affected.
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


# "20.4.0-beta" ships an installer whose network connectivity check
# (net.minecraftforge.installer.SimpleInstaller.getIps) queries, among
# others, "authserver.mojang.com"; that name has a CNAME pointing to a
# CloudFront distribution that has since been deleted (NXDOMAIN confirmed),
# so the check always fails and the installer crashes with a
# NullPointerException before the installation even starts. Every other
# version tested around it (20.2.3-beta, 20.3.1-beta, 20.5.0-beta,
# 20.6.1-beta, 20.4.167, 21.0.0-beta) builds fine: it is an isolated
# artifact, permanently broken upstream, not a bug on our side.
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


# Before MC 1.5.2, Forge did not publish an "-installer.jar" but
# "-server.zip"/"-client.zip" files (legacy format, binary patched
# differently). Those versions cannot be built by our current Dockerfile
# (installer based) and are therefore explicitly excluded rather than
# failing the build. Checked: 1.5.2-7.8.0.684 is the first build with an
# installer.jar (200), everything strictly before 1.5.2 returns 404.
#
# MC 1.5.2 itself is excluded as well: on first launch its FML
# ("relauncher") downloads libraries (argo, guava, scala-library,
# deobfuscation data...) from http://files.minecraftforge.net/fmllibs/, a
# host that is permanently dead (404 confirmed): the server can never start,
# even if the Docker build succeeds. From 1.6.x on, those libraries are
# bundled directly (tested/validated locally on 1.6.1/1.6.2/1.6.4).
MIN_FORGE_INSTALLER_MC = (1, 6, 0)


# Before 1.13, Forge uses the old "FML/launchwrapper", which relies on an
# explicit cast to java.net.URLClassLoader (system classloader). That was
# removed in Java 9+ (replaced by an internal, non-castable classloader),
# which crashes the server on startup with a ClassCastException, even if the
# Docker build succeeds (checked locally on 1.12.2 with Java 11: immediate
# crash "AppClassLoader cannot be cast to URLClassLoader"). Java 8 is
# therefore forced for all those versions, independently of the general
# `java_for_mc` heuristic (which applies to Vanilla/Bukkit/Spigot, not
# affected by this issue specific to the old Forge launcher).
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
    """Fabric exposes an official endpoint that directly serves the merged
    server jar (loader + intermediary mappings), verified to work."""
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
    """Unlike Fabric, Quilt does NOT expose a ready-to-use "server/jar"
    endpoint: the quilt-installer has to run at build time, and it downloads
    the vanilla server itself and merges the loader (see
    docker/quilt/Dockerfile). We therefore only provide the installer URL;
    MC_VERSION/LOADER_VERSION are already passed separately.
    The loader entries of this API have no usable "stable" field (unlike
    Fabric): the channel is derived from the version name."""
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


# ---------------------------------------------------------------------------
# Velocity (PaperMC proxy): versioned independently from Minecraft
# ---------------------------------------------------------------------------

def _velocity_order(v):
    """Velocity version order: "3.4.0-SNAPSHOT" < "3.4.0" < "3.4.1-SNAPSHOT".
    Returns (numeric tuple, 0 if -SNAPSHOT else 1), or None if unparsable."""
    base = v[: -len("-SNAPSHOT")] if v.endswith("-SNAPSHOT") else v
    tup = _mc_version_tuple(base)
    if tup is None:
        return None
    return (tup, 0 if v.endswith("-SNAPSHOT") else 1)


def provider_velocity():
    """Same Fill v3 API as Paper. Velocity is compatible with every
    Minecraft client version it supports: it has NO MC version. The
    "mc_version" field of the entries therefore holds the Velocity version
    (e.g. "3.4.0-SNAPSHOT") and the "loaders" are its builds."""
    data = http_json("https://fill.papermc.io/v3/projects/velocity")
    out = []
    for family, versions in data["versions"].items():
        for v in versions:
            if _velocity_order(v) is None:
                continue
            builds = http_json(f"https://fill.papermc.io/v3/projects/velocity/versions/{url_segment(v)}/builds")
            loaders = []
            for b in sorted(builds, key=lambda b: int(b["id"]), reverse=True):
                dl = b.get("downloads", {}).get("server:default")
                if not dl:
                    continue
                lch = "latest" if b.get("channel", "STABLE").upper() in ("STABLE", "RECOMMENDED") else "experimental"
                loaders.append({"id": str(b["id"]), "channel": lch, "build_args": {"JAR_URL": dl["url"]}})
            if loaders:
                # Java 21 for every version: required by recent builds, and
                # backward compatible with older ones.
                out.append({"mc_version": v, "mc_channel": "snapshot" if v.endswith("-SNAPSHOT") else "latest",
                            "java": "21", "loaders": loaders})
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
    "velocity": provider_velocity,
}


# ---------------------------------------------------------------------------
# Tags + build jobs
# ---------------------------------------------------------------------------

def pick_default_loader(loaders, channel):
    """'Default' loader of a given channel = the most recent one of that
    channel, otherwise the most recent one overall (fallback)."""
    cand = [l for l in loaders if l["channel"] == channel]
    pool = cand or loaders
    return pool[0] if pool else None


def pick_loader_strict(loaders, channel):
    """Like pick_default_loader but without fallback: None if the requested
    channel does not actually exist for this loader (e.g. no 'experimental'
    build published for a given Minecraft version)."""
    cand = [l for l in loaders if l["channel"] == channel]
    return cand[0] if cand else None


def exact_tag_base(version, depth_owner_of):
    """Tag used for an exact version. A version whose name is also a partial
    depth owned by a higher version (MC "1.20" while 1.20.6 exists) would
    otherwise share the bare "1.20" tag with that depth: rebuilding the old
    version (e.g. for a new loader build) would then move "1.20" back to it.
    Such versions use "<v>.0" instead ("1.20.0", "1.20.0_latest"...), and the
    bare "1.20" stays the depth tag that follows the latest 1.20.x."""
    owner = depth_owner_of(version)
    if owner is not None and owner != version:
        return f"{version}.0"
    return version


# Marker tag published once the explicit "<v>_<loader>" tags exist. Its
# presence on Docker Hub means the migration below is done and must never
# run again: otherwise a new loader build would be mistaken for a missing
# migration. While retags are pending it is carried ONLY by the last retag
# job (and the build action drops it if any retag failed), so an interrupted
# or partially failed migration is resumed on the next daily run. When there
# is nothing to retag, the "latest" job carries it.
MIGRATION_MARKER = "tag-scheme-v2"


def apply_migration(result, known_tags, explicit_tags, live_depths):
    """One-time migration of the explicit "<v>_<loader>" tags.

    Images built before these tags existed only carry "<v>", "<v>_latest"...
    Without a migration, every one of them would look new and the first
    daily run would rebuild the whole history. While MIGRATION_MARKER is not
    published yet (= migration not done), a job whose
    only missing tags are explicit ones, and whose exact tag already exists,
    is turned into a retag job: the build step then adds the missing tags to
    the existing image (docker buildx imagetools create) instead of
    compiling. Versions that are really missing are still built. Retag jobs
    come first, and only the last one carries MIGRATION_MARKER (with
    "marker_tag" set, so the build action can drop it if a retag failed)."""
    if MIGRATION_MARKER in known_tags or not explicit_tags:
        return result
    retags, others = [], []
    for j in result:
        missing = {t for t in j["tags"] if t not in known_tags}
        key = (j["mc_version"], j["loader_version"])
        explicit = explicit_tags.get(key)
        src = j.get("_exact_tag")
        if (explicit and missing == {explicit} and src in known_tags
                and not is_moving_job(j, live_depths)):
            retags.append(dict(j, tags={explicit}, retag_from=src))
        else:
            others.append(j)
    if retags:
        for j in others:
            j["tags"].discard(MIGRATION_MARKER)
        retags[-1]["tags"].add(MIGRATION_MARKER)
        retags[-1]["marker_tag"] = MIGRATION_MARKER
    return retags + others


MOVING_GLOBAL = ("latest", "snapshot", "experimental")
MOVING_SUFFIXES = ("-latest", "-snapshot", "-experimental")


def is_moving_job(j, live_depths):
    """True if the job carries a moving tag, i.e. a tag that must be
    republished every day to follow the latest version: global tags
    (latest, snapshot, experimental, latest_*...) and partial depth tags of
    the ACTIVE branch (live_depths = depths of the latest release, e.g. "1",
    "1.21": "1-latest", "1.21", "1.21-snapshot"...).
    Depths of finished branches ("1.4", "1.12"...) no longer move: they are
    only republished if one of their tags is missing (or in backfill).
    "<mc>-latest" (full depth, e.g. "1.4.6-latest") is NOT moving: it always
    designates the same Minecraft version. New loader versions for an MC
    version are detected through the explicit "<mc>_<loader>" tag (missing
    from known_tags until it is published)."""
    for t in j["tags"]:
        if t in MOVING_GLOBAL or t.startswith(tuple(f"{g}{SEP}" for g in MOVING_GLOBAL)):
            return True
        if t in live_depths and t != j["mc_version"]:
            return True
        for s in MOVING_SUFFIXES:
            base = t[: -len(s)]
            if t.endswith(s) and base != j["mc_version"] and base in live_depths:
                return True
    return False


def build_jobs(loader_name, entries, mode, known_tags):
    """entries: output of a provider. Returns a list of matrix jobs, sorted
    in chronological order of appearance (oldest -> newest); in daily mode,
    jobs carrying a moving tag come first."""
    # index by channel, to compute the "-snapshot"/"-experimental" depth tags
    by_channel = {"latest": [], "snapshot": [], "experimental": []}
    for e in entries:
        by_channel[e["mc_channel"]].append(e)
    for v in by_channel.values():
        v.sort(key=entry_sort_key, reverse=True)

    jobs = {}

    def add_job(mc_version, loader_id, java, tags, build_args, sort_key):
        key = (mc_version, loader_id)
        j = jobs.setdefault(key, {
            "loader": loader_name, "mc_version": mc_version, "loader_version": loader_id,
            "java": java, "build_args": build_args, "tags": set(), "_sort_key": sort_key,
        })
        j["tags"].update(tags)

    # owner of each depth tag ("1", "1.20", "1.20.6"): the highest release
    # of that depth. Without this, EVERY release received
    # "1"/"1-latest"/"1.x"/"1.x-latest": (a) the daily filter kept every
    # release (because of the "-latest" tags) and rebuilt the whole history
    # every day, (b) an interrupted run left ":1" pointing to an old version
    # (the last version pushed before the failure).
    depth_owner = {}
    for e in by_channel["latest"]:
        tup = _mc_version_tuple(e["mc_version"])
        if tup is None:
            continue
        for d in depth_tags(e["mc_version"]):
            cur = depth_owner.get(d)
            if cur is None or tup > cur[0]:
                depth_owner[d] = (tup, e["mc_version"])

    global_latest_mc = by_channel["latest"][0] if by_channel["latest"] else None
    live_depths = set(depth_tags(global_latest_mc["mc_version"])) if global_latest_mc else set()
    explicit_tags = {}  # (mc, default loader) -> "<base>_<loader>", for the migration
    global_snapshot_mc = by_channel["snapshot"][0] if by_channel["snapshot"] else None
    global_experimental_mc = by_channel["experimental"][0] if by_channel["experimental"] else None

    for e in entries:
        mc = e["mc_version"]
        loaders = e["loaders"]
        default_loader = pick_default_loader(loaders, "latest")
        if not default_loader:
            continue

        # --- exact tag without a loader version = latest loader for this mc version
        base = exact_tag_base(mc, lambda v: depth_owner.get(v, (None, None))[1])
        tags = {base}
        # --- depths (only for purely numeric mc versions, release channel)
        depths = depth_tags(mc) if e["mc_channel"] == "latest" else []
        # the exact tag (full depth) always stays on its own version;
        # partial depths ("1", "1.20") and every "-latest" only go to the
        # highest release of the depth.
        depths = [d for d in depths if depth_owner.get(d, (None, None))[1] == mc]
        for d in depths:
            tags.add(d)
            tags.add(f"{d}-latest")

        if base != mc:
            tags.add(f"{base}-latest")

        add_job(mc, default_loader["id"], e["java"], tags, default_loader["build_args"], job_sort_key(e, default_loader["id"]))
        jobs[(mc, default_loader["id"])]["_exact_tag"] = base

        # --- loader-side channel keywords: "<mc>_latest" (alias of the bare
        # tag) and "<mc>_experimental" when an experimental loader build
        # actually exists for this Minecraft version.
        add_job(mc, default_loader["id"], e["java"], {f"{base}{SEP}latest"}, default_loader["build_args"], job_sort_key(e, default_loader["id"]))
        # explicit "<mc>_<loader>" tag on the default loader (except vanilla,
        # where loader == MC version): this is what triggers a daily rebuild
        # when a new loader build comes out for an existing MC version.
        if loader_name != "vanilla" and default_loader["id"] != mc:
            explicit_tags[(mc, default_loader["id"])] = sanitize_tag(f"{base}{SEP}{default_loader['id']}")
            add_job(mc, default_loader["id"], e["java"], {f"{base}{SEP}{default_loader['id']}"}, default_loader["build_args"], job_sort_key(e, default_loader["id"]))
        exp_keyword_loader = pick_loader_strict(loaders, "experimental")
        if exp_keyword_loader:
            add_job(mc, exp_keyword_loader["id"], e["java"], {f"{base}{SEP}experimental"}, exp_keyword_loader["build_args"], job_sort_key(e, exp_keyword_loader["id"]))

        # --- explicit loader version variants: mc_loader
        if mode == "backfill":
            for l in loaders:
                if l is default_loader:
                    continue
                add_job(mc, l["id"], e["java"], {f"{base}{SEP}{l['id']}"}, l["build_args"], job_sort_key(e, l["id"]))
        # in daily mode, limited to the most recent "latest"/"experimental" loaders
        elif mode == "daily":
            exp_loader = pick_default_loader(loaders, "experimental")
            if exp_loader and exp_loader is not default_loader:
                add_job(mc, exp_loader["id"], e["java"], {f"{base}{SEP}{exp_loader['id']}"}, exp_loader["build_args"], job_sort_key(e, exp_loader["id"]))

    # --- moving global tags: latest / snapshot / experimental
    if global_latest_mc:
        e = global_latest_mc
        dl = pick_default_loader(e["loaders"], "latest")
        if dl:
            add_job(e["mc_version"], dl["id"], e["java"], {"latest", f"latest{SEP}latest", MIGRATION_MARKER}, dl["build_args"], job_sort_key(e, dl["id"]))
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

    # --- -snapshot / -experimental depth tags: the latest known
    # snapshot/experimental version is attached to every depth of the
    # latest release (best effort, see the README for the limits of this heuristic)
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
        if "_exact_tag" in j:
            j["_exact_tag"] = sanitize_tag(j["_exact_tag"])

    if mode == "daily":
        # only keep jobs that touch at least one never-published tag, or a
        # moving tag (always republished to stay up to date)
        filtered = []
        for j in result:
            if is_moving_job(j, live_depths) or any(t not in known_tags for t in j["tags"]):
                filtered.append(j)
        result = filtered

    # chronological order of appearance (oldest -> newest)
    result.sort(key=lambda j: j["_sort_key"])
    if mode == "daily":
        # in daily mode, jobs carrying a moving tag (latest, depths,
        # snapshot...) come first: a failure further down the list must not
        # prevent refreshing what users actually pull.
        result.sort(key=lambda j: 0 if is_moving_job(j, live_depths) else 1)
        result = apply_migration(result, known_tags, explicit_tags, live_depths)
    for j in result:
        j.pop("_sort_key", None)
        j.pop("_exact_tag", None)
        j["tags"] = sorted(j["tags"])
    return result


def build_jobs_velocity(entries, mode, known_tags):
    """Velocity tags (no Minecraft version in the tags):
      latest / latest_latest      -> latest stable build of the highest version
      latest_experimental         -> latest non-stable build of that version (if any)
      snapshot / snapshot_latest  -> latest "-SNAPSHOT" dev line (often = latest)
      experimental                -> alias of latest_experimental
      <v> / <v>_latest            -> latest stable build of version <v> (e.g. 3.4.0-SNAPSHOT)
      <v>_experimental            -> latest non-stable build of <v>
      <v>_<build>                 -> exact build (e.g. 3.4.0-SNAPSHOT_523)
      <d> / <d>-latest            -> depths "3", "3.4", "3.4.0": highest version of
                                     that level, a final release ranking above its
                                     -SNAPSHOT (3.4.0 > 3.4.0-SNAPSHOT)."""
    jobs = {}

    def add_job(v, l, tags):
        j = jobs.setdefault((v, l["id"]), {
            "loader": "velocity", "mc_version": v, "loader_version": l["id"], "java": "21",
            "build_args": l["build_args"], "tags": set(), "_sort_key": (_velocity_order(v), int(l["id"])),
        })
        j["tags"].update(tags)

    entries = sorted(entries, key=lambda e: _velocity_order(e["mc_version"]), reverse=True)
    if not entries:
        return []

    depth_owner = {}
    for e in entries:  # from highest to lowest: the first one seen wins
        base = e["mc_version"].removesuffix("-SNAPSHOT")
        for d in depth_tags(base):
            depth_owner.setdefault(d, e["mc_version"])

    top = entries[0]["mc_version"]
    live_depths = set(depth_tags(top.removesuffix("-SNAPSHOT")))
    top_snapshot = next((e for e in entries if e["mc_version"].endswith("-SNAPSHOT")), None)

    for e in entries:
        v = e["mc_version"]
        dl = pick_default_loader(e["loaders"], "latest")
        exp = pick_loader_strict(e["loaders"], "experimental")
        b = exact_tag_base(v, depth_owner.get)
        tags = {b, f"{b}{SEP}latest", f"{b}{SEP}{dl['id']}"}
        for d, owner in depth_owner.items():
            if owner == v:
                tags.update({d, f"{d}-latest"})
        if v == top:
            tags.update({"latest", f"latest{SEP}latest"})
        if top_snapshot and v == top_snapshot["mc_version"]:
            tags.update({"snapshot", f"snapshot{SEP}latest"})
        add_job(v, dl, tags)
        if exp:
            etags = {f"{b}{SEP}experimental", f"{b}{SEP}{exp['id']}"}
            if v == top:
                etags.update({"experimental", f"latest{SEP}experimental"})
            add_job(v, exp, etags)
        if mode == "backfill":
            for l in e["loaders"]:
                add_job(v, l, {f"{b}{SEP}{l['id']}"})

    result = list(jobs.values())
    for j in result:
        j["tags"] = {sanitize_tag(t) for t in j["tags"]}
    if mode == "daily":
        result = [j for j in result if is_moving_job(j, live_depths) or any(t not in known_tags for t in j["tags"])]
    result.sort(key=lambda j: j["_sort_key"])
    if mode == "daily":
        result.sort(key=lambda j: 0 if is_moving_job(j, live_depths) else 1)
    for j in result:
        j.pop("_sort_key", None)
        j["tags"] = sorted(j["tags"])
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--loader", required=True, choices=PROVIDERS.keys())
    ap.add_argument("--mode", default="daily", choices=["daily", "backfill"])
    ap.add_argument("--state-file", default=None, help="text file listing the already published tags (one per line)")
    ap.add_argument("--limit", type=int, default=None, help="limits the number of returned jobs (backfill pagination)")
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
    if args.loader == "velocity":
        jobs = build_jobs_velocity(entries, args.mode, known_tags)
    else:
        jobs = build_jobs(args.loader, entries, args.mode, known_tags)

    if args.limit is not None:
        jobs = jobs[args.offset:args.offset + args.limit]

    json.dump({"include": jobs}, sys.stdout)


if __name__ == "__main__":
    main()
