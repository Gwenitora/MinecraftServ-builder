# Image "quilt" — https://quiltmc.org (fork de Fabric)
#
# Build args attendus (fournis par scripts/resolve_versions.py):
#   JAVA_RUNTIME_IMAGE, MC_VERSION, LOADER_VERSION, INSTALLER_URL
#
# Contrairement à Fabric, l'API Quilt n'expose pas d'endpoint "serveur
# fusionné" prêt à télécharger : il faut exécuter le quilt-installer
# officiel, qui télécharge lui-même le serveur vanilla et fusionne le
# loader. Le builder utilise donc toujours un JDK récent (indépendant de la
# version Java ciblée par le serveur final) pour être sûr de pouvoir
# exécuter cet installeur quelle que soit l'ancienneté de la version MC.
ARG JAVA_RUNTIME_IMAGE=eclipse-temurin:21-jre-jammy

FROM eclipse-temurin:21-jdk-jammy AS builder
ARG MC_VERSION
ARG LOADER_VERSION
ARG INSTALLER_URL
WORKDIR /opt/server-src

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    curl -fsSL -o /tmp/quilt-installer.jar "$INSTALLER_URL"; \
    java -jar /tmp/quilt-installer.jar install server "$MC_VERSION" "$LOADER_VERSION" \
        --download-server --install-dir=/opt/server-src; \
    rm -f /tmp/quilt-installer.jar; \
    echo "quilt-${MC_VERSION}-${LOADER_VERSION}" > .version; \
    printf '#!/bin/sh\nexec java $JAVA_OPTS -jar quilt-server-launch.jar nogui "$@"\n' > run.sh; \
    chmod +x run.sh

FROM ${JAVA_RUNTIME_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/Gwenitora/MinecraftServ-builder"
LABEL org.opencontainers.image.description="Serveur Minecraft Quilt"

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
