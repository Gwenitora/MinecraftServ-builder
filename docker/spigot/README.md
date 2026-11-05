# minecraftserv/spigot

> This image is part of [MinecraftServ](https://github.com/Gwenitora/MinecraftServ-builder),
> a family of ready-to-use Minecraft server images. Other loaders are available:
>
> | Loader | Type | Docker Hub | Documentation |
> |--------|------|------------|---------------|
> | Vanilla | Official Mojang server | [minecraftserv/vanilla](https://hub.docker.com/r/minecraftserv/vanilla) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/vanilla/README.md) |
> | Bukkit | CraftBukkit (plugins) | [minecraftserv/bukkit](https://hub.docker.com/r/minecraftserv/bukkit) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/bukkit/README.md) |
> | **Spigot** (this image) | Plugins, optimized Bukkit | [minecraftserv/spigot](https://hub.docker.com/r/minecraftserv/spigot) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/spigot/README.md) |
> | Paper | Plugins, high performance | [minecraftserv/paper](https://hub.docker.com/r/minecraftserv/paper) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/paper/README.md) |
> | Forge | Mods | [minecraftserv/forge](https://hub.docker.com/r/minecraftserv/forge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/forge/README.md) |
> | NeoForge | Mods | [minecraftserv/neoforge](https://hub.docker.com/r/minecraftserv/neoforge) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/neoforge/README.md) |
> | Fabric | Mods (lightweight) | [minecraftserv/fabric](https://hub.docker.com/r/minecraftserv/fabric) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/fabric/README.md) |
> | Quilt | Mods (Fabric fork) | [minecraftserv/quilt](https://hub.docker.com/r/minecraftserv/quilt) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/quilt/README.md) |
> | Velocity | Proxy | [minecraftserv/velocity](https://hub.docker.com/r/minecraftserv/velocity) | [README](https://github.com/Gwenitora/MinecraftServ-builder/blob/main/docker/velocity/README.md) |

Spigot, the optimized Bukkit server, compiled from source with the official
[BuildTools](https://www.spigotmc.org/wiki/buildtools/) (no precompiled jar
may be redistributed). Every version listed by BuildTools is available, for
`linux/amd64` and `linux/arm64`. Bukkit and Spigot plugins work as is.

> ✅ The Mojang EULA is accepted automatically (`ACCEPT_EULA=true`). By using
> this image you accept <https://aka.ms/MinecraftEULA>.

## Quick start

```bash
docker run -d --name spigot -p 25565:25565 -v spigot_data:/app minecraftserv/spigot:latest
```

Put your plugins (`.jar`) in `/app/plugins/` and restart the container.

## Tags

| Tag | Points to |
|-----|-----------|
| `latest` | latest release |
| `snapshot` | most recent pre-release / release candidate built by BuildTools |
| `1.21.1` (= `1.21.1_latest`, `1.21.1-latest`) | exactly Minecraft 1.21.1 |
| `1` / `1.21` | highest 1.x.y / 1.21.y release |
| `1.18-snapshot` | newest pre-release / release candidate of 1.18.y |
| `1.18-pre8`, `1.18-rc3` | that exact pre-release |

Spigot has no separate loader version: the `_<loader>` suffix only exists as
`_latest`. Full tag rules:
[main README](https://github.com/Gwenitora/MinecraftServ-builder#tags).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ACCEPT_EULA` | `true` | Writes `eula=true`/`false` to `/app/eula.txt` |
| `MIN_MEMORY` | `1G` | JVM `-Xms` |
| `MAX_MEMORY` | `2G` | JVM `-Xmx` |
| `EXTRA_JAVA_OPTS` | (empty) | Additional JVM options |

Everything lives in `/app`: `server.properties`
([reference](https://minecraft.wiki/w/Server.properties)), `bukkit.yml`,
`spigot.yml` ([reference](https://www.spigotmc.org/wiki/spigot-configuration/)),
`plugins/`, `world/`, `logs/`. Your files are kept when the image is updated.

Java: 8 before 1.12, 11 for 1.12-1.16.5, 17 for 1.17-1.20.4, 21 from 1.20.5.

## Limitations

- 1.8 and 1.8.3 are not available: they depend on an artifact that was removed
  from every Maven repository (1.8.4 to 1.8.8 are available).
- Builds compile the server from source and are much slower than the other
  images: new versions may appear later.
