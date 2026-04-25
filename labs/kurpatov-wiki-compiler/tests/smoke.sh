#!/usr/bin/env bash
# Smoke for kurpatov-wiki-compiler lab.
#
# Source of truth: smoke.md (this dir).
#
# What this verifies:
#   1. Containers up (vllm-inference healthy, kurpatov-wiki-compiler-caddy up).
#   2. GPU pinned to INFERENCE_GPU_UUID.
#   3. Active model registry consistency: forge/.env's
#      INFERENCE_ACTIVE_MODEL_ID exists in configs/models.yml; the
#      .env.active-model on disk matches what the registry says for
#      that id (no manual drift).
#   4. Compiler endpoint live: GET https://$INFERENCE_DOMAIN/v1/models
#      returns the served_name expected by the active registry entry.

set -u
set -o pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
LAB_DIR=$(cd -- "$HERE/.." &>/dev/null && pwd)
FORGE_ROOT=$(git -C "$HERE" rev-parse --show-toplevel)

if [[ ! -f "$FORGE_ROOT/.env" ]]; then
  echo "ERROR: $FORGE_ROOT/.env not found" >&2
  exit 2
fi
set -a; . "$FORGE_ROOT/.env"; set +a

. "$FORGE_ROOT/scripts/smoke-lib.sh"

require_env INFERENCE_DOMAIN VLLM_API_KEY INFERENCE_ACTIVE_MODEL_ID INFERENCE_GPU_UUID

# ---------- 1. containers ----------
section "containers"
check_container_up vllm-inference --healthy
check_container_up kurpatov-wiki-compiler-caddy

# ---------- 2. GPU partitioning ----------
section "GPU partitioning"
check_gpu_pinned vllm-inference "$INFERENCE_GPU_UUID"

# ---------- 3. active model registry consistency ----------
section "model registry consistency"

REGISTRY="$LAB_DIR/configs/models.yml"
ACTIVE_ENV="$LAB_DIR/.env.active-model"

if [[ ! -f "$REGISTRY" ]]; then
  fail "registry missing at $REGISTRY"
else
  pass "registry present at $REGISTRY"
fi

# Active id resolves in registry?
expected_served=$(python3 - "$REGISTRY" "$INFERENCE_ACTIVE_MODEL_ID" <<'PY' 2>/dev/null || true
import sys, yaml
try:
    data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
    m = next((x for x in data["models"] if x["id"] == sys.argv[2]), None)
    print(m["served_name"] if m else "")
except Exception:
    print("")
PY
)
if [[ -n "$expected_served" ]]; then
  pass "INFERENCE_ACTIVE_MODEL_ID=$INFERENCE_ACTIVE_MODEL_ID resolves in registry (served_name=$expected_served)"
else
  fail "INFERENCE_ACTIVE_MODEL_ID=$INFERENCE_ACTIVE_MODEL_ID not found in $REGISTRY"
  expected_served=""
fi

# .env.active-model exists and matches what render would produce now?
if [[ ! -f "$ACTIVE_ENV" ]]; then
  fail ".env.active-model missing — was 'make compiler-up' chained through load-active-model.sh?"
else
  rendered_id=$(grep -E '^MODEL_ID=' "$ACTIVE_ENV" | cut -d= -f2-)
  if [[ "$rendered_id" == "$INFERENCE_ACTIVE_MODEL_ID" ]]; then
    pass ".env.active-model MODEL_ID matches active selector ($rendered_id)"
  else
    fail ".env.active-model has MODEL_ID=$rendered_id but selector is $INFERENCE_ACTIVE_MODEL_ID — re-run load-active-model.sh"
  fi
fi

# Re-render to /tmp and diff against .env.active-model — drift check.
if [[ -f "$REGISTRY" && -f "$ACTIVE_ENV" ]]; then
  fresh=$(mktemp)
  if INFERENCE_ACTIVE_MODEL_ID="$INFERENCE_ACTIVE_MODEL_ID" \
     bash "$LAB_DIR/bin/load-active-model.sh" >/dev/null 2>"$fresh.err"; then
    if diff -q "$ACTIVE_ENV" "$ACTIVE_ENV" >/dev/null 2>&1 \
       && diff -q "$ACTIVE_ENV" "$LAB_DIR/.env.active-model" >/dev/null 2>&1; then
      pass ".env.active-model is byte-stable against current registry"
    else
      fail ".env.active-model has drifted from registry — re-run load-active-model.sh"
    fi
  fi
  rm -f "$fresh" "$fresh.err"
fi

# ---------- 4. inference endpoint live ----------
section "inference endpoint"

models_json=$(curl -fsS \
  -H "Authorization: Bearer ${VLLM_API_KEY}" \
  "https://${INFERENCE_DOMAIN}/v1/models" 2>/dev/null || echo "")

if [[ -z "$models_json" ]]; then
  fail "GET https://${INFERENCE_DOMAIN}/v1/models did not return 2xx"
elif [[ -z "$expected_served" ]]; then
  skip "served_name expected from registry was empty (active id not resolvable)"
elif python3 -c "
import sys, json
d = json.loads(sys.argv[1])
ids = [m.get('id') for m in d.get('data', [])]
sys.exit(0 if '${expected_served}' in ids else 1)
" "$models_json" 2>/dev/null; then
  pass "vLLM serves '${expected_served}' (matches registry expectation)"
else
  actual=$(python3 -c "
import sys, json
d = json.loads(sys.argv[1])
print(','.join(m.get('id', '?') for m in d.get('data', [])) or '<empty>')
" "$models_json" 2>/dev/null || echo "<unparseable>")
  fail "expected '${expected_served}' missing from /v1/models (got: $actual). Drift: registry vs running vLLM"
fi

summary_and_exit
