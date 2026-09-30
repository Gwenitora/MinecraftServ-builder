# Image "neoforge" — https://neoforged.net
#
# Build args attendus (fournis par scripts/resolve_versions.py):
#   JAVA_IMAGE, JAVA_RUNTIME_IMAGE, MC_VERSION, LOADER_VERSION, INSTALLER_URL
ARG JAVA_IMAGE=eclipse-temurin:21-jdk-jammy
ARG JAVA_RUNTIME_IMAGE=eclipse-temurin:21-jre-jammy

FROM ${JAVA_IMAGE} AS builder
ARG MC_VERSION
ARG LOADER_VERSION
ARG INSTALLER_URL
WORKDIR /opt/server-src

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL -o installer.jar "$INSTALLER_URL"

# NeoForge ne supporte que les versions récentes (>= 1.20.2), l'installeur
# génère systématiquement run.sh référencant des fichiers d'arguments.
RUN set -eux; \
    java -jar installer.jar --installServer; \
    rm -f installer.jar installer.jar.log; \
    echo "neoforge-${MC_VERSION}-${LOADER_VERSION}" > .version; \
    ARGFILE=$(grep -oE '@libraries[^"[:space:]]*\.txt' run.sh | head -n1); \
    HAS_USERARGS=$(grep -c '@user_jvm_args.txt' run.sh || true); \
    USERARGS_PART=""; \
    [ "$HAS_USERARGS" != "0" ] && USERARGS_PART="@user_jvm_args.txt"; \
    printf '#!/bin/sh\nexec java $JAVA_OPTS %s %s nogui "$@"\n' "$USERARGS_PART" "$ARGFILE" > run.sh; \
    chmod +x run.sh

FROM ${JAVA_RUNTIME_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/Gwenitora/MinecraftServ-builder"
LABEL org.opencontainers.image.description="Serveur Minecraft NeoForge"

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
