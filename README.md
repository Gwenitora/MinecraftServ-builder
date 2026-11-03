# MinecraftServ-builder

Ready-to-use Docker images to host a Minecraft server with any loader:
**vanilla, bukkit, spigot, paper, forge, neoforge, fabric, quilt**, plus the
**velocity** proxy. Every version officially published by each project is
available (releases, snapshots and pre-releases), for `linux/amd64` and
`linux/arm64`, and the images are refreshed automatically every day.

> ✅ **The Mojang EULA is accepted automatically** (`ACCEPT_EULA=true` by
> default). By using these images you accept the official EULA:
> <https://aka.ms/MinecraftEULA>. Set `ACCEPT_EULA=false` to refuse it (the
> server will then not start).

## Images

| Loader | Type | Docker Hub | Documentation | Official site |
|--------|------|------------|---------------|---------------|
| Vanilla | Official Mojang server | [minecraftserv/vanilla](https://hub.docker.com/r/minecraftserv/vanilla) | [README](docker/vanilla/README.md) | <https://www.minecraft.net/download/server> |
| Bukkit | CraftBukkit (plugins) | [minecraftserv/bukkit](https://hub.docker.com/r/minecraftserv/bukkit) | [README](docker/bukkit/README.md) | <https://www.spigotmc.org/wiki/buildtools/> |
| Spigot | Plugins, optimized Bukkit | [minecraftserv/spigot](https://hub.docker.com/r/minecraftserv/spigot) | [README](docker/spigot/README.md) | <https://www.spigotmc.org/wiki/buildtools/> |
| Paper | Plugins, high performance | [minecraftserv/paper](https://hub.docker.com/r/minecraftserv/paper) | [README](docker/paper/README.md) | <https://papermc.io/software/paper> |
| Forge | Mods | [minecraftserv/forge](https://hub.docker.com/r/minecraftserv/forge) | [README](docker/forge/README.md) | <https://files.minecraftforge.net> |
| NeoForge | Mods | [minecraftserv/neoforge](https://hub.docker.com/r/minecraftserv/neoforge) | [README](docker/neoforge/README.md) | <https://neoforged.net> |
| Fabric | Mods (lightweight) | [minecraftserv/fabric](https://hub.docker.com/r/minecraftserv/fabric) | [README](docker/fabric/README.md) | <https://fabricmc.net/use/server/> |
| Quilt | Mods (Fabric fork) | [minecraftserv/quilt](https://hub.docker.com/r/minecraftserv/quilt) | [README](docker/quilt/README.md) | <https://quiltmc.org/en/install/server/> |
| Velocity | Proxy (network of servers) | [minecraftserv/velocity](https://hub.docker.com/r/minecraftserv/velocity) | [README](docker/velocity/README.md) | <https://papermc.io/software/velocity> |

## Quick start

```bash
docker run -d --name my-server \
  -p 25565:25565 \
  -v mc_data:/app \
  -e MAX_MEMORY=4G \
  minecraftserv/paper:latest
```

With Docker Compose:

```yaml
services:
  minecraft:
    image: minecraftserv/paper:1.21
    ports:
      - "25565:25565"
    environment:
      MAX_MEMORY: 4G
    volumes:
      - mc_data:/app
    restart: unless-stopped
volumes:
  mc_data:
```

All server data (world, configuration, logs, plugins, mods) lives in `/app`.
On first start the image copies the server files into `/app`. When the image
is updated to another version, the server files are refreshed and your own
files (world, configuration, plugins, mods) are kept.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCEPT_EULA` | `true` | Writes `eula=true`/`false` to `/app/eula.txt` on startup |
| `MIN_MEMORY` | `1G` (`512M` for velocity) | JVM `-Xms` |
| `MAX_MEMORY` | `2G` (`1G` for velocity) | JVM `-Xmx` |
| `EXTRA_JAVA_OPTS` | (empty) | Additional JVM options (e.g. `-XX:+UseG1GC`) |

## Tags

The separator between the Minecraft version and the loader version is **`_`**
(Docker does not allow `:` inside a tag). Examples below use
`minecraftserv/fabric`, with 1.21.1 as the latest release.

### Moving tags (follow new releases)

| Tag | Points to |
|-----|-----------|
| `latest` (= `latest_latest`) | latest release + latest stable loader build |
| `latest_experimental` | latest release + latest experimental loader build (beta/rc), if any |
| `snapshot` (= `snapshot_latest`) | most recent snapshot / pre-release / release candidate |
| `snapshot_experimental` | same, with the latest experimental loader build |
| `experimental` (= `experimental_latest`) | latest historical alpha/beta version of the game, when the loader offers one |

### One version

| Tag | Points to |
|-----|-----------|
| `1.21.1` (= `1.21.1_latest`, `1.21.1-latest`) | Minecraft 1.21.1 + latest stable loader build |
| `1.21.1_0.16.5` | Minecraft 1.21.1 + exactly this loader build |
| `1.21.1_experimental` | Minecraft 1.21.1 + latest experimental loader build, if any |
| `24w10a`, `1.21-pre1`, `1.21-rc1`... | that exact snapshot / pre-release (with the same `_<loader>` variants) |

### Branch tags (follow the newest version of a branch)

| Tag | Points to |
|-----|-----------|
| `1` (= `1-latest`) | highest 1.x.y release |
| `1.20` (= `1.20-latest`) | highest 1.20.y release (e.g. 1.20.6) |
| `1.20-snapshot` | newest snapshot / pre-release leading to a 1.20.y version |
| `1.20.0` | the exact release named "1.20" (see below) |

Rules:

- A branch tag only goes to the highest release of its branch. If 1.20.7 comes
  out, `1.20` moves to it; if 1.21 comes out, `1.20` does not change.
- When a release has the same name as a branch that has newer versions
  (Minecraft "1.20" while 1.20.6 exists), its exact tags use `.0`: `1.20.0`,
  `1.20.0_latest`, `1.20.0_<loader>`. The bare `1.20` stays the branch tag.
- `<branch>-snapshot` goes to the newest snapshot **of that branch**:
  - pre-releases and release candidates are matched by name (`1.18-pre8` ->
    1.18, `26.1-snapshot-2` -> 26.1);
  - weekly snapshots (`24w10a`) belong to the release that followed them;
  - ordering inside a version: snapshot < pre-release < release candidate;
  - a branch without any snapshot has no `<branch>-snapshot` tag.
- `vanilla`, `bukkit` and `spigot` have no separate loader: the `_<loader>`
  suffix only exists as `_latest`.
- Velocity is not tied to a Minecraft version: see its
  [README](docker/velocity/README.md) for its own tags.

### Channels

| Docker channel | Vanilla (Mojang type) | Paper / Fabric / Quilt (project API) | Forge / NeoForge (build name) |
|----------------|-----------------------|--------------------------------------|-------------------------------|
| `latest` | `release` | stable | no `beta`/`rc`/`pre` |
| `snapshot` | `snapshot` | non-stable game version | (none) |
| `experimental` | `old_beta` / `old_alpha` | non-stable loader build | contains `beta`/`rc`/`pre`/`alpha` |

### Java version

| Minecraft | Java |
|-----------|------|
| before 1.12 | 8 |
| 1.12 to 1.16.5 | 11 |
| 1.17 to 1.20.4 | 17 |
| 1.20.5 and newer (including 26.x) | 21 |
| Forge before 1.13 | 8 (old launcher) |
| Velocity | 21 |

### Why are there untagged images on Docker Hub?

Every tag points to an **image index** that lists one image per architecture
(`linux/amd64`, `linux/arm64`) plus small build attestations. Docker Hub shows
those entries as untagged lines under the tagged one: they are not duplicates,
`docker pull` picks the right one for your machine.

## Files in `/app`

```
/app
├── eula.txt            # written on every start (ACCEPT_EULA)
├── server.properties   # main server configuration (created on first start)
├── server.jar / run.sh # server launcher (depends on the loader)
├── libraries/          # server dependencies (depends on the loader/version)
├── world/              # the world
├── plugins/            # bukkit / spigot / paper / velocity
├── mods/               # forge / neoforge / fabric / quilt
├── config/             # mod configuration (forge / neoforge / fabric / quilt)
└── logs/
```

Configuration references:

- `server.properties`: <https://minecraft.wiki/w/Server.properties>
- Paper: <https://docs.papermc.io/paper/reference/configuration>
- Spigot (`spigot.yml`): <https://www.spigotmc.org/wiki/spigot-configuration/>
- Bukkit (`bukkit.yml`): <https://bukkit.fandom.com/wiki/Bukkit.yml>
- Velocity (`velocity.toml`): <https://docs.papermc.io/velocity/configuration>
- Forge / NeoForge / Fabric / Quilt: each mod documents its own file in `config/`.

## How the images are built

### Schedule

Each loader has its own workflow, started once a day (times in UTC; GitHub
may start scheduled runs a few minutes late):

| Loader | UTC | Paris (winter / summer) |
|--------|-----|-------------------------|
| vanilla | 00:00 | 01:00 / 02:00 |
| velocity | 01:00 | 02:00 / 03:00 |
| bukkit | 03:00 | 04:00 / 05:00 |
| spigot | 06:00 | 07:00 / 08:00 |
| paper | 09:00 | 10:00 / 11:00 |
| forge | 12:00 | 13:00 / 14:00 |
| neoforge | 15:00 | 16:00 / 17:00 |
| fabric | 18:00 | 19:00 / 20:00 |
| quilt | 21:00 | 22:00 / 23:00 |

Builds **never** start on a push or a merge, on any branch: only on this
schedule or manually.

### Daily mode

1. `scripts/resolve_versions.py` reads the official API of the loader and
   lists every Minecraft version and every loader build.
2. It reads the tags already on Docker Hub, and for each tag the image it
   points to (the per-architecture digests given by the Docker Hub API).
3. An image that already exists (found through its `<mc>_<loader>` tag, or
   `<mc>` for vanilla, bukkit and spigot) is **never rebuilt**: the tags that
   are missing or point to another image are re-attached to it with
   `docker buildx imagetools create`, which takes a few seconds. This is how
   moving tags (`latest`, `1.21`, `snapshot`...) follow new versions, and how
   tags left wrong by older versions of the scripts are repaired.
4. Only the images that do not exist yet are built, one at a time, moving
   tags first.
5. Branch snapshot tags that are no longer produced (for example an old
   `26-snapshot` that pointed to 1.18-pre8) are deleted from Docker Hub.

The run *Summary* shows how many images are built, how many tags are fixed
and how many tags are deleted.

### Backfill mode (full history)

Rebuilding the whole history does not fit in one run (GitHub stops a run
after about 6 hours). Use the manual `backfill` mode in batches with `limit`
(number of versions in this run, `0` = no limit) and `offset` (number of
versions to skip):

| Run | limit | offset |
|-----|-------|--------|
| 1 | 100 | 0 |
| 2 | 100 | 100 |
| 3 | 100 | 200 |

Keep going until a run reports 0 version to build. Backfill always rebuilds
the images it lists. Bukkit and Spigot are compiled with BuildTools and are
much slower than the other loaders: use smaller batches for them.

### Failures

- A failed build or tag fix is retried once after 60 seconds.
- If it fails again, the run goes on with the next versions; the job is
  marked as failed at the end and the run *Summary* lists the failed versions.
- Set the `continue_on_error: "false"` input of the `build-loader` action to
  stop at the first failure instead.

To fit in the runner disk (~14 GB free), the build frees about 25 GB of
unused preinstalled SDKs and prunes the buildx cache above 4 GB after every
version. The Java base images (`eclipse-temurin`) come from the ECR Public
mirror of the official images (`public.ecr.aws/docker/library`), so they do
not count against the Docker Hub pull quota.

### One-time tag migration

Images built before the `<mc>_<loader>` tags existed do not have them. Until
the marker tag `tag-scheme-v2` is published, the daily run finds those images
through their exact `<mc>` tag and adds the missing tags to them (no
compilation). The marker is published only once every one of those tag fixes
succeeded; an interrupted migration resumes on the next daily run.

### Concurrency

Each workflow runs at most once at a time per branch
(`concurrency: <loader>-<branch>` with `cancel-in-progress: true`): starting a
new run cancels the one in progress. Avoid starting a manual run while a long
scheduled run is still going.

## Running builds manually

**Actions** tab -> **builds** -> **Run workflow**: tick the loaders (or
**all**), choose `daily` or `backfill`, optionally `limit`/`offset`, and run.
Each selected loader starts as a separate run of its own `<loader>.yml`
workflow. You can also start a single `<loader>.yml` workflow directly.

The **reset** checkbox first deletes **every** tag of `minecraftserv/<loader>`
on Docker Hub. It cannot be undone.

## Docker Hub setup

1. Log in to <https://hub.docker.com> with the `minecraftserv` account.
2. **Account Settings -> Personal access tokens**: create a token with
   **Read, Write, Delete** permissions (*Delete* is needed to remove stale
   tags and by `reset`).
3. In this GitHub repository: **Settings -> Secrets and variables -> Actions**,
   add `DOCKERHUB_USERNAME` (`minecraftserv`) and `DOCKERHUB_TOKEN`.
4. Create the 9 **public** repositories `minecraftserv/<loader>` (otherwise
   anonymous `docker pull` fails).

## Repository layout

```
docker/<loader>/Dockerfile          # one image per loader
docker/<loader>/README.md           # documentation of that image
entrypoint/entrypoint.sh            # shared entrypoint: fills /app, writes the EULA, starts run.sh
scripts/resolve_versions.py         # reads the loader APIs, computes tags, builds and tag fixes
.github/actions/resolve-versions/   # reads Docker Hub and computes the build matrix of a loader
.github/actions/build-loader/       # builds, fixes tags and deletes stale tags, one version at a time
.github/actions/reset-images/       # deletes every Docker Hub tag of a loader (reset)
.github/workflows/<loader>.yml      # daily schedule + manual run, per loader
.github/workflows/builds.yml        # starts several loader workflows at once
```

## Known limitations

- **Vanilla before 1.2.5** is not available: Mojang publishes no dedicated
  server jar for those versions.
- **Forge before 1.6** is not available: no installer before 1.5.2, and
  1.5.2 downloads libraries from a host that no longer exists.
- **Spigot 1.8 and 1.8.3** are not available: they depend on an artifact that
  was removed from every Maven repository (CraftBukkit 1.8/1.8.3 still build).
- **NeoForge 20.4.0-beta** is not available: its installer always crashes on
  a network check against a dead host.
- **Bukkit / Spigot** are compiled from source with BuildTools (no jar may be
  redistributed): their builds are much slower.
- **Quilt** has no ready-made server jar: the official installer runs at
  build time.
- The snapshot-to-branch matching relies on version names and release dates:
  check the exact tag on Docker Hub if a project changes its naming scheme.
