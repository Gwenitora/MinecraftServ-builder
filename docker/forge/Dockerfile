# Image "forge" — https://files.minecraftforge.net
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

# L'installeur Forge moderne (>=1.17 environ) génère run.sh/run.bat qui
# référencent des fichiers d'arguments (@libraries/.../unix_args.txt et
# @user_jvm_args.txt). Pour les versions intermédiaires (~1.6-1.12.x) il
# produit directement un jar exécutable avec -jar : soit un jar "universal"
# (nom contenant "universal"), soit (ex: 1.12.2) directement
# "forge-<mc>-<loader>.jar" sans suffixe particulier. Ce jar référence dans
# son manifeste Class-Path: minecraft_server.jar (nom générique), alors que
# l'installeur télécharge un nom versionné (minecraft_server.X.jar) : on
# crée un lien générique pour que le classpath du jar le retrouve (sinon:
# "Could not find or load main class net.minecraft.server.MinecraftServer").
RUN set -eux; \
    java -jar installer.jar --installServer; \
    rm -f installer.jar installer.jar.log; \
    echo "forge-${MC_VERSION}-${LOADER_VERSION}" > .version; \
    if ! [ -f minecraft_server.jar ] && ls minecraft_server*.jar >/dev/null 2>&1; then \
        ln -s "$(ls minecraft_server*.jar | head -n1)" minecraft_server.jar; \
    fi; \
    if [ -f run.sh ]; then \
        ARGFILE=$(grep -oE '@libraries[^"[:space:]]*\.txt' run.sh | head -n1); \
        HAS_USERARGS=$(grep -c '@user_jvm_args.txt' run.sh || true); \
        USERARGS_PART=""; \
        [ "$HAS_USERARGS" != "0" ] && USERARGS_PART="@user_jvm_args.txt"; \
        printf '#!/bin/sh\nexec java $JAVA_OPTS %s %s nogui "$@"\n' "$USERARGS_PART" "$ARGFILE" > run.sh; \
    elif ls *-universal*.jar >/dev/null 2>&1; then \
        JAR=$(ls *-universal*.jar | head -n1); \
        printf '#!/bin/sh\nexec java $JAVA_OPTS -jar %s nogui "$@"\n' "$JAR" > run.sh; \
    elif [ -f "forge-${MC_VERSION}-${LOADER_VERSION}.jar" ]; then \
        printf '#!/bin/sh\nexec java $JAVA_OPTS -jar forge-%s-%s.jar nogui "$@"\n' "${MC_VERSION}" "${LOADER_VERSION}" > run.sh; \
    else \
        echo "Impossible de déterminer le script de lancement Forge pour ${MC_VERSION}-${LOADER_VERSION}" >&2; \
        exit 1; \
    fi; \
    chmod +x run.sh

FROM ${JAVA_RUNTIME_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/Gwenitora/MinecraftServ-builder"
LABEL org.opencontainers.image.description="Serveur Minecraft Forge"

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
