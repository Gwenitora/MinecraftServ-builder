# Image "velocity" — https://papermc.io/software/velocity (proxy Minecraft).
#
# Velocity n'est pas un serveur de jeu mais un proxy placé devant des
# serveurs (paper, fabric...). Il est versionné indépendamment de Minecraft :
# MC_VERSION contient ici la version de Velocity (ex: 3.4.0-SNAPSHOT) et
# LOADER_VERSION le numéro de build.
#
# Build args attendus (fournis par scripts/resolve_versions.py):
#   JAVA_IMAGE, JAVA_RUNTIME_IMAGE, MC_VERSION (= version Velocity),
#   LOADER_VERSION (= build Velocity), JAR_URL
ARG JAVA_IMAGE=public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy
ARG JAVA_RUNTIME_IMAGE=public.ecr.aws/docker/library/eclipse-temurin:21-jre-jammy

FROM ${JAVA_IMAGE} AS builder
ARG MC_VERSION
ARG LOADER_VERSION
ARG JAR_URL
WORKDIR /opt/server-src

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    curl -fsSL -o velocity.jar "$JAR_URL"; \
    echo "velocity-${MC_VERSION}-${LOADER_VERSION}" > .version; \
    printf '#!/bin/sh\nexec java $JAVA_OPTS -jar velocity.jar "$@"\n' > run.sh; \
    chmod +x run.sh

FROM ${JAVA_RUNTIME_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/Gwenitora/MinecraftServ-builder"
LABEL org.opencontainers.image.description="Proxy Minecraft Velocity"

# Un proxy consomme peu de mémoire : valeurs par défaut plus basses que pour
# un serveur de jeu (recommandation PaperMC : 512 Mo à 1 Go).
ENV ACCEPT_EULA=true \
    MIN_MEMORY=512M \
    MAX_MEMORY=1G

COPY --from=builder /opt/server-src /opt/server-src
COPY entrypoint/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/app"]
WORKDIR /app
EXPOSE 25577/tcp 25577/udp

ENTRYPOINT ["/entrypoint.sh"]
