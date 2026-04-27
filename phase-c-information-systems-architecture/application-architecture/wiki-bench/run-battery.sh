#!/usr/bin/env bash
# wiki-bench/run-battery.sh — bench-as-battery driver.
#
# After ADR 0008, this script changes the *active model selector*
# (forge/.env: INFERENCE_ACTIVE_MODEL_ID) and lets the compiler lab
# render the rest from its own registry. Battery never patches model
# parameters directly.
#
# Usage:
#   ./run-battery.sh                # iterate every entry where bench_skip != true
#   ./run-battery.sh <id>           # single id (skip-flag ignored)
#   ./run-battery.sh --tier A       # all bench_tier == A, skip-flag ignored
#
# For each picked entry:
#   1. patch forge/.env: INFERENCE_ACTIVE_MODEL_ID=<id>
#   2. make -C phase-c-information-systems-architecture/application-architecture/wiki-compiler down ; make -C phase-c-information-systems-architecture/application-architecture/wiki-compiler up
#   3. wait for vLLM healthy (poll /v1/models until served_name appears)
#   4. ./run.sh
#   5. continue on failure; restore the original active id at the end.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
REGISTRY="$FORGE_ROOT/labs/wiki-compiler/configs/models.yml"

[[ -f "$REGISTRY" ]] || { echo "FATAL: registry not found at $REGISTRY" >&2; exit 2; }
[[ -f "$FORGE_ROOT/.env" ]] || { echo "FATAL: $FORGE_ROOT/.env not found" >&2; exit 2; }

# --- arg parsing ---
mode="all"
arg_id=""
arg_tier=""
case "${1:-}" in
  --tier)
    mode="tier"; arg_tier="${2:-}"; shift 2 || true
    [[ -n "$arg_tier" ]] || { echo "usage: $0 --tier <A|B|C|D>" >&2; exit 2; }
    ;;
  -h|--help)
    sed -n '2,16p' "$0"; exit 0
    ;;
  "")
    mode="all"
    ;;
  *)
    mode="single"; arg_id="$1"
    ;;
esac

# --- pick ids from registry ---
mapfile -t ids < <(python3 - "$REGISTRY" "$mode" "$arg_id" "$arg_tier" <<'PY'
import sys, yaml
registry, mode, arg_id, arg_tier = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
data = yaml.safe_load(open(registry, encoding="utf-8"))
for m in data.get("models", []):
    if mode == "single":
        if m["id"] == arg_id:
            print(m["id"])
    elif mode == "tier":
        if m.get("bench_tier") == arg_tier:
            print(m["id"])
    else:  # all
        if not m.get("bench_skip", False):
            print(m["id"])
PY
)

if [[ ${#ids[@]} -eq 0 ]]; then
  case "$mode" in
    single) echo "FATAL: model id '$arg_id' not in registry" >&2 ;;
    tier)   echo "FATAL: no models with bench_tier=$arg_tier in registry" >&2 ;;
    all)    echo "FATAL: no non-skipped models in registry" >&2 ;;
  esac
  exit 2
fi

# --- preserve original active id ---
orig_active=$(grep -E '^INFERENCE_ACTIVE_MODEL_ID=' "$FORGE_ROOT/.env" | head -1 | cut -d= -f2- || echo "")

# --- per-model runtime knobs from forge/.env ---
set -a; source "$FORGE_ROOT/.env"; set +a

: "${STORAGE_ROOT:?must be set}"
: "${INFERENCE_BASE_URL:?must be set}"
: "${VLLM_API_KEY:?must be set}"

ts=$(date +"%Y-%m-%d-%H%M%S")
log_dir="${STORAGE_ROOT}/labs/wiki-bench/battery-runs"
mkdir -p "$log_dir"
battery_log="${log_dir}/${ts}.log"

echo "[battery] start ${ts}" | tee "$battery_log"
echo "[battery] log: $battery_log" | tee -a "$battery_log"
echo "[battery] ${#ids[@]} model(s) to run: ${ids[*]}" | tee -a "$battery_log"

