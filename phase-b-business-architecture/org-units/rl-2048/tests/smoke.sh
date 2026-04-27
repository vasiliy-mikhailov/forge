#!/usr/bin/env bash
# Smoke for rl-2048 lab.
#
# Source of truth: smoke.md (this dir).
#
# What this verifies:
#   1. Containers up: jupyter-rl-2048, mlflow, rl-2048-caddy.
#   2. GPU pinned to RL_2048_GPU_UUID.
#   3. torch.cuda matmul inside jupyter-rl-2048.
#   4. Caddy basic auth on $MLFLOW_DOMAIN and $JUPYTER_RL_2048_DOMAIN.
#   5. mlflow REST API: /experiments/search returns JSON.

set -u
set -o pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
FORGE_ROOT=$(git -C "$HERE" rev-parse --show-toplevel)

if [[ ! -f "$FORGE_ROOT/.env" ]]; then
  echo "ERROR: $FORGE_ROOT/.env not found" >&2
  exit 2
fi
set -a; . "$FORGE_ROOT/.env"; set +a

. "$FORGE_ROOT/scripts/smoke-lib.sh"

require_env BASIC_AUTH_USER MLFLOW_TRACKING_PASSWORD \
            MLFLOW_DOMAIN JUPYTER_RL_2048_DOMAIN \
            RL_2048_GPU_UUID

# ---------- 1. containers ----------
section "containers"
for c in jupyter-rl-2048 mlflow rl-2048-caddy; do
  check_container_up "$c"
done

# ---------- 2. GPU partitioning ----------
section "GPU partitioning"
check_gpu_pinned jupyter-rl-2048 "$RL_2048_GPU_UUID"

# ---------- 3. torch.cuda matmul ----------
section "torch.cuda matmul"
check_torch_cuda_matmul jupyter-rl-2048

# ---------- 4. Caddy basic auth ----------
section "Caddy basic auth (unauth=401, auth=200|302)"
check_http_basic_auth \
  mlflow \
  "$MLFLOW_DOMAIN" \
  "$BASIC_AUTH_USER" "$MLFLOW_TRACKING_PASSWORD" \
  "401" "200"
check_http_basic_auth \
  jupyter-rl-2048 \
  "$JUPYTER_RL_2048_DOMAIN" \
  "$BASIC_AUTH_USER" "$MLFLOW_TRACKING_PASSWORD" \
  "401" "200|302"

# ---------- 5. mlflow REST API ----------
section "mlflow REST API"
api_body=$(curl -sS --max-time 10 \
  -u "$BASIC_AUTH_USER:$MLFLOW_TRACKING_PASSWORD" \
  "https://$MLFLOW_DOMAIN/api/2.0/mlflow/experiments/search" \
  -H 'Content-Type: application/json' \
  -d '{"max_results":1}' 2>/dev/null || true)

if [[ "$api_body" == *'"experiments"'* ]]; then
  pass "mlflow /experiments/search returns JSON with an experiments list"
else
  fail "mlflow /experiments/search unexpected response: $(printf '%.200s' "$api_body")"
fi

summary_and_exit
