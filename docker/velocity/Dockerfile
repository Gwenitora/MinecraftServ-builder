# "velocity" image: https://papermc.io/software/velocity (Minecraft proxy).
#
# Velocity is not a game server but a proxy placed in front of servers
# (paper, fabric...). It is versioned independently from Minecraft:
# MC_VERSION holds the Velocity version here (e.g. 3.4.0-SNAPSHOT) and
# LOADER_VERSION the build number.
#
# Expected build args (provided by scripts/resolve_versions.py):
#   JAVA_IMAGE, JAVA_RUNTIME_IMAGE, MC_VERSION (= Velocity version),
#   LOADER_VERSION (= Velocity build), JAR_URL
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

# A proxy uses little memory: lower defaults than for a game server
# (PaperMC recommendation: 512 MB to 1 GB).
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