set_active_id() {
  local id=$1
  if grep -qE '^INFERENCE_ACTIVE_MODEL_ID=' "$FORGE_ROOT/.env"; then
    sed -i.bak -E "s|^INFERENCE_ACTIVE_MODEL_ID=.*|INFERENCE_ACTIVE_MODEL_ID=${id}|" "$FORGE_ROOT/.env"
  else
    echo "INFERENCE_ACTIVE_MODEL_ID=${id}" >> "$FORGE_ROOT/.env"
  fi
  rm -f "$FORGE_ROOT/.env.bak"
}

served_name_for() {
  python3 - "$REGISTRY" "$1" <<'PY'
import sys, yaml
data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
m = next((x for x in data["models"] if x["id"] == sys.argv[2]), None)
print(m["served_name"] if m else "")
PY
}

wait_for_served() {
  local want=$1
  local deadline=$(($(date +%s) + 1200))   # 20 min
  while (( $(date +%s) < deadline )); do
    served=$(curl -fsS "${INFERENCE_BASE_URL}/models" \
      -H "Authorization: Bearer ${VLLM_API_KEY}" 2>/dev/null \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data') or [{}])[0].get('id',''))" 2>/dev/null \
      || echo "")
    if [[ "$served" == "$want" ]]; then
      return 0
    fi
    sleep 10
  done
  return 1
}

i=0
ok=()
fail=()
for id in "${ids[@]}"; do
  i=$((i+1))
  echo "" | tee -a "$battery_log"
  echo "================================================================" | tee -a "$battery_log"
  echo "[battery] [${i}/${#ids[@]}] model: $id" | tee -a "$battery_log"
  echo "================================================================" | tee -a "$battery_log"
  expected=$(served_name_for "$id")
  echo "[battery]   expected served_name=$expected" | tee -a "$battery_log"

  set_active_id "$id"

  echo "[battery]   make kurpatov-wiki-compiler-down" | tee -a "$battery_log"
  ( cd "$FORGE_ROOT" && make kurpatov-wiki-compiler-down ) >> "$battery_log" 2>&1 || true
  sleep 2

  echo "[battery]   make wiki-compiler" | tee -a "$battery_log"
  ( cd "$FORGE_ROOT" && make wiki-compiler ) >> "$battery_log" 2>&1 || true

  echo "[battery]   waiting for vLLM healthy ..." | tee -a "$battery_log"
  t0=$(date +%s)
  if wait_for_served "$expected"; then
    elapsed=$(( $(date +%s) - t0 ))
    echo "[battery]   healthy after ${elapsed} seconds" | tee -a "$battery_log"
  else
    echo "[battery]   ✗ vLLM did not serve '$expected' within 20m; skipping run.sh" | tee -a "$battery_log"
    fail+=("$id (compiler-not-healthy)")
    continue
  fi

  echo "[battery]   ./run.sh" | tee -a "$battery_log"
  set +e
  ( cd "$HERE" && ./run.sh ) >> "$battery_log" 2>&1
  exp_rc=$?
  set -e
  if (( exp_rc == 0 )); then
    echo "[battery]   ✓ experiment $id finished (exit=0)" | tee -a "$battery_log"
    ok+=("$id")
  else
    echo "[battery]   ✗ experiment $id failed (exit=$exp_rc); continuing battery" | tee -a "$battery_log"
    fail+=("$id (run.sh exit=$exp_rc)")
  fi
done

# Restore original selector if any
if [[ -n "$orig_active" && "$orig_active" != "${ids[-1]}" ]]; then
  echo "" | tee -a "$battery_log"
  echo "[battery] restoring original INFERENCE_ACTIVE_MODEL_ID=$orig_active" | tee -a "$battery_log"
  set_active_id "$orig_active"
fi

echo "" | tee -a "$battery_log"
echo "================================================================" | tee -a "$battery_log"
echo "[battery] done. ok=${#ok[@]}/${#ids[@]} fail=${#fail[@]}" | tee -a "$battery_log"
[[ ${#ok[@]} -gt 0 ]] && printf '[battery]   ok:   %s\n' "${ok[@]}" | tee -a "$battery_log"
[[ ${#fail[@]} -gt 0 ]] && printf '[battery]   fail: %s\n' "${fail[@]}" | tee -a "$battery_log"
echo "[battery] log: $battery_log" | tee -a "$battery_log"
echo "[battery] per-experiment artifacts: ${STORAGE_ROOT}/labs/wiki-bench/experiments/" | tee -a "$battery_log"
echo "================================================================" | tee -a "$battery_log"
