# minecraftserv/vanilla

> This image is part of [MinecraftServ](https://github.com/Gwenitora/MinecraftServ-builder),
> a family of ready-to-use Minecraft server images. Other loaders are available:
>
> | Loader | Type | Docker Hub | Documentation |
> |--------|------|------------|---------------|
> | **Vanilla** (this image) | Official Mojang server | [minecraftserv/vanilla](https://hub.docker.com/r/minecraftserv/vanilla) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/vanilla/README.md) |
> | Bukkit | CraftBukkit (plugins) | [minecraftserv/bukkit](https://hub.docker.com/r/minecraftserv/bukkit) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/bukkit/README.md) |
> | Spigot | Plugins, optimized Bukkit | [minecraftserv/spigot](https://hub.docker.com/r/minecraftserv/spigot) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/spigot/README.md) |
> | Paper | Plugins, high performance | [minecraftserv/paper](https://hub.docker.com/r/minecraftserv/paper) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/paper/README.md) |
> | Forge | Mods | [minecraftserv/forge](https://hub.docker.com/r/minecraftserv/forge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/forge/README.md) |
> | NeoForge | Mods | [minecraftserv/neoforge](https://hub.docker.com/r/minecraftserv/neoforge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/neoforge/README.md) |
> | Fabric | Mods (lightweight) | [minecraftserv/fabric](https://hub.docker.com/r/minecraftserv/fabric) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/fabric/README.md) |
> | Quilt | Mods (Fabric fork) | [minecraftserv/quilt](https://hub.docker.com/r/minecraftserv/quilt) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/quilt/README.md) |
> | Velocity | Proxy | [minecraftserv/velocity](https://hub.docker.com/r/minecraftserv/velocity) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/velocity/README.md) |

The official Minecraft server from Mojang, without mods or plugins. Every
version with a dedicated server jar is available (1.2.5 and newer), including
weekly snapshots, pre-releases and release candidates, for `linux/amd64` and
`linux/arm64`.

> ✅ The Mojang EULA is accepted automatically (`ACCEPT_EULA=true`). By using
> this image you accept <https://aka.ms/MinecraftEULA>.

## Quick start

```bash
docker run -d --name vanilla -p 25565:25565 -v vanilla_data:/app minecraftserv/vanilla:latest
```

```yaml
services:
  minecraft:
    image: minecraftserv/vanilla:1.21
    ports: ["25565:25565"]
    environment:
      MAX_MEMORY: 4G
    volumes: ["vanilla_data:/app"]
    restart: unless-stopped
volumes:
  vanilla_data:
```

## Tags

| Tag | Points to |
|-----|-----------|
| `latest` | latest release |
| `snapshot` | most recent snapshot / pre-release / release candidate |
| `1.21.1` (= `1.21.1_latest`, `1.21.1-latest`) | exactly Minecraft 1.21.1 |
| `1` / `1.21` | highest 1.x.y / 1.21.y release |
| `1.21-snapshot` | newest snapshot leading to a 1.21.y version |
| `24w10a`, `1.21-pre1`, `1.21-rc1` | that exact snapshot |
| `1.20.0` | the release named "1.20" (`1.20` itself is the branch tag) |

Vanilla has no separate loader: the `_<loader>` suffix only exists as
`_latest`. Weekly snapshots belong to the release that followed them, so
`24w10a` counts as a 1.20.5 snapshot. Full tag rules:
[main README](https://github.com/Gwenitora/MinecraftServ-builder#tags).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCEPT_EULA` | `true` | Writes `eula=true`/`false` to `/app/eula.txt` |
| `MIN_MEMORY` | `1G` | JVM `-Xms` |
| `MAX_MEMORY` | `2G` | JVM `-Xmx` |
| `EXTRA_JAVA_OPTS` | (empty) | Additional JVM options |

Everything lives in `/app`: `server.properties`
([reference](https://minecraft.wiki/w/Server.properties)), `world/`, `logs/`.
Your files are kept when the image is updated.

Java: 8 before 1.12, 11 for 1.12-1.16.5, 17 for 1.17-1.20.4, 21 from 1.20.5.

## Limitations

- Versions before 1.2.5 (all alpha/beta and 1.0 to 1.2.4) are not available:
  Mojang publishes no server jar for them.
