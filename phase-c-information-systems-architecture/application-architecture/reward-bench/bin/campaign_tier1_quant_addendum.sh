#!/usr/bin/env bash
# Quantization-comparison + extra-coverage addendum to campaign_tier1.sh.
#
# Adds 10 sweeps (each = N_TRIALS x MAX_TURNS, same condenser config as main):
#
#   Quantization comparison:
#     1. qwen3.6-27b-fp8         -> completes AWQ/NVFP4/FP8 trio for Qwen 3.6
#     2. qwen3.5-27b-fp8         -> 2-way (FP8 vs NVFP4) on Qwen 3.5
#     3. qwen3-32b-nvfp4         -> 2-way (NVFP4 vs FP8) on Qwen 3-32b
#     4. gemma-4-31b-fp8         -> 2-way (FP8 vs NVFP4) on Gemma 4-31B
#     5. nemotron-super-49b-v1.5-fp8
#     6. nemotron-super-49b-v1.5-nvfp4   (FP8 vs NVFP4 on Nemotron Super 49B)
#
#   New model coverage (single variant, no quant comparison):
#     7. qwen3.6-35b-a3b-fp8     (MoE 35B-A3B)
#     8. llama-3.3-70b-nvfp4
#     9. mistral-small-3.2-24b
#    10. devstral-small-2-24b
#
# Self-contained: helper definitions duplicated from campaign_tier1.sh so this
# can run after the main campaign without sourcing it. Output dirs use the same
# CAMPAIGN_TAG so analysis can pool results.

set -uo pipefail

EXP_BASE=/mnt/steam/forge/labs/reward-bench/experiments
RB_DIR=/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench
INFERENCE_DIR=/home/vmihaylov/forge/phase-c-information-systems-architecture/operating-modes/inference
ACTIVE_ENV=/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/wiki-compiler/.env.active-model
CAMPAIGN_TAG="${CAMPAIGN_TAG:-2026-05-08-campaign}"
N_TRIALS="${N_TRIALS:-10}"
MAX_TURNS="${MAX_TURNS:-500}"
TEMPERATURE="${TEMPERATURE:-0.7}"
CONDENSER_URL="${CONDENSER_URL:-http://172.18.0.3:8000/v1}"
CONDENSER_MODEL="${CONDENSER_MODEL:-condenser-llama31-8b}"
LOG=/tmp/campaign_tier1_quant.log

VLLM_API_KEY=$(grep "^VLLM_API_KEY=" /home/vmihaylov/forge/.env | cut -d= -f2)
HF_TOKEN=$(grep "^HF_TOKEN=" /home/vmihaylov/forge/.env | cut -d= -f2)
BLACKWELL=$(grep "^GPU_BLACKWELL_UUID=" /home/vmihaylov/forge/.env | cut -d= -f2)

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

teardown_candidate() {
  cd "$INFERENCE_DIR" && make down 2>&1 | tail -1 >> "$LOG" || true
  docker rm -f vllm-inference 2>/dev/null || true
  sleep 2
}

wait_healthy() {
  local label="$1"
  for i in $(seq 1 60); do
    local status
    status=$(docker ps --filter "name=vllm-inference" --format "{{.Status}}" 2>/dev/null)
    if echo "$status" | grep -q "(healthy)"; then
      log "  $label healthy after ${i}x20s"; return 0
    fi
    if echo "$status" | grep -qE "Up [0-9]+ minutes? "; then
      local ip
      ip=$(docker inspect vllm-inference --format "{{(index .NetworkSettings.Networks \"proxy-net\").IPAddress}}" 2>/dev/null)
      if curl -sS -m 5 -H "Authorization: Bearer $VLLM_API_KEY" "http://${ip}:8000/v1/models" | grep -q "\"id\""; then
        log "  $label serving (no healthcheck) after ${i}x20s"; return 0
      fi
    fi
    sleep 20
  done
  log "  $label FAILED to come up in 20 min"; return 1
}

bring_up_compose() {
  local model_id="$1"
  log "bring_up_compose: $model_id"
  sed -i "s/^INFERENCE_ACTIVE_MODEL_ID=.*/INFERENCE_ACTIVE_MODEL_ID=$model_id/" /home/vmihaylov/forge/.env
  bash "$RB_DIR/../wiki-compiler/bin/load-active-model.sh" 2>&1 | tail -1 >> "$LOG"
  cd "$INFERENCE_DIR"
  docker compose --env-file /home/vmihaylov/forge/.env --env-file "$ACTIVE_ENV" up -d 2>&1 | tail -1 >> "$LOG"
  wait_healthy "$model_id"
}

bring_up_custom() {
  local hf="$1"; local served="$2"; shift 2
  log "bring_up_custom: $served ($hf) extra=[$*]"
  docker run -d --name vllm-inference \
    --network=proxy-net --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=$BLACKWELL -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN \
    -e VLLM_FLASHINFER_WORKSPACE_BUFFER_SIZE=1073741824 \
    --shm-size=16gb --ipc=host \
    -v /mnt/steam/forge/shared/models:/root/.cache/huggingface \
    -v /mnt/fire/forge/shared/models/hub:/mnt/fire/forge/shared/models/hub \
    vllm/vllm-openai:v0.20.0-cu130-ubuntu2404 \
      --model "$hf" --served-model-name "$served" \
      --kv-cache-dtype fp8 --tensor-parallel-size 1 \
      --enable-prefix-caching --trust-remote-code \
      --host 0.0.0.0 --port 8000 --api-key "$VLLM_API_KEY" "$@" 2>&1 | tail -2 >> "$LOG"
  sleep 5
  wait_healthy "$served"
}

