# "quilt" image: https://quiltmc.org (fork of Fabric)
#
# Expected build args (provided by scripts/resolve_versions.py):
#   JAVA_RUNTIME_IMAGE, MC_VERSION, LOADER_VERSION, INSTALLER_URL
#
# Unlike Fabric, the Quilt API does not expose a ready-to-download "merged
# server" endpoint: the official quilt-installer has to run, and it
# downloads the vanilla server itself and merges the loader. The builder
# therefore always uses a recent JDK (independent of the Java version
# targeted by the final server) to be sure it can run this installer
# whatever the age of the MC version.
#
# The base images come from the ECR Public mirror of the official Docker
# images (public.ecr.aws/docker/library) so they do not consume the Docker
# Hub pull quota.
ARG JAVA_RUNTIME_IMAGE=public.ecr.aws/docker/library/eclipse-temurin:21-jre-jammy

FROM public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy AS builder
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
