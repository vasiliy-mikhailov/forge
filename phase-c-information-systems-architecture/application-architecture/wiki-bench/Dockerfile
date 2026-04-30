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

# Wrappers for `curl` and `python3` that strip LD_LIBRARY_PATH before
# exec'ing the real binary. This neutralises the PyInstaller-openhands env
# leak: when /usr/local/bin/openhands runs as PyInstaller, it sets
# LD_LIBRARY_PATH=/tmp/_MEI<random>/ so its bundled python finds bundled
# libs. That LD_LIBRARY_PATH is inherited by every shell subprocess, and
# the bundled libssl.so.3 (older) shadows system libssl/libcurl, breaking
# bare `curl` and bare `python3 urllib`. The agent in D7-rev2 attempt #1
# wasted ~28s rediscovering this. Wrappers eliminate the symptom at source.
# /usr/local/bin/ precedes /usr/bin/ in PATH; /usr/local/bin/python3 was
# a symlink to python3.12 which we replace with a wrapper that exec's
# python3.12 directly.
RUN set -e \
 && rm -f /usr/local/bin/python3 \
 && printf '%s\n' '#!/bin/sh' 'unset LD_LIBRARY_PATH' 'exec /usr/local/bin/python3.12 "$@"' \
        > /usr/local/bin/python3 \
 && chmod +x /usr/local/bin/python3 \
 && printf '%s\n' '#!/bin/sh' 'unset LD_LIBRARY_PATH' 'exec /usr/bin/curl "$@"' \
        > /usr/local/bin/curl \
 && chmod +x /usr/local/bin/curl

# Build-time HTTPS smoke. Two phases:
#   (a) clean env — verifies CA chain, network reachability.
#   (b) simulated PyInstaller leak — populate /tmp/_MEI_FAKE with a faux
#       libssl.so.3 that would crash the linker, set LD_LIBRARY_PATH to it,
#       then exercise bare `curl` and bare `python3` (which now go through
#       the wrappers above and must succeed despite the broken
#       LD_LIBRARY_PATH).
RUN set -e \
 && python3 -c "import urllib.request, ssl; \
        req = urllib.request.Request('https://en.wikipedia.org/wiki/Test', headers={'User-Agent': 'kurpatov-wiki-bench-smoke/1.0'}); \
        r = urllib.request.urlopen(req, timeout=10); \
        assert r.status == 200, r.status; \
        print('[smoke 1a] python urllib HTTPS ok (clean env)')" \
 && curl -fsS -A kurpatov-wiki-bench-smoke/1.0 \
        -o /dev/null -w '[smoke 1b] curl HTTPS ok (HTTP %{http_code}, clean env)\n' \
        "https://en.wikipedia.org/wiki/Test" \
 && mkdir -p /tmp/_MEI_FAKE \
 && printf '' > /tmp/_MEI_FAKE/libssl.so.3 \
 && printf '' > /tmp/_MEI_FAKE/libcrypto.so.3 \
 && LD_LIBRARY_PATH=/tmp/_MEI_FAKE python3 -c "import urllib.request; \
        req = urllib.request.Request('https://en.wikipedia.org/wiki/Test', headers={'User-Agent': 'kurpatov-wiki-bench-smoke/1.0'}); \
        r = urllib.request.urlopen(req, timeout=10); \
        assert r.status == 200, r.status; \
        print('[smoke 2a] python urllib HTTPS ok under PyInstaller LD_LIBRARY_PATH leak')" \
 && LD_LIBRARY_PATH=/tmp/_MEI_FAKE curl -fsS -A kurpatov-wiki-bench-smoke/1.0 \
        -o /dev/null -w '[smoke 2b] curl HTTPS ok under PyInstaller LD_LIBRARY_PATH leak (HTTP %{http_code})\n' \
        "https://en.wikipedia.org/wiki/Test" \
 && rm -rf /tmp/_MEI_FAKE


# ─── D8: Python SDK + retrieval deps (added 2026-04-26) ────────────────
#
# Replaces standalone PyInstaller CLI for D7-rev3+ orchestrators.
# numpy used instead of sqlite-vss to avoid libblas3 system pkg.

RUN pip install --no-cache-dir \
        "openhands-sdk==1.17.0" \
        "openhands-tools==1.18.1" \
        "sentence-transformers>=2.7" \
        "numpy>=1.24" \
        "pyyaml>=6.0"

# Pre-download e5-base into image (~280 MB) so HF Hub is not hit on
# every `make bench` invocation (saves ~5 min cold start).
RUN python3 -c "from sentence_transformers import SentenceTransformer; \
    m = SentenceTransformer('intfloat/multilingual-e5-base'); \
    v = m.encode('passage: smoke', normalize_embeddings=True); \
    assert v.shape == (768,), v.shape; \
    print('[smoke 3] sentence-transformers e5-base ok, dim=768')"

# Install our D8 scripts. Run them via `docker run --entrypoint python3
# kurpatov-wiki-bench:V /opt/forge/<script>`.
RUN mkdir -p /opt/forge
COPY orchestrator/run-d8-pilot.py /opt/forge/run-d8-pilot.py
COPY orchestrator/embed_helpers.py /opt/forge/embed_helpers.py
COPY orchestrator/source_coordinator.py /opt/forge/source_coordinator.py
COPY tests/synthetic-orchestrator/step8_smoke.py /opt/forge/step8_smoke.py
COPY tests/synthetic-orchestrator/step7_orchestrator.py /opt/forge/step7_orchestrator.py
COPY evals/grade/bench_grade.py /opt/forge/bench_grade.py

# Build-time D8 retrieval smoke. Pure-Python, no external network beyond
# the e5-base download already cached above.
RUN python3 /opt/forge/step8_smoke.py \
 && echo "[smoke 4] D8 retrieval helpers ok"

# Working directory the agent operates in. The agent will git clone
# kurpatov-wiki-{raw,wiki} into here. /runs/current is the only
# bind-mount back to the host.
WORKDIR /workspace
RUN mkdir -p /runs

ENTRYPOINT ["/usr/local/bin/openhands"]
CMD ["--help"]
