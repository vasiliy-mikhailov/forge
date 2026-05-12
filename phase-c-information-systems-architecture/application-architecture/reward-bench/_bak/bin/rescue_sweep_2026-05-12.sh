#!/usr/bin/env bash
# Rescue sweep for 2048 reward-bench: re-run models that the original
# 2026-05-11 campaign couldn't score, plus add the control-minecraft
# VL models as text-only LLMs.
#
# Prerequisite fixes already applied to bin/agent_loop.py:
#   - _detokenize_bpe strips Ġ (U+0120 leading-space), Ċ (U+010A newline),
#     ĉ (U+0109 tab) from model replies
#   - _TOOL_BLOCK_RE relaxed: ```tool\b\s* instead of ```tool\s*\n
#     (Mistral/Pixtral emit ```tool{...} with no newline)
#
# Tag: 2026-05-12-rescue — separate from the original 2026-05-08-campaign
# so dirs don't collide.

set -uo pipefail

RB_DIR=/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench
LOG=/tmp/rescue_sweep_2026-05-12.log
EXP_BASE=/mnt/steam/forge/labs/reward-bench/experiments
TAG=2026-05-12-rescue
N_TRIALS=${N_TRIALS:-10}
BLACKWELL_UUID=GPU-315974eb-b8ad-dceb-62b0-f24a774d5327
VLLM_API_KEY=sk-ef2926520a83b7f6efac7f4dc5b049842b4b2baebfdc18b69b76220f29fdf272

log()  { echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }

teardown() {
  docker rm -f vllm-inference 2>&1 | tail -1 | tee -a $LOG
}

# Args: hf_path served_name extra_flags...
bring_up() {
  local hf=$1; local served=$2; shift 2
  log "bring_up: $served ($hf) extra=$*"
  docker run -d --name vllm-inference \
    --network=proxy-net --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=$BLACKWELL_UUID \
    -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN \
    -e HF_HUB_CACHE=/mnt/steam/forge/shared/models/hub \
    -e VLLM_FLASHINFER_WORKSPACE_BUFFER_SIZE=1073741824 \
    -e VLLM_USE_FLASHINFER_MOE_FP4=1 \
    -e VLLM_FLASHINFER_MOE_BACKEND=throughput \
    --shm-size=16gb --ipc=host \
    -v /mnt/steam/forge/shared/models:/root/.cache/huggingface \
    -v /mnt/fire/forge/shared/models/hub:/mnt/fire/forge/shared/models/hub \
    vllm/vllm-openai:v0.20.0-cu130-ubuntu2404 \
      --model "$hf" --served-model-name "$served" \
      --tensor-parallel-size 1 \
      --enable-prefix-caching --trust-remote-code \
      --enable-auto-tool-choice \
      --host 0.0.0.0 --port 8000 \
      --api-key "$VLLM_API_KEY" \
      "$@" >> $LOG 2>&1
  for i in $(seq 1 60); do
    sleep 20
    local ip
    ip=$(docker inspect vllm-inference --format '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}' 2>/dev/null)
    if [[ -n $ip ]] && curl -sS -m 5 -H "Authorization: Bearer $VLLM_API_KEY" "http://${ip}:8000/v1/models" | grep -q '"id"'; then
      log "  $served serving at $ip after ${i}x20s"
      return 0
    fi
  done
  log "  $served FAILED to serve"
  docker logs --tail 30 vllm-inference 2>&1 | tail -30 | tee -a $LOG
  return 1
}

