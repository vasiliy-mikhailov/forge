#!/bin/bash
# Run e2e tests inside the bench container with real LLM + real Agent.
# Highest fidelity layer per ADR 0010.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(cd "$HERE/../../../../.." && pwd)"
ORCHESTRATOR_DIR="$FORGE_ROOT/phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator"

# Source forge .env for LLM credentials
set -a; source "$FORGE_ROOT/.env"; set +a

# Workspace
WORKSPACE=/tmp/e2e-test-workspace
docker run --rm -v /tmp:/host_tmp ubuntu:24.04 rm -rf /host_tmp/e2e-test-workspace 2>/dev/null || true
mkdir -p "$WORKSPACE"
cp "$HERE/test_verify_source_e2e.py" "$WORKSPACE/test.py"

docker run --rm \
  --network proxy-net \
  --entrypoint python3 \
  -e ORCH_DIR=/opt/forge \
  -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 \
  -e LLM_BASE_URL="${INFERENCE_BASE_URL:-https://inference.mikhailov.tech/v1}" \
  -e LLM_API_KEY="$VLLM_API_KEY" \
  -e LLM_MODEL="openai/qwen3.6-27b-fp8" \
  -v "$WORKSPACE:/workspace" \
  -v "$ORCHESTRATOR_DIR/run-d8-pilot.py:/opt/forge/run-d8-pilot.py" \
  kurpatov-wiki-bench:1.17.0-d8-cal \
  -u /workspace/test.py
