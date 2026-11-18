# "horizon" image: https://playhorizon.dev (Minecraft: Java Edition rewritten
# in Rust). horizon-server is a native program: no Java in this image.
#
# The image holds NONE of Minecraft's files (Horizon ships none either). The
# game files are prepared once by the user from their own copy of Minecraft
# (horizon-prepare --prepare) and mounted read-only, as in Horizon's own
# packaging/server/Dockerfile. See docker/horizon/README.md.
#
# The prebuilt server is published for Linux x86_64 only: this image is built
# for linux/amd64 only (.github/workflows/horizon.yml).
#
# Expected build args (provided by scripts/resolve_versions.py):
#   MC_VERSION (= the Minecraft version Horizon targets), LOADER_VERSION
#   (= "<date>-<commit>" of the Horizon build), SERVER_URL, SERVER_SHA256
# JAVA_IMAGE / JAVA_RUNTIME_IMAGE are passed to every loader and unused here.
ARG BASE_IMAGE=public.ecr.aws/docker/library/debian:bookworm-slim

FROM ${BASE_IMAGE} AS builder
ARG MC_VERSION
ARG LOADER_VERSION
ARG SERVER_URL
ARG SERVER_SHA256
WORKDIR /tmp/horizon

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    curl -fsSL -o server.tar.gz "$SERVER_URL"; \
    if [ -n "$SERVER_SHA256" ]; then echo "${SERVER_SHA256}  server.tar.gz" | sha256sum -c -; fi; \
    mkdir -p /opt/horizon; \
    tar -xzf server.tar.gz -C /opt/horizon --strip-components=1; \
    test -x /opt/horizon/horizon-server; \
    echo "horizon-${MC_VERSION}-${LOADER_VERSION}" > /opt/horizon/.version

FROM ${BASE_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/Gwenitora/MinecraftServ-builder"
LABEL org.opencontainers.image.description="Serveur Minecraft Horizon (Minecraft: Java Edition en Rust)"

# ca-certificates: online mode checks players' accounts over HTTPS.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/horizon/.local/horizon-client

COPY --from=builder /opt/horizon /opt/horizon
# Fails the build if a shared library (or the glibc version) the programs need
# is missing from this base image, instead of publishing an image that cannot
# start. horizon-engine is the game itself, started by horizon-server.
RUN set -eu; \
    for bin in horizon-server horizon-engine; do \
      if ldd "/opt/horizon/$bin" 2>&1 | grep -q 'not found'; then \
        ldd "/opt/horizon/$bin"; exit 1; \
      fi; \
    done

COPY docker/horizon/start.sh /start.sh
RUN chmod +x /start.sh

# HORIZON_NO_UPDATE_CHECK: the program is updated by pulling a newer image,
# never by `horizon-server update` inside the container.
ENV PATH=/opt/horizon:$PATH \
    HORIZON_NO_AUDIO=1 \
    HORIZON_NO_UPDATE_CHECK=1 \
    ACCEPT_EULA=true

VOLUME ["/app"]
WORKDIR /app
EXPOSE 25565/tcp

# horizon-server saves and stops cleanly on SIGTERM: give it time
# (docker run --stop-timeout 180, or stop_grace_period: 3m in Compose).
STOPSIGNAL SIGTERM
ENTRYPOINT ["/start.sh"]
