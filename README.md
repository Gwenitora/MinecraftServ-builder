# MinecraftServ-builder

Images Docker prêtes à l'emploi pour héberger un serveur Minecraft, quel que
soit le loader : **vanilla, bukkit, spigot, paper, forge, neoforge, fabric,
quilt**. Toutes les versions officiellement publiées par chaque projet sont
disponibles — releases, snapshots, et versions historiques/expérimentales —
et les images sont reconstruites automatiquement chaque jour.

> ✅ **L'EULA Mojang est acceptée automatiquement** dans ces images
> (`ACCEPT_EULA=true` par défaut). En les utilisant, vous acceptez l'EULA
> officielle : <https://aka.ms/MinecraftEULA>. Mettez `ACCEPT_EULA=false` si
> vous souhaitez la refuser (le serveur ne démarrera pas).

## Images Docker Hub

| Loader     | Image                          | Site officiel des versions |
|------------|---------------------------------|------------------------------|
| Vanilla    | `minecraftserv/vanilla`        | https://www.minecraft.net/fr-fr/download/server |
| Bukkit     | `minecraftserv/bukkit`         | https://www.spigotmc.org/wiki/buildtools/ |
| Spigot     | `minecraftserv/spigot`         | https://www.spigotmc.org/wiki/buildtools/ |
| Paper      | `minecraftserv/paper`          | https://papermc.io/downloads/paper |
| Forge      | `minecraftserv/forge`          | https://files.minecraftforge.net |
| NeoForge   | `minecraftserv/neoforge`       | https://neoforged.net/ |
| Fabric     | `minecraftserv/fabric`         | https://fabricmc.net/use/server/ |
| Quilt      | `minecraftserv/quilt`          | https://quiltmc.org/en/install/server/ |

## Démarrage rapide

```bash
docker run -d --name my-server \
  -p 25565:25565 \
  -v mc_data:/app \
  -e MAX_MEMORY=4G \
  minecraftserv/paper:latest
```

Toutes les données du serveur (monde, config, logs) vivent dans `/app`. Vous
pouvez monter n'importe quel volume sur `/app` : au premier démarrage,
l'image y recopie automatiquement les fichiers nécessaires (jar, libs,
configuration par défaut). Si le volume est déjà initialisé, vos fichiers
personnalisés sont conservés.

### Variables d'environnement

| Variable          | Défaut | Description |
|-------------------|--------|--------------|
| `ACCEPT_EULA`      | `true` | Écrit `eula=true`/`false` dans `/app/eula.txt` au démarrage |
| `MIN_MEMORY`       | `1G`   | `-Xms` de la JVM |
| `MAX_MEMORY`       | `2G`   | `-Xmx` de la JVM |
| `EXTRA_JAVA_OPTS`  | (vide) | Options JVM additionnelles (ex: `-XX:+UseG1GC`) |

## Système de tags

Le séparateur entre la version Minecraft et la version du loader dans un tag
est **`_`** (underscore) — Docker n'autorise pas `:` dans un tag.

- `latest` : dernière version stable (release) du jeu, avec le build de
  loader recommandé/stable le plus récent.
