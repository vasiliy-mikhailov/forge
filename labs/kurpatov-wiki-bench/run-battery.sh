#!/usr/bin/env bash
# kurpatov-wiki-bench/run-battery.sh — iterate the configs/models.yml
# roster and run one experiment per model.
#
# Usage:
#   ./run-battery.sh                  — run all non-skip models
#   ./run-battery.sh qwen3.6-27b-fp8  — run a specific model by id
#
# Per model: stop compiler, swap forge/.env (INFERENCE_MODEL,
# INFERENCE_SERVED_NAME, INFERENCE_MAX_MODEL_LEN), bring compiler
# back up, wait healthy, run one ./run.sh experiment.
#
# NOTE — first iteration: per-model quant / tool-call-parser /
# reasoning-parser flags in models.yml are NOT yet rendered into
# labs/kurpatov-wiki-compiler/docker-compose.yml; the operator must
# either pre-edit the compose for parser-compatibility across the
# battery roster, or extend this script to template them. Lift to a
# follow-up commit once we see whether all-Qwen runs work with the
# qwen3_xml/qwen3 parser pair without per-row tweaks.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

FORGE_ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
ENV_FILE="$FORGE_ROOT/.env"
MODELS_YML="$HERE/configs/models.yml"

[[ -f "$ENV_FILE" ]] || { echo "FATAL: $ENV_FILE not found" >&2; exit 2; }
[[ -f "$MODELS_YML" ]] || { echo "FATAL: $MODELS_YML not found" >&2; exit 2; }
python3 -c 'import yaml' 2>/dev/null || { echo "FATAL: PyYAML not installed" >&2; exit 2; }

set -a; source "$ENV_FILE"; set +a
: "${STORAGE_ROOT:?must be set in forge/.env}"

BATTERY_TS=$(date +"%Y-%m-%d-%H%M%S")
BATTERY_LOG_DIR="$STORAGE_ROOT/labs/kurpatov-wiki-bench/battery-runs"
mkdir -p "$BATTERY_LOG_DIR"
BATTERY_LOG="$BATTERY_LOG_DIR/$BATTERY_TS.log"
exec > >(tee -a "$BATTERY_LOG") 2>&1
echo "[battery] start $BATTERY_TS"
echo "[battery] log: $BATTERY_LOG"

# Resolve model id list. If $1 given, run only that one (even if skip:true).
filter_id="${1:-}"
mapfile -t ids < <(python3 - <<PY "$MODELS_YML" "$filter_id"
import sys, yaml
path, filt = sys.argv[1], sys.argv[2]
with open(path) as f: data = yaml.safe_load(f)
for m in data.get('models', []):
    if filt:
        if m.get('id') == filt: print(m['id'])
    else:
        if not m.get('skip', False): print(m['id'])
PY
)
total=${#ids[@]}
if [[ $total -eq 0 ]]; then
  echo "FATAL: no models matched (filter='$filter_id')" >&2
  exit 3
fi
echo "[battery] $total model(s) to run: ${ids[*]}"

# Helper: extract a field for a model id.
field() {
  local id="$1" field="$2" default="$3"
  python3 - <<PY "$MODELS_YML" "$id" "$field" "$default"
import sys, yaml
path, mid, fld, default = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
with open(path) as f: data = yaml.safe_load(f)
for m in data.get('models', []):
    if m.get('id') == mid:
        v = m.get(fld, default)
        if v is None: v = default
        print(v)
        sys.exit(0)
print(default)
PY
}

i=0
for id in "${ids[@]}"; do
  i=$((i+1))
  echo
  echo "================================================================"
  echo "[battery] [$i/$total] model: $id"
  echo "================================================================"

  hf=$(field "$id" hf "")
  served_name=$(field "$id" served_name "$id")
  max_len=$(field "$id" max_model_len 65536)

  echo "[battery]   hf=$hf"
  echo "[battery]   served_name=$served_name  max_len=$max_len"

  if [[ -z "$hf" ]]; then
    echo "[battery]   skip (no hf field — likely a baseline reference entry)"
    continue
  fi

  # Patch forge/.env
  sed -i "s|^INFERENCE_MODEL=.*|INFERENCE_MODEL=$hf|" "$ENV_FILE"
  sed -i "s|^INFERENCE_SERVED_NAME=.*|INFERENCE_SERVED_NAME=$served_name|" "$ENV_FILE"
  sed -i "s|^INFERENCE_MAX_MODEL_LEN=.*|INFERENCE_MAX_MODEL_LEN=$max_len|" "$ENV_FILE"
  set -a; source "$ENV_FILE"; set +a

  # Restart compiler with new model
  echo "[battery]   make kurpatov-wiki-compiler-down"
  make -C "$FORGE_ROOT" kurpatov-wiki-compiler-down 2>&1 | tail -3 || true

  echo "[battery]   make kurpatov-wiki-compiler"
  make -C "$FORGE_ROOT" kurpatov-wiki-compiler 2>&1 | tail -3

  # Wait for healthy with served_name match (up to 20 minutes for cold loads)
  echo "[battery]   waiting for vLLM healthy ..."
  ok=0
  for attempt in $(seq 1 120); do
    sleep 10
    served=$(curl -fsS "${INFERENCE_BASE_URL}/models" -H "Authorization: Bearer ${VLLM_API_KEY}" 2>/dev/null | jq -r '.data[0].id' 2>/dev/null || echo "")
    if [[ "$served" == "$served_name" ]]; then
      echo "[battery]   healthy after ${attempt}0 seconds"
      ok=1
      break
    fi
  done
  if [[ $ok -ne 1 ]]; then
    echo "[battery]   FAIL: vLLM not healthy after 20 minutes — skipping experiment for $id"
    continue
  fi

  # Run one experiment
  echo "[battery]   ./run.sh"
  if "$HERE/run.sh"; then
    echo "[battery]   ✓ experiment $id succeeded"
  else
    rc=$?
    echo "[battery]   ✗ experiment $id failed (exit=$rc); continuing battery"
  fi
done

echo
echo "================================================================"
echo "[battery] done. Log: $BATTERY_LOG"
echo "[battery] Per-experiment artifacts: $STORAGE_ROOT/labs/kurpatov-wiki-bench/experiments/"
echo "================================================================"
