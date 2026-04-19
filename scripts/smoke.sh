#!/usr/bin/env bash
# forge smoke test — end-to-end health check for all services.
#
# SOURCE OF TRUTH: tests/smoke.md
#   This script is a derivation of that model. If you find yourself
#   adding a check here without a matching entry there, stop. Update
#   tests/smoke.md first (goals + signals + edge cases), then come
#   back and mirror the change in this file. See tests/README.md for
#   the full TDD workflow.
#
# What it verifies (each section below corresponds to a section in
# tests/smoke.md with the same name):
#   1. Containers up — all 6 forge containers (caddy, mlflow,
#      jupyter-rl-2048, jupyter-kurpatov-wiki, kurpatov-transcriber,
#      kurpatov-wiki-raw-pusher).
#   2. GPU partitioning — rl-2048 pinned to RL_2048_GPU_UUID,
#      kurpatov-wiki pinned to KURPATOV_WIKI_GPU_UUID, no leakage.
#   3. torch.cuda matmul — both GPU containers can actually run a
#      CUDA kernel.
#   4. Caddy basic auth — unauth=401, auth=200|302 on every public
#      domain.
#   5. mlflow REST API — /experiments/search returns JSON.
#   6. Reactive watchers — transcriber has inotify on
#      /workspace/videos, raw-pusher has inotify on
#      /workspace/vault/raw (see kurpatov-wiki/docs/adr/0005).
#   7. Pusher image discipline — raw-pusher runs a dedicated lean
#      image (no CUDA), not the GPU image (see
#      kurpatov-wiki/docs/adr/0006).
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

# Capture logs first, then grep, to avoid `grep -q` + pipefail SIGPIPE:
# grep -q closes stdin on first match, docker logs exits 141, pipefail
# fails the whole pipe. Capturing sidesteps that cleanly.
check_watcher_log() {
  local label=$1 container=$2 pattern=$3
  local logs
  logs=$(docker logs --since=24h "$container" 2>&1 || true)
  if grep -qE -- "$pattern" <<<"$logs"; then
    pass "$label"
  else
    fail "$label"
  fi
}

check_watcher_log \
  "transcriber has inotify on /workspace/videos" \
  kurpatov-transcriber \
  'inotify on /workspace/videos'

# The raw-pusher watches the raw-transcripts tree; the transcriber writes
# there, and the pusher commits + pushes to the kurpatov-wiki-raw GitHub
# repo. See kurpatov-wiki/docs/adr/0005-split-transcribe-and-push.md.
check_watcher_log \
  "raw-pusher has inotify on /workspace/vault/raw/data" \
  kurpatov-wiki-raw-pusher \
  'inotify on /workspace/vault/raw/data'

# ---------- 7. pusher image discipline ----------
# Rationale: the raw-pusher only needs git + openssh-client + watchdog.
# Riding the ~20 GB forge-kurpatov-wiki:latest GPU image wastes space,
# bloats restart-time logs with the NVIDIA CUDA banner (which in turn
# was what triggered the grep -q + pipefail SIGPIPE false-fail in
# check #6 above), and needlessly expands the container's attack
# surface. See kurpatov-wiki/docs/adr/0006-lean-pusher-image.md.
section "pusher image discipline"

pusher_image=$(docker inspect kurpatov-wiki-raw-pusher \
  --format '{{.Config.Image}}' 2>/dev/null || echo "")
gpu_image=$(docker inspect jupyter-kurpatov-wiki \
  --format '{{.Config.Image}}' 2>/dev/null || echo "")

if [[ -z "$pusher_image" ]]; then
  fail "raw-pusher image lookup: docker inspect returned empty (is the container running?)"
elif [[ -z "$gpu_image" ]]; then
  fail "gpu image lookup: docker inspect on jupyter-kurpatov-wiki returned empty"
elif [[ "$pusher_image" == "$gpu_image" ]]; then
  fail "raw-pusher shares the GPU image (both=$pusher_image); expected a dedicated lean image"
else
  pass "raw-pusher uses a dedicated image (pusher=$pusher_image gpu=$gpu_image)"
fi

# Size check: lean pusher image should be well under 500 MB.
# A python:3.12-slim + git + openssh-client + watchdog build is ~200 MB;
# 500 MB threshold catches an accidental FROM forge-kurpatov-wiki:latest
# regression (that image is ~20 GB) with generous headroom.
MAX_PUSHER_BYTES=$((500 * 1024 * 1024))
if [[ -n "$pusher_image" ]]; then
  pusher_bytes=$(docker image inspect "$pusher_image" \
    --format '{{.Size}}' 2>/dev/null || echo "")
  if [[ -z "$pusher_bytes" || ! "$pusher_bytes" =~ ^[0-9]+$ ]]; then
    fail "raw-pusher image size lookup failed (image=$pusher_image)"
  elif (( pusher_bytes < MAX_PUSHER_BYTES )); then
    pass "raw-pusher image size under 500MB (image=$pusher_image bytes=$pusher_bytes)"
  else
    fail "raw-pusher image too large (image=$pusher_image bytes=$pusher_bytes limit=$MAX_PUSHER_BYTES)"
  fi
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
