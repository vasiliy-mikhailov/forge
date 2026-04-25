#!/usr/bin/env bash
# Shared smoke-test helpers for per-lab smokes and the root dispatcher.
#
# Usage: source from a per-lab smoke.sh:
#
#   . "$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)/scripts/smoke-lib.sh"
#
# Provides:
#   pass / fail / skip / section / summary_and_exit
#   check_container_up <name>
#   check_container_image_size_below <name> <max_bytes>
#   check_container_image_differs_from <a> <b>
#   check_gpu_pinned <container> <expected_uuid>
#   check_torch_cuda_matmul <container>
#   check_http_basic_auth <label> <domain> <user> <pass> <want_unauth> <want_auth_regex>
#   check_logs_contains <label> <container> <pattern>
#   require_env <var>...

# Pretty-print state. Each per-lab smoke.sh tracks its own counters; we
# just append.
PASSED=${PASSED:-0}
FAILED=${FAILED:-0}
FAILED_NAMES=${FAILED_NAMES:-}

pass()    { printf '  [ OK ] %s\n' "$1"; PASSED=$((PASSED + 1)); }
fail()    { printf '  [FAIL] %s\n' "$1"; FAILED=$((FAILED + 1)); FAILED_NAMES="${FAILED_NAMES}${FAILED_NAMES:+|}$1"; }
skip()    { printf '  [SKIP] %s\n' "$1"; }
section() { printf '\n== %s ==\n' "$1"; }

require_env() {
  local var
  for var in "$@"; do
    if [[ -z "${!var:-}" ]]; then
      echo "ERROR: $var must be set in .env" >&2
      exit 2
    fi
  done
}

# --- Containers ---

check_container_up() {
  # check_container_up <name> [--healthy]
  local name=$1 want_healthy=${2:-}
  local ps_line status
  ps_line=$(docker ps --format '{{.Names}}\t{{.Status}}' | grep -P "^${name}\t" || true)
  if [[ -z "$ps_line" ]]; then
    fail "container up: $name"
    return 1
  fi
  status=${ps_line#*$'\t'}
  if [[ "$status" != Up* ]]; then
    fail "container up: $name (status=$status)"
    return 1
  fi
  if [[ "$want_healthy" == "--healthy" && "$status" != *"(healthy)"* ]]; then
    fail "container healthy: $name (status=$status)"
    return 1
  fi
  pass "container up: $name${want_healthy:+ (healthy)}"
}

check_container_image_differs_from() {
  # check_container_image_differs_from <label> <container_a> <container_b>
  local label=$1 a=$2 b=$3
  local img_a img_b
  img_a=$(docker inspect "$a" --format '{{.Config.Image}}' 2>/dev/null || true)
  img_b=$(docker inspect "$b" --format '{{.Config.Image}}' 2>/dev/null || true)
  if [[ -z "$img_a" || -z "$img_b" ]]; then
    fail "$label (could not inspect: a=$a -> '$img_a', b=$b -> '$img_b')"
    return 1
  fi
  if [[ "$img_a" == "$img_b" ]]; then
    fail "$label (both run $img_a)"
    return 1
  fi
  pass "$label ($a=$img_a; $b=$img_b)"
}

check_container_image_size_below() {
  # check_container_image_size_below <label> <container> <max_bytes>
  local label=$1 container=$2 max=$3
  local img bytes
  img=$(docker inspect "$container" --format '{{.Config.Image}}' 2>/dev/null || true)
  if [[ -z "$img" ]]; then
    fail "$label (no image for $container)"
    return 1
  fi
  bytes=$(docker image inspect "$img" --format '{{.Size}}' 2>/dev/null || true)
  if [[ -z "$bytes" || ! "$bytes" =~ ^[0-9]+$ ]]; then
    fail "$label (image size lookup failed for $img)"
    return 1
  fi
  if (( bytes < max )); then
    pass "$label ($img: $bytes bytes < $max)"
  else
    fail "$label ($img: $bytes bytes >= $max)"
  fi
}

# --- GPU ---

check_gpu_pinned() {
  # check_gpu_pinned <container> <expected_uuid>
  local container=$1 expected=$2
  local got
  got=$(docker exec "$container" nvidia-smi --query-gpu=uuid --format=csv,noheader 2>/dev/null | tr -d '[:space:]' || true)
  expected=$(echo -n "$expected" | tr -d '[:space:]')
  if [[ "$got" == "$expected" ]]; then
    pass "$container pinned to expected GPU"
  else
    fail "$container GPU mismatch (got=$got want=$expected)"
  fi
}

check_torch_cuda_matmul() {
  # check_torch_cuda_matmul <container>
  local container=$1
  local snippet='
import torch, sys
assert torch.cuda.is_available(), "cuda not available"
a = torch.randn(1024, 1024, device="cuda")
b = torch.randn(1024, 1024, device="cuda")
c = a @ b
torch.cuda.synchronize()
'
  if docker exec "$container" python -c "$snippet" >/dev/null 2>&1; then
    pass "torch.cuda matmul inside $container"
  else
    fail "torch.cuda matmul inside $container"
  fi
}

# --- HTTP / caddy ---

check_http_basic_auth() {
  # check_http_basic_auth <label> <domain> <user> <pass> <want_unauth> <want_auth_regex>
  # auth-codes can be "200" or "200|302" etc.
  local label=$1 domain=$2 user=$3 pass=$4 want_unauth=$5 want_auth=$6
  local unauth auth
  unauth=$(curl -sSo /dev/null -w '%{http_code}' --max-time 8 "https://$domain/" 2>/dev/null || echo 000)
  auth=$(curl -sSo /dev/null -w '%{http_code}' --max-time 8 -u "$user:$pass" "https://$domain/" 2>/dev/null || echo 000)
  if [[ "$unauth" == "$want_unauth" && "$auth" =~ ^(${want_auth})$ ]]; then
    pass "$label unauth=$unauth auth=$auth"
  else
    fail "$label unauth=$unauth (want $want_unauth) auth=$auth (want $want_auth)"
  fi
}

# --- Logs ---

check_logs_contains() {
  # check_logs_contains <label> <container> <pattern>
  # Capture-then-grep discipline: avoid `docker logs | grep -q` under
  # `set -o pipefail`, which can SIGPIPE-fail when logs are large.
  local label=$1 container=$2 pattern=$3
  local logs
  logs=$(docker logs --since=24h "$container" 2>&1 || true)
  if grep -qE -- "$pattern" <<<"$logs"; then
    pass "$label"
  else
    fail "$label (pattern '$pattern' not found in last 24h of $container logs)"
  fi
}

# --- Final summary ---

summary_and_exit() {
  local total=$((PASSED + FAILED))
  printf '\n== summary ==\n  passed: %d/%d\n' "$PASSED" "$total"
  if (( FAILED > 0 )); then
    printf '  failed:\n'
    local IFS='|'
    for name in $FAILED_NAMES; do
      printf '    - %s\n' "$name"
    done
    exit 1
  fi
  printf '  all checks passed.\n'
  exit 0
}
