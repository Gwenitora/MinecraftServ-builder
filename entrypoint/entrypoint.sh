#!/bin/sh
# Entrypoint commun à tous les loaders (vanilla, bukkit, spigot, paper,
# forge, neoforge, fabric, quilt).
#
# Rôle:
#  - rendre l'image "volume-safe": si /app est un volume monté vide (ou
#    obsolète), on y recopie les fichiers embarqués dans l'image (/opt/server-src)
#  - accepter automatiquement l'EULA Mojang (ACCEPT_EULA=true par défaut)
#  - exposer les réglages mémoire/JVM classiques via variables d'environnement
#  - lancer le serveur via le run.sh généré au build (spécifique au loader)
set -e

APP_DIR="/app"
SRC_DIR="/opt/server-src"
MARKER="$APP_DIR/.mcserv-baked-version"

mkdir -p "$APP_DIR"

BAKED_VERSION="$(cat "$SRC_DIR/.version" 2>/dev/null || echo unknown)"
CURRENT_VERSION="$(cat "$MARKER" 2>/dev/null || echo "")"

if [ ! -f "$MARKER" ] || [ "$CURRENT_VERSION" != "$BAKED_VERSION" ]; then
  echo "[entrypoint] Initialisation/mise à jour de $APP_DIR avec la version embarquée dans l'image ($BAKED_VERSION)"
  cp -a "$SRC_DIR"/. "$APP_DIR"/
  echo "$BAKED_VERSION" > "$MARKER"
else
  echo "[entrypoint] $APP_DIR déjà initialisé (version $CURRENT_VERSION) : fichiers utilisateur conservés."
fi

if [ "${ACCEPT_EULA:-true}" = "true" ]; then
  echo "eula=true" > "$APP_DIR/eula.txt"
else
  echo "eula=false" > "$APP_DIR/eula.txt"
  echo "[entrypoint] ACCEPT_EULA=false : le serveur refusera de démarrer tant que l'EULA n'est pas acceptée."
  echo "[entrypoint] Définissez ACCEPT_EULA=true (valeur par défaut de ces images) pour l'accepter automatiquement."
fi

cd "$APP_DIR"

export JAVA_OPTS="-Xms${MIN_MEMORY:-1G} -Xmx${MAX_MEMORY:-2G} ${EXTRA_JAVA_OPTS:-}"

exec "$APP_DIR/run.sh" "$@"
