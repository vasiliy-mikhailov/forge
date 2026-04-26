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

# Build-time HTTPS smoke. The bench depends on factcheck.py reaching
# Wikipedia from inside the container; if either ca-certificates or system
# curl is broken, fail the build now rather than mid-experiment. The smoke
# also exercises the LD_LIBRARY_PATH="" workaround used by factcheck.py at
# runtime (PyInstaller-bundled openhands sets LD_LIBRARY_PATH to /tmp/_MEI*
# which shadows system libssl — see kurpatov-wiki-wiki/skills/benchmark/
# scripts/factcheck.py).
RUN set -e \
 && python3 -c "import urllib.request, ssl; \
        req = urllib.request.Request('https://en.wikipedia.org/wiki/Test', headers={'User-Agent': 'kurpatov-wiki-bench-smoke/1.0'}); \
        r = urllib.request.urlopen(req, timeout=10); \
        assert r.status == 200, r.status; \
        print('[smoke] python urllib HTTPS ok')" \
 && LD_LIBRARY_PATH="" curl -fsS -A kurpatov-wiki-bench-smoke/1.0 \
        -o /dev/null -w '[smoke] curl HTTPS ok (HTTP %{http_code})\n' \
        "https://en.wikipedia.org/wiki/Test"

# Working directory the agent operates in. The agent will git clone
# kurpatov-wiki-{raw,wiki} into here. /runs/current is the only
# bind-mount back to the host.
WORKDIR /workspace
RUN mkdir -p /runs

ENTRYPOINT ["/usr/local/bin/openhands"]
CMD ["--help"]
