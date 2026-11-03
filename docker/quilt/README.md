# minecraftserv/quilt

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
> | **Quilt** (this image) | Mods (Fabric fork) | [minecraftserv/quilt](https://hub.docker.com/r/minecraftserv/quilt) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/quilt/README.md) |
> | Velocity | Proxy | [minecraftserv/velocity](https://hub.docker.com/r/minecraftserv/velocity) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/velocity/README.md) |

[Quilt](https://quiltmc.org), a fork of Fabric, installed with the official
Quilt installer. Every Minecraft version supported by Quilt (releases,
snapshots, pre-releases) is available, for `linux/amd64` and `linux/arm64`.
Most Fabric mods also work on Quilt.

> ✅ The Mojang EULA is accepted automatically (`ACCEPT_EULA=true`). By using
> this image you accept <https://aka.ms/MinecraftEULA>.

## Quick start

```bash
docker run -d --name quilt -p 25565:25565 -v quilt_data:/app -e MAX_MEMORY=4G minecraftserv/quilt:latest
```

Put your mods (`.jar`) in `/app/mods/` and restart the container. Mods must
match the Minecraft version of the tag.

## Tags

The loader version is the Quilt loader version (e.g. `0.27.1`).

| Tag | Points to |
|-----|-----------|
| `latest` | latest release + latest stable Quilt loader |
| `latest_experimental` | latest release + latest beta Quilt loader, if any |
| `snapshot` | most recent snapshot / pre-release / release candidate |
| `1.21.1` (= `1.21.1_latest`, `1.21.1-latest`) | Minecraft 1.21.1 + latest stable Quilt loader |
| `1.21.1_0.27.1` | Minecraft 1.21.1 + exactly Quilt loader 0.27.1 |
| `1.21.1_experimental` | Minecraft 1.21.1 + latest beta Quilt loader |
| `1` / `1.21` | highest 1.x.y / 1.21.y release |
| `1.21-snapshot` | newest snapshot leading to a 1.21.y version |

Full tag rules: [main README](https://github.com/Gwenitora/MinecraftServ-builder#tags).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCEPT_EULA` | `true` | Writes `eula=true`/`false` to `/app/eula.txt` |
| `MIN_MEMORY` | `1G` | JVM `-Xms` |
| `MAX_MEMORY` | `2G` | JVM `-Xmx` |
| `EXTRA_JAVA_OPTS` | (empty) | Additional JVM options |

Everything lives in `/app`: `server.properties`
([reference](https://minecraft.wiki/w/Server.properties)), `mods/`,
`config/` (one file per mod), `world/`, `logs/`. Your files are kept when the
image is updated.

Java: 8 before 1.12, 11 for 1.12-1.16.5, 17 for 1.17-1.20.4, 21 from 1.20.5.

## Limitations

- Quilt has no ready-made server jar: the official installer runs at build
  time and downloads the vanilla server itself.
