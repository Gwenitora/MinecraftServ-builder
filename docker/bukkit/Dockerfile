# Image "bukkit" (CraftBukkit) — compilé via BuildTools officiel
# (https://www.spigotmc.org/wiki/buildtools/). CraftBukkit est l'implémentation
# de référence de l'API Bukkit, sans les optimisations Spigot.
#
# Build args attendus (fournis par scripts/resolve_versions.py):
#   JAVA_IMAGE, JAVA_RUNTIME_IMAGE, MC_VERSION (= BUILDTOOLS_REV)
ARG JAVA_IMAGE=eclipse-temurin:21-jdk-jammy
ARG JAVA_RUNTIME_IMAGE=eclipse-temurin:21-jre-jammy

FROM ${JAVA_IMAGE} AS builder
ARG MC_VERSION
ARG BUILDTOOLS_REV
WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git maven ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global user.email "build@minecraftserv.local" \
    && git config --global user.name "MinecraftServ Builder" \
    && git config --global --add safe.directory '*'

RUN curl -fsSL -o BuildTools.jar https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar

RUN set -eux; \
    java -jar BuildTools.jar --rev "${BUILDTOOLS_REV:-$MC_VERSION}" --compile CRAFTBUKKIT --output-dir /opt/server-src; \
    cd /opt/server-src; \
    JAR=$(ls craftbukkit-*.jar | head -n1); \
    mv "$JAR" server.jar; \
    echo "bukkit-${MC_VERSION}" > .version; \
    printf '#!/bin/sh\nexec java $JAVA_OPTS -jar server.jar nogui "$@"\n' > run.sh; \
    chmod +x run.sh

FROM ${JAVA_RUNTIME_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/Gwenitora/MinecraftServ-builder"
LABEL org.opencontainers.image.description="Serveur Minecraft CraftBukkit (compilé via BuildTools)"

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
