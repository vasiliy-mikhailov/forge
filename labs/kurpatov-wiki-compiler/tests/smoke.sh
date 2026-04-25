#!/usr/bin/env bash
# Smoke for kurpatov-wiki-compiler lab.
#
# Source of truth: smoke.md (this dir).
#
# What this verifies:
#   1. Containers up (vllm-inference healthy, kurpatov-wiki-compiler-caddy up).
#   2. GPU pinned to INFERENCE_GPU_UUID.
#   3. Compiler endpoint live behind caddy:
#      GET https://$INFERENCE_DOMAIN/v1/models returns the
#      $INFERENCE_SERVED_NAME registered with vLLM.

set -u
set -o pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
FORGE_ROOT=$(git -C "$HERE" rev-parse --show-toplevel)

# Load forge/.env (single source of truth).
if [[ ! -f "$FORGE_ROOT/.env" ]]; then
  echo "ERROR: $FORGE_ROOT/.env not found" >&2
  exit 2
fi
set -a; . "$FORGE_ROOT/.env"; set +a

. "$FORGE_ROOT/scripts/smoke-lib.sh"

require_env INFERENCE_DOMAIN VLLM_API_KEY INFERENCE_SERVED_NAME INFERENCE_GPU_UUID

# ---------- 1. containers ----------
section "containers"
check_container_up vllm-inference --healthy
check_container_up kurpatov-wiki-compiler-caddy

# ---------- 2. GPU partitioning ----------
section "GPU partitioning"
check_gpu_pinned vllm-inference "$INFERENCE_GPU_UUID"

# ---------- 3. inference endpoint live ----------
section "inference endpoint"

models_json=$(curl -fsS \
  -H "Authorization: Bearer ${VLLM_API_KEY}" \
  "https://${INFERENCE_DOMAIN}/v1/models" 2>/dev/null || echo "")

if [[ -z "$models_json" ]]; then
  fail "GET https://${INFERENCE_DOMAIN}/v1/models did not return 2xx"
elif python3 -c "
import sys, json
d = json.loads(sys.argv[1])
ids = [m.get('id') for m in d.get('data', [])]
sys.exit(0 if '${INFERENCE_SERVED_NAME}' in ids else 1)
" "$models_json" 2>/dev/null; then
  pass "vLLM serves '${INFERENCE_SERVED_NAME}' on https://${INFERENCE_DOMAIN}/v1/models"
else
  actual=$(python3 -c "
import sys, json
d = json.loads(sys.argv[1])
print(','.join(m.get('id', '?') for m in d.get('data', [])) or '<empty>')
" "$models_json" 2>/dev/null || echo "<unparseable>")
  fail "expected '${INFERENCE_SERVED_NAME}' missing from /v1/models (got: $actual)"
fi

summary_and_exit
