# minecraftserv/horizon

> This image is part of [MinecraftServ](https://github.com/Gwenitora/MinecraftServ-builder),
> a family of ready-to-use Minecraft server images. See the
> [main README](https://github.com/Gwenitora/MinecraftServ-builder#images) for
> the other loaders.

[Horizon](https://playhorizon.dev): Minecraft: Java Edition 26.3 rewritten in
Rust. `horizon-server` is a native program: there is **no Java** in this
image. Every Horizon build that ships the Linux dedicated server (the
Nightly builds of [horizon-rust/horizon](https://github.com/horizon-rust/horizon/releases))
is available, for **`linux/amd64` only**: Horizon publishes no prebuilt server
for other platforms.

## Game files: prepare them first

The image contains **none of Minecraft's files**, and Horizon ships none
either. Before the first start, prepare them once from your own copy of
Minecraft 26.3, on a machine with Java 25 (a JDK), as described in the
[Horizon hosting guide](https://playhorizon.dev/docs/hosting):

```bash
horizon-prepare --prepare --server-jar /path/to/26.3/server.jar
```

`horizon-prepare` comes with the Horizon server download. It writes a `26.3`
folder (under `~/.local/share/horizon/game-files/horizon-client/` with the
default settings). Mount that folder read-only into the container, at the
place Horizon's own Docker image uses:

```
-v /path/to/horizon-client/26.3:/opt/horizon/.local/horizon-client/26.3:ro
```

Without it the server refuses to start and says where it looked.

## Quick start

```bash
docker run -d --name horizon \
  -p 25565:25565 \
  --stop-timeout 180 \
  -v horizon_data:/app \
  -v /path/to/horizon-client/26.3:/opt/horizon/.local/horizon-client/26.3:ro \
  -e HORIZON_WHITELIST=true -e HORIZON_PLAYERS=Alex,Steve -e HORIZON_OP=Alex \
  minecraftserv/horizon:latest
```

With Docker Compose:

```yaml
services:
  horizon:
    image: minecraftserv/horizon:latest
    ports:
      - "25565:25565"
    environment:
      HORIZON_WHITELIST: "true"
      HORIZON_PLAYERS: Alex,Steve
      HORIZON_OP: Alex
    volumes:
      - horizon_data:/app
      - /path/to/horizon-client/26.3:/opt/horizon/.local/horizon-client/26.3:ro
    stop_grace_period: 3m
    restart: unless-stopped
volumes:
  horizon_data:
```

`horizon-server` saves the world and stops cleanly on `SIGTERM`: keep the
long stop timeout (`--stop-timeout 180` / `stop_grace_period: 3m`), or Docker
kills it after 10 seconds.

Manage the running server with the Horizon command line:

```bash
docker exec horizon horizon-server status
docker exec horizon horizon-server cmd say hello
docker exec horizon horizon-server backup
docker exec horizon horizon-server logs -n 50
```

## Configuration

On the first start, the image runs `horizon-server init --yes`, which writes
`/app/server.toml` from these variables. **They are read on the first start
only**: afterwards, edit `/app/server.toml` (or run
`docker exec horizon horizon-server config set SECTION.KEY=VALUE`) and restart.

| Variable | Default | Description |
|----------|---------|-------------|
| `HORIZON_EULA` | value of `ACCEPT_EULA` (`true`) | `true` accepts the Minecraft EULA (<https://aka.ms/MinecraftEULA>); the server does not start until it is `true` |
| `HORIZON_WORLD` | `world` | world folder name |
| `HORIZON_SEED` | (random) | world seed |
| `HORIZON_PORT` | `25565` | server port |
| `HORIZON_WHITELIST` | `true` | whitelist on or off |
| `HORIZON_PLAYERS` | (empty) | names added to the whitelist, separated by commas |
| `HORIZON_OP` | (empty) | a player to make an operator |
| `HORIZON_ONLINE` | `true` | check players' Minecraft accounts (online mode) |

Note that Horizon turns the **whitelist on by default**: set
`HORIZON_PLAYERS`, or `HORIZON_WHITELIST=false`, or nobody can join.

`server.toml` is the file to edit: Horizon rewrites `server.properties` from
it before every start. Reference: <https://playhorizon.dev/docs/api/server-reference>.
`MIN_MEMORY`, `MAX_MEMORY` and `EXTRA_JAVA_OPTS` (Java options of the other
images) do not apply here.

Everything the server writes lives in `/app`: `server.toml`, the world,
`backups/`, `logs/`, `ops.json`, `whitelist.json`... The program itself stays
in the image (`/opt/horizon`), so updating the image never touches your files.

## Tags

Horizon targets one Minecraft version (26.3) and only ships Nightly builds,
named here `<date>-<commit>`:

| Tag | Points to |
|-----|-----------|
| `latest` (= `latest_latest`, `26.3`, `26.3_latest`, `26`) | newest Horizon build |
| `26.3_<date>-<commit>` (e.g. `26.3_2026-11-13-abc1234`) | exactly that Horizon build |

## Limitations

- `linux/amd64` only (no prebuilt Horizon server for ARM).
- Horizon is under heavy development and only publishes Nightly builds: pin an
  exact `26.3_<date>-<commit>` tag if you need a build that does not change.
- If Horizon moves to another Minecraft version, the image tags follow only
  once `HORIZON_MC_VERSION` is updated in `scripts/resolve_versions.py`.
