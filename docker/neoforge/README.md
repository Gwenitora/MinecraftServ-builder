# minecraftserv/neoforge

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
> | **NeoForge** (this image) | Mods | [minecraftserv/neoforge](https://hub.docker.com/r/minecraftserv/neoforge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/neoforge/README.md) |
> | Fabric | Mods (lightweight) | [minecraftserv/fabric](https://hub.docker.com/r/minecraftserv/fabric) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/fabric/README.md) |
> | Quilt | Mods (Fabric fork) | [minecraftserv/quilt](https://hub.docker.com/r/minecraftserv/quilt) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/quilt/README.md) |
> | Velocity | Proxy | [minecraftserv/velocity](https://hub.docker.com/r/minecraftserv/velocity) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/velocity/README.md) |

[NeoForge](https://neoforged.net), the community fork of Forge, installed
with the official installer. Every NeoForge build (Minecraft 1.20.2 and
newer) is available, for `linux/amd64` and `linux/arm64`.

> ✅ The Mojang EULA is accepted automatically (`ACCEPT_EULA=true`). By using
> this image you accept <https://aka.ms/MinecraftEULA>.

## Quick start

```bash
docker run -d --name neoforge -p 25565:25565 -v neoforge_data:/app -e MAX_MEMORY=6G minecraftserv/neoforge:1.21.1
```

Put your mods (`.jar`) in `/app/mods/` and restart the container. Mods must
match both the Minecraft version and the NeoForge version of the tag.

## Tags

The loader version is the NeoForge version (e.g. `21.1.77` for Minecraft
1.21.1).

| Tag | Points to |
|-----|-----------|
| `latest` | latest release + latest stable NeoForge build |
| `latest_experimental` | latest release + latest beta NeoForge build, if any |
| `1.21.1` (= `1.21.1_latest`, `1.21.1-latest`) | Minecraft 1.21.1 + latest stable NeoForge build |
| `1.21.1_21.1.77` | Minecraft 1.21.1 + exactly NeoForge 21.1.77 |
| `1.21.1_experimental` | Minecraft 1.21.1 + latest beta NeoForge build |
| `1` / `1.21` | highest 1.x.y / 1.21.y release |
| `1.21.0` | the release named "1.21" (`1.21` itself is the branch tag) |

Full tag rules: [main README](https://github.com/Gwenitora/MinecraftServ-builder#tags).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCEPT_EULA` | `true` | Writes `eula=true`/`false` to `/app/eula.txt` |
| `MIN_MEMORY` | `1G` | JVM `-Xms` |
| `MAX_MEMORY` | `2G` | JVM `-Xmx` (modpacks usually need 4G or more) |
| `EXTRA_JAVA_OPTS` | (empty) | Additional JVM options |

Everything lives in `/app`: `server.properties`
([reference](https://minecraft.wiki/w/Server.properties)), `mods/`,
`config/` (one file per mod), `world/`, `logs/`. Your files are kept when the
image is updated.

Java: 17 for 1.20.2-1.20.4, 21 from 1.20.5.

## Limitations

- NeoForge 20.4.0-beta is not available: its installer always crashes on a
  network check against a host that no longer exists.