run_sweep() {
  local label="$1"; local served="$2"
  local ip
  ip=$(docker inspect vllm-inference --format "{{(index .NetworkSettings.Networks \"proxy-net\").IPAddress}}" 2>/dev/null)
  log "sweep $label served=$served ip=$ip"
  for trial in $(seq 1 "$N_TRIALS"); do
    local exp_dir="$EXP_BASE/${CAMPAIGN_TAG}-${label}-trial${trial}"
    rm -rf "$exp_dir"
    mkdir -p "$exp_dir/workspace"
    log "  trial $trial -> $exp_dir"
    cd "$RB_DIR"
    python3 -u bin/agent_loop.py \
      --shim "http://${ip}:8000/v1" --api-key "$VLLM_API_KEY" --model "$served" \
      --workspace "$exp_dir/workspace" \
      --tasks-dir "$RB_DIR/tasks" --env-dir "$RB_DIR/tasks/2048" \
      --max-iters "$MAX_TURNS" --max-no-improve 999999 --finish-floor 0 --max-wall-sec 14400 \
      --seed "$trial" --temperature "$TEMPERATURE" \
      --condenser-shim "$CONDENSER_URL" --condenser-model "$CONDENSER_MODEL" \
      --condenser-api-key "$VLLM_API_KEY" \
      --condenser-trigger-tokens 40000 --condenser-keep-recent 8 \
      --trace "$exp_dir/events.jsonl" \
      > "$exp_dir/agent.log" 2>&1
    local rc=$?
    local turns
    turns=$(grep -c "=== turn" "$exp_dir/agent.log")
    local best
    best=$(grep "\[harness\] new best dev MEAN" "$exp_dir/agent.log" | grep -oE "MEAN=[0-9]+" | sort -t= -k2 -n -r | head -1)
    log "    trial $trial done (rc=$rc, turns=$turns, $best)"
  done
}

log "==== campaign_tier1_quant_addendum start ===="

# Quant comparison block ----------------------------------------------------

# 1. Qwen 3.6-27b FP8 (completes AWQ/NVFP4/FP8 trio)
teardown_candidate
bring_up_compose qwen3.6-27b-fp8
run_sweep qwen36-fp8 qwen3.6-27b-fp8

# 2. Qwen 3.5-27b FP8 (FP8 vs NVFP4 on Qwen 3.5)
teardown_candidate
bring_up_compose qwen3.5-27b-fp8
run_sweep qwen35-fp8 qwen3.5-27b-fp8

# 3. Qwen 3-32b NVFP4 (NVFP4 vs FP8 on Qwen 3-32b)
teardown_candidate
bring_up_compose qwen3-32b-nvfp4
run_sweep qwen3-32b-nvfp4 qwen3-32b-nvfp4

# 4. Gemma 4-31b FP8 (FP8 vs NVFP4 on Gemma 4)
teardown_candidate
bring_up_compose gemma-4-31b-fp8
run_sweep gemma4-fp8 gemma-4-31b-fp8

# 5. Nemotron Super 49B v1.5 FP8
teardown_candidate
bring_up_compose nemotron-super-49b-v1.5-fp8
run_sweep nemotron-49b-fp8 nemotron-super-49b-v1.5-fp8

# 6. Nemotron Super 49B v1.5 NVFP4
teardown_candidate
bring_up_compose nemotron-super-49b-v1.5-nvfp4
run_sweep nemotron-49b-nvfp4 nemotron-super-49b-v1.5-nvfp4

# 6b. Devstral-2-123B AWQ-4bit (AWQ vs NVFP4 on a 123B model)
teardown_candidate
bring_up_custom cyankiwi/Devstral-2-123B-Instruct-2512-AWQ-4bit devstral-2-123b-awq \
  --max-model-len 32768 --gpu-memory-utilization 0.92 --tool-call-parser mistral
run_sweep devstral-2-123b-awq devstral-2-123b-awq

# Extra coverage block (single variant, no quant comparison) ----------------

# 7. Qwen 3.6 35B-A3B FP8 (MoE)
teardown_candidate
bring_up_compose qwen3.6-35b-a3b-fp8
run_sweep qwen36-35b-a3b qwen3.6-35b-a3b-fp8

# 8. Llama 3.3 70B NVFP4
teardown_candidate
bring_up_compose llama-3.3-70b-nvfp4
run_sweep llama33-70b llama-3.3-70b-nvfp4

# 9. Mistral Small 3.2 24B
teardown_candidate
bring_up_compose mistral-small-3.2-24b
run_sweep mistral-small-24b mistral-small-3.2-24b

# 10. Devstral Small 2 24B
teardown_candidate
bring_up_compose devstral-small-2-24b
run_sweep devstral-small-24b devstral-small-2-24b

teardown_candidate
log "==== campaign_tier1_quant_addendum done ===="
