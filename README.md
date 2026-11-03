# MinecraftServ-builder

Images Docker prêtes à l'emploi pour héberger un serveur Minecraft, quel que
soit le loader : **vanilla, bukkit, spigot, paper, forge, neoforge, fabric,
quilt**, ainsi que le proxy **velocity**. Toutes les versions officiellement publiées par chaque projet sont
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
| Velocity (proxy) | `minecraftserv/velocity` | https://papermc.io/software/velocity |

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
  - Un tag de profondeur partielle (`1`, `1.21`…) n'est posé **que** sur la
    release la plus haute de cette profondeur : la build de `1.20.1` ne
    reçoit plus les tags `1` ni `1.20`, seule `1.20.6` reçoit `1.20`. Ainsi
    un échec ou un ordre de build ne peut plus faire pointer `:1` vers une
    vieille version.
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

### Tags de Velocity (proxy)

Velocity n'est pas lié à une version de Minecraft : un même build accepte
toutes les versions clientes qu'il supporte. Ses tags reprennent donc le
même système, mais avec la **version de Velocity** à la place de la version
de Minecraft, et le **numéro de build** à la place de la version du loader :

| Tag | Pointe vers |
|-----|-------------|
| `latest` (= `latest_latest`) | dernier build stable de la version Velocity la plus haute (aujourd'hui une `-SNAPSHOT`, c'est la ligne que PaperMC recommande) |
| `latest_experimental` (= `experimental`) | dernier build non stable de cette version, s'il en existe |
| `snapshot` (= `snapshot_latest`) | dernier build de la ligne de dev `-SNAPSHOT` la plus haute |
| `3.4.0-SNAPSHOT` (= `3.4.0-SNAPSHOT_latest`) | dernier build stable de cette version |
| `3.4.0-SNAPSHOT_523` | exactement ce build |
| `3.4.0-SNAPSHOT_experimental` | dernier build non stable de cette version |
| `3`, `3.4`, `3.4.0` (+ `-latest`) | version la plus haute de ce niveau ; une version finale passe devant sa `-SNAPSHOT` (`3.4.0` pointe vers `3.4.0-SNAPSHOT` tant que `3.4.0` finale n'existe pas) |

Le port par défaut est `25577`, et la mémoire par défaut plus basse
(`MIN_MEMORY=512M`, `MAX_MEMORY=1G`). La configuration se trouve dans
`/app/velocity.toml` (créé au premier lancement) :
https://docs.papermc.io/velocity/configuration

```bash
docker run -d --name proxy -p 25577:25577 -v proxy_data:/app minecraftserv/velocity:latest
```

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
scripts/resolve_versions.py       # interroge les API officielles de chaque loader, calcule les tags, trie les builds
.github/actions/resolve-versions/ # action composite: calcule la matrix de build pour un loader
.github/actions/build-loader/     # action composite: build + push TOUTES les versions de la matrix, une par une, 1 nouvel essai par version, sans arrêt au 1er échec
.github/actions/reset-images/     # action composite: supprime tous les tags Docker Hub existants d'un loader (option "reset")
.github/workflows/<loader>.yml    # déclenchement quotidien (cron, décalé entre loaders ; velocity à 1 h UTC) par loader, job unique séquentiel utilisant les actions ci-dessus
.github/workflows/builds.yml       # déclenche manuellement un ou plusieurs workflows <loader>.yml
```

Les builds ne se lancent **jamais** sur un push ou un merge, quelle que soit
la branche : uniquement via le cron quotidien de chaque loader ou un
lancement manuel (`workflow_dispatch`, voir plus bas).

### Ordre de build et gestion des échecs

Chaque workflow `<loader>.yml` construit **une seule image à la fois**,
plutôt qu'en parallèle. En mode `daily`, les versions qui portent un tag
mouvant (`latest`, `snapshot`, `experimental`, et les tags de profondeur de
la branche active comme `1`, `1.21`, `1.21-latest`…) passent **en premier**,
puis les nouvelles versions dans l'ordre chronologique de sortie. En mode
`backfill`, l'ordre reste chronologique.

Si le build d'une version échoue (erreur Docker, téléchargement du jar,
limite de pulls, etc.), il est **réessayé une fois** après 60 s. S'il échoue
encore, la version est notée en échec et le job **continue** avec les
suivantes : un vieux build cassé ne bloque plus `latest` ni les versions
récentes. Le job est marqué en échec à la fin s'il reste au moins une
version ratée, et le résumé du run (onglet *Summary*) liste ces versions.

Le comportement historique (arrêt au premier échec) reste disponible via
l'entrée `continue_on_error: "false"` de l'action `build-loader`.

Pour tenir dans l'espace disque des runners GitHub (~14 Go libres), l'action
libère d'abord ~25 Go (SDK .NET/Android/GHC/CodeQL inutiles ici) et purge le
cache buildx après chaque version au-delà de 4 Go. Les images Java de base
(`eclipse-temurin`) sont tirées depuis le miroir ECR Public des images
officielles (`public.ecr.aws/docker/library`) pour ne pas consommer le quota
de pulls Docker Hub.

### Option « reset » : repartir de zéro

Chaque workflow `<loader>.yml` (et le dispatcher `builds.yml`)
propose une case à cocher **`reset`** dans le formulaire `workflow_dispatch`.
Si elle est cochée, **avant** de calculer la matrix et de lancer les builds,
l'action `reset-images` supprime **tous** les tags déjà présents sur
`minecraftserv/<loader>` (le token Docker Hub doit avoir les droits de
suppression). Cela permet de repartir d'un dépôt Docker Hub vide et de
relancer un backfill complet pendant les phases de test, sans avoir à
nettoyer manuellement Docker Hub. À utiliser avec précaution : l'opération
est irréversible.

### Lancer soi-même un ou plusieurs builds

Onglet **Actions** → workflow **builds** → **Run workflow**.
Coche les loaders à reconstruire (ou la case **all** pour tous les
sélectionner), choisis le `mode` (`daily`/`backfill`), coche `reset` si tu
veux d'abord supprimer tous les tags Docker Hub existants pour ces loaders,
et lance. Ce workflow déclenche à sa place chaque `<loader>.yml`
correspondant via l'API GitHub Actions (`gh workflow run`), donc chaque
loader sélectionné tourne comme un run indépendant (visible séparément dans
l'onglet Actions), et chacun construit ses versions une par une (voir
ci-dessus).

### Comment fonctionne la mise à jour quotidienne

Chaque jour, pour chaque loader :
1. `resolve_versions.py` interroge l'API officielle du loader et liste
   toutes les versions Minecraft + toutes les versions de loader associées.
2. Le script compare avec les tags déjà présents sur Docker Hub et ne
   reconstruit que :
   - les versions qui portent un tag "mouvant" : `latest`, `snapshot`,
     `experimental`, et les tags de profondeur de la **branche active**
     (ex: `1`, `1.21`, `1-latest`, `1.21-snapshot`). Une ancienne release
     comme `1.12.2` ne porte plus que des tags qui ne bougent plus
     (`1.12.2`, `1.12.2-latest`, `1.12`…) et n'est donc **pas** reconstruite
     chaque jour ;
   - les versions jamais construites auparavant, y compris une nouvelle
     build de loader pour une version Minecraft existante (détectée via le
     tag explicite `<mc>_<loader>`).
3. Chaque version est construite **séquentiellement** (pas en parallèle) et
   poussée avec tous ses tags sur `minecraftserv/<loader>`, tags mouvants
   d'abord. Une version en échec n'empêche pas les suivantes (voir
   « Ordre de build et gestion des échecs »).

> ⚠️ Un run GitHub Actions est limité à ~6h d'exécution (`timeout-minutes:
> 350` dans chaque workflow). Un backfill complet de plusieurs centaines de
> versions peut donc nécessiter plusieurs runs successifs (voir `--limit`/
> `--offset` ci-dessous) : c'est normal et prévu.

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
   token avec permissions **Read, Write, Delete** (le *Delete* est
   nécessaire pour l'option `reset`, qui supprime des tags), puis copiez-le
   (il ne sera plus affiché).
3. Dans ce dépôt GitHub : **Settings → Secrets and variables → Actions →
   New repository secret**, ajoutez :
   - `DOCKERHUB_USERNAME` = `minecraftserv`
   - `DOCKERHUB_TOKEN` = le token généré à l'étape 2
4. Créez les 9 dépôts Docker Hub (`minecraftserv/vanilla`, `.../bukkit`,
   `.../spigot`, `.../paper`, `.../forge`, `.../neoforge`, `.../fabric`,
   `.../quilt`, `.../velocity`) — publics, sinon les `docker pull` anonymes échoueront.
5. Les workflows tournent automatiquement chaque jour ; vous pouvez aussi
   les lancer manuellement depuis l'onglet **Actions** du dépôt
   (`workflow_dispatch`).

## Limites connues

- **Forge antérieur à 1.6** (ex: 1.1 à 1.5.2 inclus) n'est **pas
  proposé** : avant 1.5.2, Forge ne publiait pas de `-installer.jar` (format
  `-server.zip`/`-client.zip` différent, non supporté). Et 1.5.2 elle-même
  est exclue car son FML télécharge au 1er lancement des librairies depuis
  `files.minecraftforge.net/fmllibs/`, un hôte définitivement mort (404) —
  le serveur ne peut jamais démarrer même si le build réussit. Ces versions
  sont automatiquement exclues par `resolve_versions.py`.
- **Forge antérieur à 1.13** utilise systématiquement Java 8, quelle que
  soit la version de Minecraft : son ancien launcher ("FML/launchwrapper")
  caste explicitement le system classloader en `java.net.URLClassLoader`,
  retiré en Java 9+, ce qui plante le serveur au démarrage. Géré
  automatiquement par `resolve_versions.py` (indépendant de l'heuristique
  Java générale utilisée par les autres loaders).
- **Minecraft 1.20.5 et 1.20.6** exigent Java 21 (comme toute la 1.21) ;
  `resolve_versions.py` en tient compte (1.20.4 et antérieures restent en
  Java 17).
- Quilt n'expose pas d'endpoint "jar serveur fusionné" prêt à l'emploi
  (contrairement à Fabric) : l'image exécute l'installeur officiel Quilt
  (`quilt-installer ... install server <mc> <loader> --download-server`) au
  moment du build, qui télécharge lui-même le jar vanilla et les librairies.
- **Vanilla antérieur à 1.2.5** (toutes les `old_alpha`/`old_beta`, et les
  releases 1.0 à 1.2.4) n'est **pas proposé** : le manifeste officiel Mojang
  ne référence aucun jar serveur dédié pour ces versions (champ
  `downloads.server` absent), seulement un client. Automatiquement exclu.
- Spigot/Bukkit sont compilés à la volée via BuildTools (légalement, aucun
  jar précompilé ne peut être redistribué) : le build est plus long que les
  autres loaders.
- **Spigot 1.8 et 1.8.3** (uniquement ces deux versions précises) ne sont
  **pas proposées** : elles dépendent de
  `net.md-5:bungeecord-chat:1.8-SNAPSHOT`, un artefact jamais promu en
  release et depuis purgé de tous les dépôts Sonatype/mirrors connus (404
  partout). 1.8.4 à 1.8.8 partagent un autre build et ne sont pas affectées.
  CraftBukkit 1.8/1.8.3 (qui ne dépendent pas de ce module) restent
  disponibles normalement. Automatiquement exclues.
- **NeoForge 20.4.0-beta** (MC 1.20.4) n'est **pas proposée** : son
  installeur embarque une vérification de connectivité réseau qui interroge
  `authserver.mojang.com`, un nom dont le CNAME pointe vers une distribution
  CloudFront aujourd'hui supprimée (NXDOMAIN permanent). Toutes les autres
  versions (y compris les betas voisines) ne sont pas affectées.
  Automatiquement exclue.
- L'association d'une snapshot/version expérimentale à une "profondeur" de
  release (ex: `1.21-snapshot`) est une heuristique du resolver — en cas de
  changement de nommage côté Mojang/loader, vérifiez le tag exact généré sur
  Docker Hub.