- `snapshot` : dernière snapshot hebdomadaire du jeu.
- `experimental` : dernière version historique/expérimentale de Minecraft
  (anciennes versions *alpha*/*beta*, avant la 1.0) — voir la section
  « Canaux » ci-dessous pour la définition exacte.
- **Profondeur de version** : chaque niveau de précision d'une version
  release est disponible et pointe par défaut sur le plus récent de ce
  niveau :
  - `1` → dernière version `1.x.y`
  - `1.21` → dernière version `1.21.y`
  - `1.21.2` → exactement cette version
  - Chacun de ces tags est un alias de `<profondeur>-latest`. Les variantes
    `<profondeur>-snapshot` et `<profondeur>-experimental` existent aussi et
    pointent vers la snapshot/version expérimentale la plus proche de cette
    branche (ex: `1.21-snapshot`).
- **Version de loader précise** : ajoutez `_<version-loader>` à n'importe
  quel tag de version Minecraft pour figer une version de loader précise,
  par exemple `1.21.2_40.1.80` (NeoForge) ou `1.21.2_9.6.0` (Fabric). Sans ce
  suffixe, c'est toujours la dernière version de loader compatible qui est
  utilisée. Le suffixe accepte aussi `latest`, `snapshot` ou `experimental`
  comme mot-clé (ex: `1.21.2_experimental` pour la dernière build
  expérimentale du loader sur cette version de Minecraft), en plus d'une
  version exacte — jamais de version "semi-précise" côté loader.
- Pour `vanilla`, `bukkit` et `spigot`, il n'existe pas de version de loader
  séparée (le "loader" est la version du jeu elle-même), donc le suffixe
  `_<version-loader>` n'a pas d'effet utile.

### Canaux (comment une version est classée)

| Canal Docker   | Vanilla (type Mojang)      | Paper / Fabric / Quilt (API du projet) | Forge / NeoForge (nom du build) |
|----------------|-----------------------------|------------------------------------------|-----------------------------------|
| `latest`       | `release`                   | stable                                    | ne contient pas `beta`/`rc`/`pre` |
| `snapshot`     | `snapshot`                  | non-stable                                | — |
| `experimental` | `old_beta` / `old_alpha`    | —                                          | contient `beta`/`rc`/`pre`/`alpha` |

Cette classification vient directement des API officielles utilisées par
`scripts/resolve_versions.py` (voir plus bas).

## Architecture des fichiers dans `/app`

L'organisation exacte dépend de la version de Minecraft et du loader (par
exemple les noms de dossiers de librairies changent entre les grandes
versions), mais reste globalement stable :

```
/app
├── eula.txt                 # généré/écrasé automatiquement (ACCEPT_EULA)
├── server.properties        # configuration principale du serveur (créé au 1er lancement)
├── server.jar               # jar exécutable (vanilla/paper/spigot/bukkit/fabric/quilt)
├── run.sh                   # script de lancement (utilisé par forge/neoforge, ou généré pour les autres)
├── libraries/ ou versions/  # dépendances du serveur (présent selon le loader/version)
├── world/                   # sauvegarde du monde
├── plugins/                 # (bukkit/spigot/paper uniquement) plugins .jar
├── mods/                    # (forge/neoforge/fabric/quilt uniquement) mods .jar
├── config/                  # (forge/neoforge/fabric/quilt) configuration des mods
└── logs/
```

- **Bukkit / Spigot / Paper** : ajoutez vos plugins dans `/app/plugins/`.
- **Forge / NeoForge / Fabric / Quilt** : ajoutez vos mods dans `/app/mods/`
  (le jar doit être compatible avec la version de Minecraft **et** de loader
  du tag utilisé).
- Les chemins exacts des librairies (`libraries/net/minecraftforge/...`,
  `libraries/net/neoforged/...`, etc.) changent selon la version — c'est
  normal et géré automatiquement par `run.sh`, vous n'avez pas à vous en
  soucier.

## Documentation des fichiers de configuration

Paper dispose de la documentation la plus complète (et Bukkit/Spigot
partagent en grande partie `server.properties`/`bukkit.yml`) :

- `server.properties` (commun à tous les loaders) : https://minecraft.wiki/w/Server.properties
- Paper (`paper-global.yml`, `paper-world-defaults.yml`) : https://docs.papermc.io/paper/reference/paper-global.yml et https://docs.papermc.io/paper/reference/paper-world-defaults.yml
- Spigot (`spigot.yml`) : https://www.spigotmc.org/wiki/spigot-configuration/
- Bukkit (`bukkit.yml`) : https://bukkit.fandom.com/wiki/Bukkit.yml
- Forge/NeoForge (`config/*.toml` par mod) : documentation propre à chaque mod, généralement un fichier `.toml` commenté généré au premier lancement.
- Fabric/Quilt : chaque mod documente son propre fichier dans `config/` (souvent `.json`/`.toml`), pas de format unifié — voir la page du mod concerné.

## Architecture du projet / CI

```
docker/<loader>/Dockerfile        # une image par loader, tout est installé dans /app (via /opt/server-src)
entrypoint/entrypoint.sh          # entrypoint commun: init /app si vide, accepte l'EULA, lance run.sh
scripts/resolve_versions.py       # interroge les API officielles de chaque loader, calcule les tags
.github/actions/resolve-versions/ # action composite: calcule la matrix de build pour un loader
.github/actions/build-push/       # action composite: build + push une image (1 entrée de la matrix)
.github/workflows/<loader>.yml    # déclenchement quotidien (cron) par loader, utilise les 2 actions ci-dessus
.github/workflows/run-selected-builds.yml  # déclenche manuellement un ou plusieurs workflows <loader>.yml
```

### Lancer soi-même un ou plusieurs builds

Onglet **Actions** → workflow **run-selected-builds** → **Run workflow**.
Coche les loaders à reconstruire (ou la case **all** pour tous les
sélectionner), choisis le `mode` (`daily`/`backfill`) et lance. Ce workflow
déclenche à sa place chaque `<loader>.yml` correspondant via l'API GitHub
Actions (`gh workflow run`), donc chaque loader sélectionné tourne comme un
run indépendant (visible séparément dans l'onglet Actions).

### Comment fonctionne la mise à jour quotidienne

Chaque jour, pour chaque loader :
1. `resolve_versions.py` interroge l'API officielle du loader et liste
   toutes les versions Minecraft + toutes les versions de loader associées.
2. Le script compare avec les tags déjà présents sur Docker Hub et ne
   reconstruit que :
   - les tags "mouvants" (`latest`, `snapshot`, `experimental`, et toutes
     les variantes `-latest`/`-snapshot`/`-experimental` par profondeur),
   - les versions jamais construites auparavant.
3. Chaque job du matrix build l'image avec les bons `--build-arg` et la
   pousse avec tous ses tags sur `minecraftserv/<loader>`.

Étant donné le nombre très important de versions historiques (plusieurs
centaines, notamment pour Forge/Fabric), la reconstruction exhaustive de
**tout** l'historique n'est pas faite automatiquement chaque jour (ce serait
irréaliste en temps CI et en quota Docker Hub). Elle est disponible via le
mode manuel `backfill` :

```
gh workflow run forge.yml -f mode=backfill -f limit=100 -f offset=0
gh workflow run forge.yml -f mode=backfill -f limit=100 -f offset=100
...
```
(relancez en augmentant `offset` jusqu'à couvrir tout l'historique ; à
exécuter une fois, puis le mode `daily` prend le relais pour les nouvelles
versions et les tags mouvants).

## Mise en place du push vers Docker Hub

1. Connectez-vous sur https://hub.docker.com avec le compte `minecraftserv`.
2. Allez dans **Account Settings → Security → Access Tokens** et créez un
   token (permissions Read/Write), puis copiez-le (il ne sera plus affiché).
3. Dans ce dépôt GitHub : **Settings → Secrets and variables → Actions →
   New repository secret**, ajoutez :
   - `DOCKERHUB_USERNAME` = `minecraftserv`
   - `DOCKERHUB_TOKEN` = le token généré à l'étape 2
4. Créez les 8 dépôts Docker Hub (`minecraftserv/vanilla`, `.../bukkit`,
   `.../spigot`, `.../paper`, `.../forge`, `.../neoforge`, `.../fabric`,
   `.../quilt`) — publics, sinon les `docker pull` anonymes échoueront.
5. Les workflows tournent automatiquement chaque jour ; vous pouvez aussi
   les lancer manuellement depuis l'onglet **Actions** du dépôt
   (`workflow_dispatch`).

## Limites connues

- Forge antérieur à ~1.17 utilise un format d'installeur différent
  (jar "universal" au lieu de `run.sh`) : la Dockerfile gère ce cas mais des
  versions très anciennes peuvent nécessiter un ajustement ponctuel.
- Spigot/Bukkit sont compilés à la volée via BuildTools (légalement, aucun
  jar précompilé ne peut être redistribué) : le build est plus long que les
  autres loaders.
- L'association d'une snapshot/version expérimentale à une "profondeur" de
  release (ex: `1.21-snapshot`) est une heuristique du resolver — en cas de
  changement de nommage côté Mojang/loader, vérifiez le tag exact généré sur
  Docker Hub.
