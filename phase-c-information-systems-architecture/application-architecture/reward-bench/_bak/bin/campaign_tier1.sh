#!/usr/bin/env bash
# Campaign: 1 sweep per candidate model. Each sweep = 10 trials × MAX_TURNS turns
# with the default condenser (condenser-llama31-8b on RTX 5090).
#
# Models are processed sequentially (single Blackwell). For each model:
#   1. Tear down vllm-inference, bring up the new candidate via per-model setup fn
#   2. Wait for healthy
#   3. Loop 10 trials, each running agent_loop.py with --seed N --temperature 0.7
#      --max-iters 500 --condenser-shim ... etc.
#
# Per-model setup uses docker-compose where the registry handles the model
# cleanly, and a custom `docker run` for tricky models (gpt-oss, devstral-123b,
# nemotron-3-super-120b) that need non-standard flags.
#
# Output: /mnt/steam/forge/labs/reward-bench/experiments/2026-05-08-campaign-{label}-trial{N}

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
LOG=/tmp/campaign_tier1.log

VLLM_API_KEY=$(grep "^VLLM_API_KEY=" /home/vmihaylov/forge/.env | cut -d= -f2)
HF_TOKEN=$(grep "^HF_TOKEN=" /home/vmihaylov/forge/.env | cut -d= -f2)
BLACKWELL=$(grep "^GPU_BLACKWELL_UUID=" /home/vmihaylov/forge/.env | cut -d= -f2)

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG"; }

teardown_candidate() {
  cd "$INFERENCE_DIR" && make down 2>&1 | tail -1 >> "$LOG" || true
  docker rm -f vllm-inference 2>/dev/null || true
  sleep 2
}

# Wait up to N×20s for vllm-inference to be (healthy) OR Up >2min serving traffic.
wait_healthy() {
  local label="$1"
  for i in $(seq 1 60); do
    local status
    status=$(docker ps --filter "name=vllm-inference" --format "{{.Status}}" 2>/dev/null)
    if echo "$status" | grep -q "(healthy)"; then
      log "  $label healthy after ${i}×20s"; return 0
    fi
    if echo "$status" | grep -qE "Up [0-9]+ minutes? "; then
      # Container has no healthcheck (custom docker run) — try /v1/models
      local ip
      ip=$(docker inspect vllm-inference --format '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}' 2>/dev/null)
      if curl -sS -m 5 -H "Authorization: Bearer $VLLM_API_KEY" "http://${ip}:8000/v1/models" | grep -q '"id"'; then
        log "  $label serving (no healthcheck) after ${i}×20s"; return 0
      fi
    fi
    sleep 20
  done
  log "  $label FAILED to come up in 20 min"; return 1
}

# Bring up via docker-compose using registry. $1 = INFERENCE_ACTIVE_MODEL_ID.
bring_up_compose() {
  local model_id="$1"
  log "bring_up_compose: $model_id"
  sed -i "s/^INFERENCE_ACTIVE_MODEL_ID=.*/INFERENCE_ACTIVE_MODEL_ID=$model_id/" /home/vmihaylov/forge/.env
  bash "$RB_DIR/../wiki-compiler/bin/load-active-model.sh" 2>&1 | tail -1 >> "$LOG"
  cd "$INFERENCE_DIR"
  docker compose --env-file /home/vmihaylov/forge/.env --env-file "$ACTIVE_ENV" up -d 2>&1 | tail -1 >> "$LOG"
  wait_healthy "$model_id"
}

# Bring up via custom docker run. Args: hf_path served_name [extra_args...]
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
  ip=$(docker inspect vllm-inference --format '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}' 2>/dev/null)
  log "sweep $label served=$served ip=$ip"
  for trial in $(seq 1 "$N_TRIALS"); do
    local exp_dir="$EXP_BASE/${CAMPAIGN_TAG}-${label}-trial${trial}"
    rm -rf "$exp_dir"
    mkdir -p "$exp_dir/workspace"
    log "  trial $trial → $exp_dir"
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
    turns=$(grep -c '=== turn' "$exp_dir/agent.log")
    local best
    best=$(grep '\[harness\] new best dev MEAN' "$exp_dir/agent.log" | grep -oE 'MEAN=[0-9]+' | sort -t= -k2 -n -r | head -1)
    log "    trial $trial done (rc=$rc, turns=$turns, $best)"
  done
}

# === Models in the campaign ===
# Sequenced fastest to slowest for early data.
log "==== campaign_tier1 start ===="

# 1. Qwen 3.6-27B AWQ-INT4 (top scorer, fast)
teardown_candidate
bring_up_compose qwen3.6-27b-awq-int4-community
run_sweep qwen36-awq qwen3.6-27b

# 2. Qwen 3.6-27B NVFP4 (sakamakismile pack)
teardown_candidate
bring_up_compose qwen3.6-27b-nvfp4
run_sweep qwen36-nvfp4 qwen3.6-27b-nvfp4

# 3. Qwen 3.5-27B NVFP4 (kaitchup A16)
teardown_candidate
bring_up_compose qwen3.5-27b-nvfp4
run_sweep qwen35-nvfp4 qwen3.5-27b-nvfp4

# 4. Qwen 3-32B FP8
teardown_candidate
bring_up_compose qwen3-32b-fp8
run_sweep qwen3-32b-fp8 qwen3-32b-fp8

# 5. Gemma 4-31B IT NVFP4
teardown_candidate
bring_up_compose gemma-4-31b-nvfp4
run_sweep gemma4-31b gemma-4-31b-nvfp4

# 6. Qwen 2.5-72B NVFP4 (slow)
teardown_candidate
bring_up_compose qwen2.5-72b-nvfp4
run_sweep qwen25-72b qwen2.5-72b-nvfp4

# 7. gpt-oss-20b (custom: no tool-call-parser)
teardown_candidate
bring_up_custom openai/gpt-oss-20b gpt-oss-20b --max-model-len 65536 --gpu-memory-utilization 0.85
run_sweep gpt-oss-20b gpt-oss-20b

# 8. gpt-oss-120b (custom: no tool-call-parser)
teardown_candidate
bring_up_custom openai/gpt-oss-120b gpt-oss-120b --max-model-len 65536 --gpu-memory-utilization 0.92
run_sweep gpt-oss-120b gpt-oss-120b

# 9. Nemotron-3 Super 120B-A12B NVFP4 (Mamba hybrid; needs --max-num-seqs and TRITON_ATTN)
teardown_candidate
bring_up_custom nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4 nemotron-3-super-120b-nvfp4 \
  --max-model-len 32768 --gpu-memory-utilization 0.92 --max-num-seqs 64 \
  --attention-backend TRITON_ATTN
run_sweep nemotron-3-super-120b nemotron-3-super-120b-nvfp4

# 10. Devstral-2 123B NVFP4 (slowest; FlashInfer workspace already bumped via env)
teardown_candidate
bring_up_custom BrainForge/Devstral-2-123B-Instruct-2512-NVFP4 devstral-2-123b-nvfp4 \
  --max-model-len 32768 --gpu-memory-utilization 0.92 --tool-call-parser mistral
run_sweep devstral-2-123b devstral-2-123b-nvfp4

teardown_candidate
log "==== campaign_tier1 done ===="
