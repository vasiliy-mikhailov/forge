#!/usr/bin/env bash
# forge smoke test — end-to-end health check for all services.
#
# What it verifies:
#   1. All 6 forge containers are Up (caddy, mlflow, jupyter-rl-2048,
#      jupyter-kurpatov-wiki, kurpatov-transcriber, kurpatov-wiki-raw-pusher).
#   2. GPU partitioning: rl-2048 sees the GPU pinned by RL_2048_GPU_UUID,
#      kurpatov-wiki sees the one pinned by KURPATOV_WIKI_GPU_UUID, and
#      they don't leak into each other.
#   3. torch.cuda is available inside both GPU containers and a small
#      matmul runs without error.
#   4. Caddy fronts all three domains correctly:
#        - unauth request -> 401
#        - auth request   -> 200 (mlflow) / 302 (jupyter hosts, to /lab)
#   5. mlflow REST API is reachable with basic auth and returns JSON.
#   6. kurpatov-transcriber has started its inotify watcher on the videos
#      tree, and kurpatov-wiki-raw-pusher has started its inotify watcher
#      on the raw-transcripts tree (see kurpatov-wiki/docs/adr/0005).
#
# Usage:
#   make smoke              # from the forge root (recommended)
#   ./scripts/smoke.sh      # direct
#
# Env: sources ./.env from the forge root. The plaintext basic-auth
# password is taken from MLFLOW_TRACKING_PASSWORD (by convention the
# same secret in this deployment — see caddy/SPEC.md).
#
# Exit code: 0 if all checks pass, 1 otherwise.

set -u
set -o pipefail

# ---------- locate repo root ----------
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
ROOT_DIR=$(cd -- "$SCRIPT_DIR/.." &>/dev/null && pwd)
cd "$ROOT_DIR"

# ---------- load .env ----------
if [[ ! -f .env ]]; then
  echo "ERROR: $ROOT_DIR/.env not found" >&2
  exit 2
fi
set -a; . ./.env; set +a

: "${BASIC_AUTH_USER:?BASIC_AUTH_USER must be set in .env}"
: "${MLFLOW_TRACKING_PASSWORD:?MLFLOW_TRACKING_PASSWORD must be set in .env (used as basic-auth plaintext)}"
: "${MLFLOW_DOMAIN:?MLFLOW_DOMAIN must be set in .env}"
: "${JUPYTER_RL_2048_DOMAIN:?JUPYTER_RL_2048_DOMAIN must be set in .env}"
: "${JUPYTER_KURPATOV_WIKI_DOMAIN:?JUPYTER_KURPATOV_WIKI_DOMAIN must be set in .env}"

USER=$BASIC_AUTH_USER
PASS=$MLFLOW_TRACKING_PASSWORD

EXPECTED_CONTAINERS=(caddy mlflow jupyter-rl-2048 jupyter-kurpatov-wiki kurpatov-transcriber kurpatov-wiki-raw-pusher)

# ---------- pretty output ----------
PASSED=0
FAILED=0
FAILED_NAMES=()

pass() { printf '  [ OK ] %s\n' "$1"; PASSED=$((PASSED+1)); }
fail() { printf '  [FAIL] %s\n' "$1"; FAILED=$((FAILED+1)); FAILED_NAMES+=("$1"); }
section() { printf '\n== %s ==\n' "$1"; }

# ---------- 1. containers ----------
section "containers"
PS_OUT=$(docker ps --format '{{.Names}}\t{{.Status}}')
for c in "${EXPECTED_CONTAINERS[@]}"; do
  if grep -qP "^${c}\t(Up )" <<<"$PS_OUT"; then
    pass "container up: $c"
  else
    fail "container up: $c"
  fi
done

# ---------- 2. GPU partitioning ----------
section "GPU partitioning"

gpu_uuid_in_container() {
  docker exec "$1" nvidia-smi --query-gpu=uuid --format=csv,noheader 2>/dev/null | tr -d '[:space:]'
}

if [[ -n "${RL_2048_GPU_UUID:-}" ]]; then
  got=$(gpu_uuid_in_container jupyter-rl-2048 || true)
  if [[ "$got" == "$(echo -n "$RL_2048_GPU_UUID" | tr -d '[:space:]')" ]]; then
    pass "rl-2048 pinned to RL_2048_GPU_UUID"
  else
    fail "rl-2048 GPU uuid mismatch (got=$got want=$RL_2048_GPU_UUID)"
  fi
else
  fail "RL_2048_GPU_UUID is not set"
fi

