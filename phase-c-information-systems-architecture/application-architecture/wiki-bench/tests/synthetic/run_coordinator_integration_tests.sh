#!/bin/bash
# Run coordinator integration tests inside the bench image.
# Per ADR 0010 (test fidelity) + ADR 0013 (Python coordinator) + ADR
# 0012-phase-g (rebuild image first).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(cd "$HERE/../../../../.." && pwd)"
WIKI_BENCH_DIR="$FORGE_ROOT/phase-c-information-systems-architecture/application-architecture/wiki-bench"

WORKSPACE=/tmp/coord-int-workspace

echo "=== rebuilding bench image (ADR 0012-phase-g) ==="
( cd "$WIKI_BENCH_DIR" && docker build -t kurpatov-wiki-bench:1.17.0-d8-cal . > /tmp/bench-build.log 2>&1 \
  && tail -3 /tmp/bench-build.log )

echo "=== preparing workspace ==="
docker run --rm -v /tmp:/host_tmp ubuntu:24.04 \
  rm -rf /host_tmp/coord-int-workspace 2>/dev/null || true
mkdir -p "$WORKSPACE"
cp "$HERE/test_source_coordinator_integration.py" "$WORKSPACE/test.py"

echo "=== running integration tests inside container ==="
docker run --rm \
  --entrypoint python3 \
  -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 \
  -v "$WORKSPACE:/workspace" \
  kurpatov-wiki-bench:1.17.0-d8-cal \
  -u /workspace/test.py
