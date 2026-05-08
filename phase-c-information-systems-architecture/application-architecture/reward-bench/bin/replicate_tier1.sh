#!/usr/bin/env bash
# Replication: N trials of one candidate model with a condenser model.
#
# Defaults to:
#   candidate  = qwen3.6-27b-awq-int4 served by vllm-inference (Blackwell)
#   condenser  = condenser-llama31-8b served by vllm-condenser (RTX 5090)
#   N_TRIALS   = 10
#   MAX_TURNS  = 200
#   TEMP       = 0.7
#
# Override via env vars on the command line.

set -uo pipefail

EXP_BASE=/mnt/steam/forge/labs/reward-bench/experiments
RB_DIR=/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench

CANDIDATE_MODEL="${CANDIDATE_MODEL:-qwen3.6-27b}"
CANDIDATE_URL="${CANDIDATE_URL:-http://172.18.0.2:8000/v1}"
CONDENSER_MODEL="${CONDENSER_MODEL:-condenser-llama31-8b}"
CONDENSER_URL="${CONDENSER_URL:-http://172.18.0.3:8000/v1}"
N_TRIALS="${N_TRIALS:-10}"
MAX_TURNS="${MAX_TURNS:-200}"
TEMPERATURE="${TEMPERATURE:-0.7}"
DATE_TAG="${DATE_TAG:-2026-05-08}"
LABEL="${LABEL:-qwen36-awq-condensed}"

VLLM_API_KEY=$(grep "^VLLM_API_KEY=" /home/vmihaylov/forge/.env | cut -d= -f2)

echo "=== replication start $(date -Iseconds) ===" | tee /tmp/replicate_tier1.log
echo "  candidate: $CANDIDATE_MODEL @ $CANDIDATE_URL" | tee -a /tmp/replicate_tier1.log
echo "  condenser: $CONDENSER_MODEL @ $CONDENSER_URL" | tee -a /tmp/replicate_tier1.log
echo "  trials=$N_TRIALS turns=$MAX_TURNS temp=$TEMPERATURE" | tee -a /tmp/replicate_tier1.log

for trial in $(seq 1 "$N_TRIALS"); do
  exp_dir="$EXP_BASE/${DATE_TAG}-${LABEL}-trial${trial}"
  rm -rf "$exp_dir"
  mkdir -p "$exp_dir/workspace"

  echo "--- trial $trial → $exp_dir ---" | tee -a /tmp/replicate_tier1.log

  cd "$RB_DIR"
  python3 -u bin/agent_loop.py \
    --shim "$CANDIDATE_URL" --api-key "$VLLM_API_KEY" --model "$CANDIDATE_MODEL" \
    --workspace "$exp_dir/workspace" \
    --tasks-dir "$RB_DIR/tasks" --env-dir "$RB_DIR/tasks/2048" \
    --max-iters "$MAX_TURNS" --max-no-improve 999999 --finish-floor 0 --max-wall-sec 7200 \
    --seed "$trial" --temperature "$TEMPERATURE" \
    --condenser-shim "$CONDENSER_URL" --condenser-model "$CONDENSER_MODEL" \
    --condenser-api-key "$VLLM_API_KEY" \
    --condenser-trigger-tokens 80000 --condenser-keep-recent 8 \
    --trace "$exp_dir/events.jsonl" \
    > "$exp_dir/agent.log" 2>&1
  rc=$?
  turns=$(grep -c '=== turn' "$exp_dir/agent.log")
  best=$(grep '\[harness\] new best dev MEAN' "$exp_dir/agent.log" | tail -1 | grep -oE 'MEAN=[0-9]+' | head -1)
  echo "  trial $trial done (rc=$rc, turns=$turns, best=$best)" | tee -a /tmp/replicate_tier1.log
done

echo "=== replication done $(date -Iseconds) ===" | tee -a /tmp/replicate_tier1.log
