# minecraftserv/paper

> This image is part of [MinecraftServ](https://github.com/Gwenitora/MinecraftServ-builder),
> a family of ready-to-use Minecraft server images. Other loaders are available:
>
> | Loader | Type | Docker Hub | Documentation |
> |--------|------|------------|---------------|
> | Vanilla | Official Mojang server | [minecraftserv/vanilla](https://hub.docker.com/r/minecraftserv/vanilla) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/vanilla/README.md) |
> | Bukkit | CraftBukkit (plugins) | [minecraftserv/bukkit](https://hub.docker.com/r/minecraftserv/bukkit) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/bukkit/README.md) |
> | Spigot | Plugins, optimized Bukkit | [minecraftserv/spigot](https://hub.docker.com/r/minecraftserv/spigot) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/spigot/README.md) |
> | **Paper** (this image) | Plugins, high performance | [minecraftserv/paper](https://hub.docker.com/r/minecraftserv/paper) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/paper/README.md) |
> | Forge | Mods | [minecraftserv/forge](https://hub.docker.com/r/minecraftserv/forge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/forge/README.md) |
> | NeoForge | Mods | [minecraftserv/neoforge](https://hub.docker.com/r/minecraftserv/neoforge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/neoforge/README.md) |
> | Fabric | Mods (lightweight) | [minecraftserv/fabric](https://hub.docker.com/r/minecraftserv/fabric) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/fabric/README.md) |
> | Quilt | Mods (Fabric fork) | [minecraftserv/quilt](https://hub.docker.com/r/minecraftserv/quilt) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/quilt/README.md) |
> | Velocity | Proxy | [minecraftserv/velocity](https://hub.docker.com/r/minecraftserv/velocity) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/velocity/README.md) |

[Paper](https://papermc.io/software/paper), the high-performance fork of
Spigot. Every Minecraft version and every Paper build published on the PaperMC
API is available, for `linux/amd64` and `linux/arm64`. Bukkit, Spigot and
Paper plugins work as is.

> ✅ The Mojang EULA is accepted automatically (`ACCEPT_EULA=true`). By using
> this image you accept <https://aka.ms/MinecraftEULA>.

## Quick start

```bash
docker run -d --name paper -p 25565:25565 -v paper_data:/app -e MAX_MEMORY=4G minecraftserv/paper:latest
```

Put your plugins (`.jar`) in `/app/plugins/` and restart the container.

## Tags

The loader version is the Paper build number.

| Tag | Points to |
|-----|-----------|
| `latest` | latest release + latest stable Paper build |
| `latest_experimental` | latest release + latest experimental Paper build, if any |
| `snapshot` | most recent pre-release / release candidate |
| `1.21.4` (= `1.21.4_latest`, `1.21.4-latest`) | Minecraft 1.21.4 + latest stable Paper build |
| `1.21.4_232` | Minecraft 1.21.4 + exactly Paper build 232 |
| `1.21.4_experimental` | Minecraft 1.21.4 + latest experimental Paper build |
| `1` / `1.21` | highest 1.x.y / 1.21.y release |
| `1.21-snapshot` | newest pre-release / release candidate of 1.21.y |

Full tag rules: [main README](https://github.com/Gwenitora/MinecraftServ-builder#tags).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCEPT_EULA` | `true` | Writes `eula=true`/`false` to `/app/eula.txt` |
| `MIN_MEMORY` | `1G` | JVM `-Xms` |
| `MAX_MEMORY` | `2G` | JVM `-Xmx` |
| `EXTRA_JAVA_OPTS` | (empty) | Additional JVM options |

Everything lives in `/app`: `server.properties`
([reference](https://minecraft.wiki/w/Server.properties)), `bukkit.yml`,
`spigot.yml`, `config/paper-global.yml` and `paper-world-defaults.yml`
([reference](https://docs.papermc.io/paper/reference/configuration)),
`plugins/`, `world/`, `logs/`. Your files are kept when the image is updated.

Java: 11 for 1.12-1.16.5, 17 for 1.17-1.20.4, 21 from 1.20.5.