run_sweep() {
  local label=$1; local served=$2
  local ip
  ip=$(docker inspect vllm-inference --format '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}' 2>/dev/null)
  log "sweep $label served=$served ip=$ip"
  for trial in $(seq 1 $N_TRIALS); do
    local exp_dir=$EXP_BASE/${TAG}-${label}-trial${trial}
    rm -rf "$exp_dir"
    mkdir -p "$exp_dir/workspace"
    log "  trial $trial -> $exp_dir"
    python3 -u $RB_DIR/bin/agent_loop.py \
      --shim "http://${ip}:8000/v1" --api-key "$VLLM_API_KEY" --model "$served" \
      --workspace "$exp_dir/workspace" \
      --tasks-dir "$RB_DIR/tasks" --env-dir "$RB_DIR/tasks/2048" \
      --max-iters 500 --max-no-improve 999999 --finish-floor 0 --max-wall-sec 14400 \
      --seed $trial --temperature 0.7 \
      --condenser-shim "http://${ip}:8000/v1" --condenser-model "$served" \
      --condenser-api-key "$VLLM_API_KEY" \
      --condenser-trigger-tokens 40000 --condenser-keep-recent 8 \
      --trace "$exp_dir/events.jsonl" >> $LOG 2>&1 || log "    trial $trial agent_loop exited non-zero"
    # Quick score peek
    local best
    best=$(grep -oE '"best_dev_mean":[ ]?[^,}]+' "$exp_dir/events.jsonl" 2>/dev/null | tail -1)
    log "    trial $trial done  $best"
  done
}

# ------------------------------------------------------------------------
# Queue
# ------------------------------------------------------------------------

log "== Rescue sweep start =="

# ===== HIGH PRIORITY: Qwen3.6-27B BF16 (base, full precision) =====
log "-- Qwen3.6-27B BF16 (full precision) --"
teardown
if bring_up Qwen/Qwen3.6-27B qwen3.6-27b-bf16 \
     --kv-cache-dtype fp8 --max-model-len 32768 --max-num-seqs 256 \
     --gpu-memory-utilization 0.85 --tool-call-parser qwen3_coder ; then
  run_sweep qwen3.6-27b-bf16 qwen3.6-27b-bf16
fi

# (1) Mistral Small 3.2 24B (already loaded; just run the sweep)
log "-- Mistral Small 3.2 24B --"
run_sweep mistral-small-3.2-24b mistral-small-3.2-24b

# (2) Mistral Small 4 119B NVFP4 (Pixtral)
log "-- Mistral Small 4 119B NVFP4 --"
teardown
if bring_up mistralai/Mistral-Small-4-119B-2603-NVFP4 mistral-small-4-nvfp4 \
     --kv-cache-dtype fp8 --max-model-len 131072 \
     --gpu-memory-utilization 0.85 --tool-call-parser mistral ; then
  run_sweep mistral-small-4-nvfp4 mistral-small-4-nvfp4
fi

# (3) Devstral Small 2 24B NVFP4
log "-- Devstral Small 2 24B NVFP4 --"
teardown
if bring_up Firworks/Devstral-Small-2-24B-Instruct-2512-nvfp4 devstral-small-2-24b \
     --kv-cache-dtype fp8 --max-model-len 131072 \
     --gpu-memory-utilization 0.85 --tool-call-parser mistral ; then
  run_sweep devstral-small-2-24b devstral-small-2-24b
fi

# (4) Devstral 2 123B AWQ-4bit
log "-- Devstral 2 123B AWQ --"
teardown
if bring_up cyankiwi/Devstral-2-123B-Instruct-2512-AWQ-4bit devstral-2-123b-awq \
     --kv-cache-dtype fp8 --max-model-len 32768 \
     --gpu-memory-utilization 0.92 --tool-call-parser mistral ; then
  run_sweep devstral-2-123b-awq devstral-2-123b-awq
fi

# (5) Nemotron Super 49B FP8 (Llama-based; same BPE issue likely)
log "-- Nemotron Super 49B FP8 --"
teardown
if bring_up nvidia/Llama-3.3-Nemotron-Super-49B-v1.5-FP8 nemotron-49b-fp8 \
     --kv-cache-dtype fp8 --max-model-len 131072 \
     --gpu-memory-utilization 0.92 --tool-call-parser hermes ; then
  run_sweep nemotron-49b-fp8 nemotron-49b-fp8
fi

# --- NEW: control-minecraft VL models as text-only LLMs on 2048 ---