if [[ -n "${KURPATOV_WIKI_GPU_UUID:-}" ]]; then
  got=$(gpu_uuid_in_container jupyter-kurpatov-wiki || true)
  if [[ "$got" == "$(echo -n "$KURPATOV_WIKI_GPU_UUID" | tr -d '[:space:]')" ]]; then
    pass "kurpatov-wiki pinned to KURPATOV_WIKI_GPU_UUID"
  else
    fail "kurpatov-wiki GPU uuid mismatch (got=$got want=$KURPATOV_WIKI_GPU_UUID)"
  fi
else
  fail "KURPATOV_WIKI_GPU_UUID is not set"
fi

# ---------- 3. torch.cuda matmul ----------
section "torch.cuda matmul"

TORCH_SNIPPET='
import torch, sys
assert torch.cuda.is_available(), "cuda not available"
a = torch.randn(1024, 1024, device="cuda")
b = torch.randn(1024, 1024, device="cuda")
c = a @ b
torch.cuda.synchronize()
print("OK", torch.__version__, torch.cuda.get_device_name(0), tuple(c.shape))
'
for c in jupyter-rl-2048 jupyter-kurpatov-wiki; do
  if docker exec "$c" python -c "$TORCH_SNIPPET" >/dev/null 2>&1; then
    pass "torch.cuda matmul inside $c"
  else
    fail "torch.cuda matmul inside $c"
  fi
done

# ---------- 4. Caddy basic auth ----------
section "Caddy basic auth (unauth=401, auth=200|302)"

check_http() {
  local label=$1 domain=$2 want_unauth=$3 want_auth=$4
  local unauth auth
  unauth=$(curl -sSo /dev/null -w '%{http_code}' --max-time 8 "https://$domain/" || echo 000)
  auth=$(curl -sSo /dev/null -w '%{http_code}' --max-time 8 -u "$USER:$PASS" "https://$domain/" || echo 000)
  if [[ "$unauth" == "$want_unauth" && "$auth" =~ ^(${want_auth})$ ]]; then
    pass "$label unauth=$unauth auth=$auth"
  else
    fail "$label unauth=$unauth (want $want_unauth)  auth=$auth (want $want_auth)"
  fi
}

check_http "mlflow"         "$MLFLOW_DOMAIN"                "401" "200"
check_http "jupyter-rl-2048" "$JUPYTER_RL_2048_DOMAIN"      "401" "200|302"
check_http "jupyter-kurpatov-wiki" "$JUPYTER_KURPATOV_WIKI_DOMAIN" "401" "200|302"

# ---------- 5. mlflow API ----------
section "mlflow REST API"

api_body=$(curl -sS --max-time 10 -u "$USER:$PASS" \
  "https://$MLFLOW_DOMAIN/api/2.0/mlflow/experiments/search" \
  -H 'Content-Type: application/json' -d '{"max_results":1}' 2>/dev/null || true)
if [[ "$api_body" == *'"experiments"'* ]]; then
  pass "mlflow /experiments/search returns JSON with an experiments list"
else
  fail "mlflow /experiments/search unexpected response: $(printf '%.200s' "$api_body")"
fi

# ---------- 6. watchers (transcriber + raw-pusher) ----------
section "kurpatov watchers"

if docker logs --since=24h kurpatov-transcriber 2>&1 | grep -qE 'inotify on /workspace/videos'; then
  pass "transcriber has inotify on /workspace/videos"
else
  fail "no 'inotify on /workspace/videos' line in last 24h of transcriber logs"
fi

# The raw-pusher watches the raw-transcripts tree; the transcriber writes
# there, and the pusher commits + pushes to the kurpatov-wiki-raw GitHub
# repo. See kurpatov-wiki/docs/adr/0005-split-transcribe-and-push.md.
if docker logs --since=24h kurpatov-wiki-raw-pusher 2>&1 | grep -qE 'inotify on /workspace/vault/raw'; then
  pass "raw-pusher has inotify on /workspace/vault/raw"
else
  fail "no 'inotify on /workspace/vault/raw' line in last 24h of raw-pusher logs"
fi

# ---------- summary ----------
TOTAL=$((PASSED + FAILED))
printf '\n== summary ==\n  passed: %d/%d\n' "$PASSED" "$TOTAL"
if (( FAILED > 0 )); then
  printf '  failed:\n'
  for name in "${FAILED_NAMES[@]}"; do
    printf '    - %s\n' "$name"
  done
  exit 1
fi
printf '  all checks passed.\n'
exit 0
