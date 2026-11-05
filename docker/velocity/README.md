# minecraftserv/velocity

> This image is part of [MinecraftServ](https://github.com/Gwenitora/MinecraftServ-builder),
> a family of ready-to-use Minecraft server images. Other loaders are available:
>
> | Loader | Type | Docker Hub | Documentation |
> |--------|------|------------|---------------|
> | Vanilla | Official Mojang server | [minecraftserv/vanilla](https://hub.docker.com/r/minecraftserv/vanilla) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/vanilla/README.md) |
> | Bukkit | CraftBukkit (plugins) | [minecraftserv/bukkit](https://hub.docker.com/r/minecraftserv/bukkit) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/bukkit/README.md) |
> | Spigot | Plugins, optimized Bukkit | [minecraftserv/spigot](https://hub.docker.com/r/minecraftserv/spigot) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/spigot/README.md) |
> | Paper | Plugins, high performance | [minecraftserv/paper](https://hub.docker.com/r/minecraftserv/paper) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/paper/README.md) |
> | Forge | Mods | [minecraftserv/forge](https://hub.docker.com/r/minecraftserv/forge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/forge/README.md) |
> | NeoForge | Mods | [minecraftserv/neoforge](https://hub.docker.com/r/minecraftserv/neoforge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/neoforge/README.md) |
> | Fabric | Mods (lightweight) | [minecraftserv/fabric](https://hub.docker.com/r/minecraftserv/fabric) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/fabric/README.md) |
> | Quilt | Mods (Fabric fork) | [minecraftserv/quilt](https://hub.docker.com/r/minecraftserv/quilt) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/quilt/README.md) |
> | **Velocity** (this image) | Proxy | [minecraftserv/velocity](https://hub.docker.com/r/minecraftserv/velocity) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/velocity/README.md) |

[Velocity](https://papermc.io/software/velocity), the PaperMC proxy. It is
not a game server: players connect to Velocity, which forwards them to your
backend servers (for example `minecraftserv/paper` images) and lets them
switch between servers. Every Velocity version and build published on the
PaperMC API is available, for `linux/amd64` and `linux/arm64`.

## Quick start

```bash
docker run -d --name proxy -p 25577:25577 -v proxy_data:/app minecraftserv/velocity:latest
```

The default port is **25577**. Edit `/app/velocity.toml` (created on first
start) to declare your backend servers and the player forwarding mode, then
restart the container. Put Velocity plugins in `/app/plugins/`.

Example with one Paper backend:

```yaml
services:
  proxy:
    image: minecraftserv/velocity:latest
    ports: ["25565:25577"]
    volumes: ["proxy_data:/app"]
  lobby:
    image: minecraftserv/paper:1.21
    volumes: ["lobby_data:/app"]
volumes:
  proxy_data:
  lobby_data:
```

In `velocity.toml`, point the server to `lobby:25565`, and configure the
backend for proxy forwarding as described in the
[Velocity documentation](https://docs.papermc.io/velocity/player-information-forwarding).

## Tags

Velocity is not tied to a Minecraft version: one build accepts every client
version it supports. Its tags use the **Velocity version** instead of the
Minecraft version, and the **build number** instead of the loader version.

| Tag | Points to |
|-----|-----------|
| `latest` (= `latest_latest`) | latest stable build of the highest Velocity version (currently a `-SNAPSHOT` line, the one PaperMC recommends) |
| `latest_experimental` (= `experimental`) | latest non-stable build of that version, if any |
| `snapshot` (= `snapshot_latest`) | latest build of the highest `-SNAPSHOT` line |
| `3.4.0-SNAPSHOT` (= `3.4.0-SNAPSHOT_latest`) | latest stable build of that version |
| `3.4.0-SNAPSHOT_523` | exactly that build |
| `3.4.0-SNAPSHOT_experimental` | latest non-stable build of that version |
| `3`, `3.4`, `3.4.0` (+ `-latest`) | highest version of that level; a final release ranks above its `-SNAPSHOT` (`3.4.0` points to `3.4.0-SNAPSHOT` until a final 3.4.0 exists) |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_MEMORY` | `512M` | JVM `-Xms` |
| `MAX_MEMORY` | `1G` | JVM `-Xmx` |
| `EXTRA_JAVA_OPTS` | (empty) | Additional JVM options |

Everything lives in `/app`: `velocity.toml`
([reference](https://docs.papermc.io/velocity/configuration)), `plugins/`,
`logs/`. Your files are kept when the image is updated. The shared entrypoint
also writes an `eula.txt`, which Velocity ignores.

Java: 21 for every version.
