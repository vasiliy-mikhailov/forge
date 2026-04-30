#!/bin/bash
# Run coordinator e2e tests inside the bench image with real vLLM.
# Per ADR 0010 + ADR 0013 + ADR 0012-phase-g.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(cd "$HERE/../../../../.." && pwd)"
WIKI_BENCH_DIR="$FORGE_ROOT/phase-c-information-systems-architecture/application-architecture/wiki-bench"

set -a; source "$FORGE_ROOT/.env"; set +a

WORKSPACE=/tmp/coord-e2e-workspace
RAW_INPUT=/tmp/k1-v2-pilot/raw          # bind-mounted raw repo for fixture
if [ ! -d "$RAW_INPUT" ]; then
    echo "ABORT: $RAW_INPUT (raw repo) not present; run a K1 pilot's setup_workspace first or adjust this path"
    exit 2
fi

echo "=== rebuilding bench image (ADR 0012-phase-g) ==="
( cd "$WIKI_BENCH_DIR" && docker build -t kurpatov-wiki-bench:1.17.0-d8-cal . > /tmp/bench-build.log 2>&1 \
  && tail -3 /tmp/bench-build.log )

echo "=== preparing workspace ==="
docker run --rm -v /tmp:/host_tmp ubuntu:24.04 \
  rm -rf /host_tmp/coord-e2e-workspace 2>/dev/null || true
mkdir -p "$WORKSPACE"
cp "$HERE/test_source_coordinator_e2e.py" "$WORKSPACE/test.py"

echo "=== running e2e tests inside container with real vLLM ==="
docker run --rm \
  --network proxy-net \
  --entrypoint python3 \
  -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 \
  -e LLM_BASE_URL="${INFERENCE_BASE_URL:-https://inference.mikhailov.tech/v1}" \
  -e LLM_API_KEY="$VLLM_API_KEY" \
  -e LLM_MODEL="openai/qwen3.6-27b-fp8" \
  -v "$WORKSPACE:/workspace" \
  -v "$RAW_INPUT:/raw_input:ro" \
  kurpatov-wiki-bench:1.17.0-d8-cal \
  -u /workspace/test.py
