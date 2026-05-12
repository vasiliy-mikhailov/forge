#!/usr/bin/env bash
# Continuation of campaign_tier1_quant_addendum after the 2026-05-10
# decision: skip the broken nemotron-49b sweeps (hostname error and
# no_tool_calls in the originals), add 4 nemotron-3-nano sweeps as
# the headline new-architecture comparison, then resume the original
# remaining queue (devstral-2-123b-awq through devstral-small-24b).
#
# Run this in place of the original campaign_tier1_quant_addendum
# from the chainer (see /tmp/addendum_chainer.log timeline).

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
    -e VLLM_USE_FLASHINFER_MOE_FP4=1 \
    -e VLLM_FLASHINFER_MOE_BACKEND=throughput \
    --shm-size=16gb --ipc=host \
    -v /mnt/steam/forge/shared/models:/root/.cache/huggingface \
    -v /mnt/fire/forge/shared/models/hub:/mnt/fire/forge/shared/models/hub \
    vllm/vllm-openai:v0.20.0-cu130-ubuntu2404 \
      --model "$hf" --served-model-name "$served" \
      --kv-cache-dtype fp8 --tensor-parallel-size 1 \
      --enable-prefix-caching --trust-remote-code \
      --enable-auto-tool-choice --tool-call-parser qwen3_coder \
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
      --condenser-shim "http://${ip}:8000/v1" --condenser-model "$served" \
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

log "==== campaign_continue_2026-05-11 start (self-condense from 2026-05-11 ~10:10 MSK) ===="
log "skipping completed: qwen36-fp8, qwen35-fp8, qwen3-32b-nvfp4, gemma4-fp8, nemotron3-nano-fp8, nemotron3-nano-nvfp4"
log "skipping broken:     nemotron-49b-fp8 (hostname err), nemotron-49b-nvfp4 (no tool calls)"

# NEW: Nemotron 3 Nano family (released 2026-04-28) ------------------

# N1. Nemotron 3 Nano 30B-A3B FP8 -- DONE 2026-05-11 (mean 3133, n=8/10, best 4624)
# teardown_candidate
# bring_up_custom nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8 nemotron3-nano-fp8 \
#   --max-model-len 131072 --gpu-memory-utilization 0.85
# run_sweep nemotron3-nano-fp8 nemotron3-nano-fp8

# N2. Nemotron 3 Nano 30B-A3B NVFP4 -- DONE 2026-05-11 (mean 2506, n=7/10, best 3311)
# teardown_candidate
# bring_up_custom nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-NVFP4 nemotron3-nano-nvfp4 \
#   --max-model-len 131072 --gpu-memory-utilization 0.85
# run_sweep nemotron3-nano-nvfp4 nemotron3-nano-nvfp4

# N3. Nemotron 3 Nano Omni 30B-A3B Reasoning FP8 (multimodal but tested on text Tier 1)
teardown_candidate
bring_up_custom nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-FP8 nemotron3-nano-omni-fp8 \
  --max-model-len 131072 --gpu-memory-utilization 0.85
run_sweep nemotron3-nano-omni-fp8 nemotron3-nano-omni-fp8

# N4. Nemotron 3 Nano Omni 30B-A3B Reasoning NVFP4
teardown_candidate
bring_up_custom nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4 nemotron3-nano-omni-nvfp4 \
  --max-model-len 131072 --gpu-memory-utilization 0.85
run_sweep nemotron3-nano-omni-nvfp4 nemotron3-nano-omni-nvfp4

# RESUME ORIGINAL ADDENDUM QUEUE ----------------------------------

# Devstral-2-123B AWQ-4bit (AWQ vs NVFP4 on a 123B model)
teardown_candidate
bring_up_custom cyankiwi/Devstral-2-123B-Instruct-2512-AWQ-4bit devstral-2-123b-awq \
  --max-model-len 32768 --gpu-memory-utilization 0.92 --tool-call-parser mistral
run_sweep devstral-2-123b-awq devstral-2-123b-awq

# Qwen 3.6 35B-A3B FP8 (MoE)
teardown_candidate
bring_up_compose qwen3.6-35b-a3b-fp8
run_sweep qwen36-35b-a3b qwen3.6-35b-a3b-fp8

# Llama 3.3 70B NVFP4
teardown_candidate
bring_up_compose llama-3.3-70b-nvfp4
run_sweep llama33-70b llama-3.3-70b-nvfp4

# Mistral Small 4 119B (MoE, 6.5B active) NVFP4 -- peer to Nemotron 3 Nano Omni
teardown_candidate
bring_up_custom mistralai/Mistral-Small-4-119B-2603-NVFP4 mistral-small-4-nvfp4 \
  --max-model-len 131072 --gpu-memory-utilization 0.85 --tool-call-parser mistral
run_sweep mistral-small-4-nvfp4 mistral-small-4-nvfp4

# Mistral Medium 3.5 128B Dense NVFP4 -- heavyweight dense omni
teardown_candidate
bring_up_custom mistralai/Mistral-Medium-3.5-128B mistral-medium-3-5-nvfp4 \
  --max-model-len 131072 --gpu-memory-utilization 0.92 \
  --quantization modelopt_fp4 --tool-call-parser mistral
run_sweep mistral-medium-3-5-nvfp4 mistral-medium-3-5-nvfp4

# Mistral Small 4 119B BF16 -- quant cost comparison vs M1 (heavy load; may time out)
teardown_candidate
bring_up_custom mistralai/Mistral-Small-4-119B-2603 mistral-small-4-bf16 \
  --max-model-len 65536 --gpu-memory-utilization 0.95 --tool-call-parser mistral
run_sweep mistral-small-4-bf16 mistral-small-4-bf16

# Mistral Small 3.2 24B (original entry, kept for completeness)
teardown_candidate
bring_up_compose mistral-small-3.2-24b
run_sweep mistral-small-24b mistral-small-3.2-24b

# Devstral Small 2 24B
teardown_candidate
bring_up_compose devstral-small-2-24b
run_sweep devstral-small-24b devstral-small-2-24b

teardown_candidate
log "==== campaign_continue_2026-05-11 done ===="
