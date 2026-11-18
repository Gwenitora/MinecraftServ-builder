#!/bin/sh
# Entrypoint of the "horizon" image (the other loaders use
# entrypoint/entrypoint.sh, which is Java-specific).
#
#  - The program stays in /opt/horizon (part of the image); /app only holds
#    the server's own files (server.toml, worlds, backups, logs), so nothing
#    has to be copied into the volume and an image update never touches them.
#  - First start: `horizon-server init --yes` writes /app/server.toml from the
#    HORIZON_* variables (HORIZON_EULA, WORLD, SEED, PORT, WHITELIST, PLAYERS,
#    OP, ONLINE). Later starts use the file.
#  - HORIZON_EULA follows ACCEPT_EULA (true by default, as for every image of
#    this project) unless it is set explicitly.
set -e

cd /app

if [ -z "${HORIZON_EULA:-}" ]; then
  HORIZON_EULA="${ACCEPT_EULA:-true}"
fi
export HORIZON_EULA

echo "[start] Horizon $(cat /opt/horizon/.version 2>/dev/null || echo '?')"

if [ ! -f server.toml ]; then
  echo "[start] Premier démarrage : création de /app/server.toml (horizon-server init)."
  horizon-server init --yes
fi

exec horizon-server run "$@"
