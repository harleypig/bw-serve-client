# The bw CLI and `bw serve`, for recording the payloads in ../serve/.
#
# Built and run by record.py, which pairs it with a throwaway Vaultwarden
# on a private network. Nothing here is installed on the host.

FROM node:22.23.4-bookworm-slim

# The CLI release the payloads are recorded against. record.py passes the
# version from upstream/lock.json; this default only covers a bare build.
ARG BW_CLI_VERSION=2026.10.1

# openssl mints the one-run certificate (certs.sh); the CLI needs https.
RUN apt-get update \
  && apt-get install --yes --no-install-recommends openssl \
  && rm -rf /var/lib/apt/lists/*

RUN npm install --global --no-fund --no-audit "@bitwarden/cli@${BW_CLI_VERSION}" \
  && npm cache clean --force

# The CLI's state lives here and dies with the container.
ENV BITWARDENCLI_APPDATA_DIR=/tmp/bw-appdata

COPY register.js entrypoint.sh certs.sh /recorder/

USER node

EXPOSE 8087

ENTRYPOINT ["/bin/sh", "/recorder/entrypoint.sh"]