# (6) Qwen2.5-VL-7B-Instruct-AWQ
log "-- Qwen2.5-VL-7B-AWQ (text-only on 2048) --"
teardown
if bring_up Qwen/Qwen2.5-VL-7B-Instruct-AWQ qwen2.5-vl-7b-awq \
     --max-model-len 32768 --gpu-memory-utilization 0.85 \
     --tool-call-parser hermes ; then
  run_sweep qwen2.5-vl-7b-awq qwen2.5-vl-7b-awq
fi

# (7) Holo1.5-7B (Qwen2.5-VL-7B + UI FT)
log "-- Holo1.5-7B --"
teardown
if bring_up Hcompany/Holo1.5-7B holo1.5-7b \
     --max-model-len 32768 --gpu-memory-utilization 0.90 \
     --tool-call-parser hermes ; then
  run_sweep holo1.5-7b holo1.5-7b
fi

# (8) UI-TARS-1.5-7B
log "-- UI-TARS-1.5-7B --"
teardown
if bring_up ByteDance-Seed/UI-TARS-1.5-7B ui-tars-1.5-7b \
     --max-model-len 32768 --gpu-memory-utilization 0.85 \
     --tool-call-parser hermes ; then
  run_sweep ui-tars-1.5-7b ui-tars-1.5-7b
fi

# (9) Holo2-8B (Qwen3-VL-Thinking + UI FT)
log "-- Holo2-8B --"
teardown
if bring_up Hcompany/Holo2-8B holo2-8b \
     --max-model-len 16384 --gpu-memory-utilization 0.90 \
     --tool-call-parser hermes ; then
  run_sweep holo2-8b holo2-8b
fi

# (10) Qwen3-VL-32B-NVFP4
log "-- Qwen3-VL-32B-NVFP4 --"
teardown
if bring_up RedHatAI/Qwen3-VL-32B-Instruct-NVFP4 qwen3-vl-32b-nvfp4 \
     --max-model-len 16384 --gpu-memory-utilization 0.92 \
     --tool-call-parser hermes ; then
  run_sweep qwen3-vl-32b-nvfp4 qwen3-vl-32b-nvfp4
fi


# ===== NEW: VL upgrades on Blackwell =====

# Qwen2.5-VL-32B-Instruct AWQ (fits 5090 too, but here we run it on Blackwell for 2048)
log "-- Qwen2.5-VL-32B-Instruct AWQ --"
teardown
if bring_up Qwen/Qwen2.5-VL-32B-Instruct-AWQ qwen2.5-vl-32b-awq \
     --max-model-len 32768 --max-num-seqs 256 \
     --gpu-memory-utilization 0.85 --tool-call-parser hermes ; then
  run_sweep qwen2.5-vl-32b-awq qwen2.5-vl-32b-awq
fi

# Qwen2.5-VL-72B-Instruct AWQ (Blackwell only)
log "-- Qwen2.5-VL-72B-Instruct AWQ --"
teardown
if bring_up Qwen/Qwen2.5-VL-72B-Instruct-AWQ qwen2.5-vl-72b-awq \
     --max-model-len 32768 --max-num-seqs 256 \
     --gpu-memory-utilization 0.92 --tool-call-parser hermes ; then
  run_sweep qwen2.5-vl-72b-awq qwen2.5-vl-72b-awq
fi

# Holo3-35B-A3B (BF16, ~70 GB; Blackwell only; MoE, fast decode)
log "-- Holo3-35B-A3B BF16 --"
teardown
if bring_up Hcompany/Holo3-35B-A3B holo3-35b-a3b \
     --kv-cache-dtype fp8 --max-model-len 32768 --max-num-seqs 256 \
     --gpu-memory-utilization 0.92 --tool-call-parser hermes ; then
  run_sweep holo3-35b-a3b holo3-35b-a3b
fi

# Holo2-30B-A3B (BF16, ~60 GB; Blackwell only)
log "-- Holo2-30B-A3B BF16 --"
teardown
if bring_up Hcompany/Holo2-30B-A3B holo2-30b-a3b \
     --kv-cache-dtype fp8 --max-model-len 32768 --max-num-seqs 256 \
     --gpu-memory-utilization 0.92 --tool-call-parser hermes ; then
  run_sweep holo2-30b-a3b holo2-30b-a3b
fi

log "== Rescue sweep complete =="
