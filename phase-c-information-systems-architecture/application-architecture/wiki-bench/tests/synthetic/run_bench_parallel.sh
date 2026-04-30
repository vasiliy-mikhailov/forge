#!/bin/bash
# Parallelism sweep — reuses the K1 v2 raw repo for fixture data.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(cd "$HERE/../../../../.." && pwd)"
WIKI_BENCH_DIR="$FORGE_ROOT/phase-c-information-systems-architecture/application-architecture/wiki-bench"

set -a; source "$FORGE_ROOT/.env"; set +a

WORKSPACE=/tmp/bench-par-workspace

echo "=== rebuilding bench image ==="
( cd "$WIKI_BENCH_DIR" && docker build -t kurpatov-wiki-bench:1.17.0-d8-cal . > /tmp/bench-build.log 2>&1 \
  && tail -3 /tmp/bench-build.log )

echo "=== preparing workspace ==="
docker run --rm -v /tmp:/host_tmp ubuntu:24.04 \
  rm -rf /host_tmp/bench-par-workspace 2>/dev/null || true
mkdir -p "$WORKSPACE"
cp "$HERE/bench_parallel.py" "$WORKSPACE/bench.py"

echo "=== running benchmark inside container ==="
docker run --rm \
  --network proxy-net \
  --entrypoint python3 \
  -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 \
  -e LLM_BASE_URL="${INFERENCE_BASE_URL:-https://inference.mikhailov.tech/v1}" \
  -e LLM_API_KEY="$VLLM_API_KEY" \
  -e LLM_MODEL="openai/qwen3.6-27b-fp8" \
  -v "$WORKSPACE:/workspace" \
  -v "/tmp/k1-v2-pilot/raw:/raw_input:ro" \
  kurpatov-wiki-bench:1.17.0-d8-cal \
  -u /workspace/bench.py
