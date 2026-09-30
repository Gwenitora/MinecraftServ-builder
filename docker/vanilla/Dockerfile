# Image "vanilla" — serveur Minecraft officiel (Mojang), sans mod/plugin.
#
# Build (fourni par le workflow GitHub Actions / scripts/resolve_versions.py):
#   --build-arg JAVA_IMAGE=eclipse-temurin:21-jdk-jammy
#   --build-arg JAVA_RUNTIME_IMAGE=eclipse-temurin:21-jre-jammy
#   --build-arg MC_VERSION=1.21.2
#   --build-arg MANIFEST_URL=https://piston-meta.mojang.com/v1/packages/.../1.21.2.json
ARG JAVA_IMAGE=eclipse-temurin:21-jdk-jammy
ARG JAVA_RUNTIME_IMAGE=eclipse-temurin:21-jre-jammy

FROM ${JAVA_IMAGE} AS builder
ARG MC_VERSION
ARG MANIFEST_URL
WORKDIR /opt/server-src

RUN apt-get update && apt-get install -y --no-install-recommends curl jq && rm -rf /var/lib/apt/lists/*

# Le manifeste de version Mojang contient l'URL du jar serveur.
RUN set -eux; \
    curl -fsSL -o version.json "$MANIFEST_URL"; \
    SERVER_URL=$(jq -r '.downloads.server.url' version.json); \
    curl -fsSL -o server.jar "$SERVER_URL"; \
    rm -f version.json; \
    echo "vanilla-${MC_VERSION}" > .version; \
    printf '#!/bin/sh\nexec java $JAVA_OPTS -jar server.jar nogui "$@"\n' > run.sh; \
    chmod +x run.sh

FROM ${JAVA_RUNTIME_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/Gwenitora/MinecraftServ-builder"
LABEL org.opencontainers.image.description="Serveur Minecraft vanilla (officiel Mojang)"

ENV ACCEPT_EULA=true \
    MIN_MEMORY=1G \
    MAX_MEMORY=2G

COPY --from=builder /opt/server-src /opt/server-src
COPY entrypoint/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/app"]
WORKDIR /app
EXPOSE 25565/tcp 25565/udp

ENTRYPOINT ["/entrypoint.sh"]
