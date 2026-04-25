# kurpatov-wiki-bench — sandboxed agent harness
#
# Built once via `make build`. Runs once per `make bench` invocation
# (--rm-after-exit). Inside this container the agent has no view of
# the host's $HOME — only the explicit /runs/current bind mount.
#
# IMPORTANT: do NOT add /var/run/docker.sock as a volume in
# docker-compose / docker run wrappers. That would let the agent
# spawn sibling containers and break the sandbox.

FROM python:3.12-slim

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    OPENHANDS_SUPPRESS_BANNER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Minimal runtime: git for clone+push, jq for the agent's potential
# JSON wrangling, curl for HTTPS, ca-certificates for TLS verification.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        git \
        jq \
        curl \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Drop in the standalone OpenHands SDK CLI binary. The host /bin
# directory holds it (downloaded via README's curl one-liner; it's
# gitignored at 85 MB).
COPY bin/openhands /usr/local/bin/openhands
RUN chmod +x /usr/local/bin/openhands

# Working directory the agent operates in. The agent will git clone
# kurpatov-wiki-{raw,wiki} into here. /runs/current is the only
# bind-mount back to the host.
WORKDIR /workspace
RUN mkdir -p /runs

ENTRYPOINT ["/usr/local/bin/openhands"]
CMD ["--help"]
