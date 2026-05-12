#!/usr/bin/env bash
# Smoke-test driver: validate each rescue+VL candidate end-to-end with one
# tool-call request before committing to a full N=10 sweep.
#
# Per model:
#   1. Bring up vLLM with the planned flags
#   2. Send a small 2048-style request asking for a `view` tool call
#   3. Run parse_tool_calls (incl. BPE detokenizer + relaxed regex) on the reply
#   4. Report PASS / FAIL with the reason
#   5. Teardown
#
# Time per model: download + load + warmup + 1 inference ≈ 1-6 min depending on size.
set -uo pipefail
source /home/vmihaylov/forge/.env

RB_DIR=/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench
BLACKWELL_UUID=$GPU_BLACKWELL_UUID
LOG=/tmp/smoke_test_$(date +%H%M%S).log

# Args list: served_name hf_path bring_up_extra_flags
# (use ';' to separate models; pipe-separate the fields)
QUEUE=(
  "nemotron-49b-fp8|nvidia/Llama-3.3-Nemotron-Super-49B-v1.5-FP8|--kv-cache-dtype fp8 --max-model-len 65536 --gpu-memory-utilization 0.92 --tool-call-parser hermes"
  "qwen2.5-vl-7b-awq|Qwen/Qwen2.5-VL-7B-Instruct-AWQ|--max-model-len 32768 --gpu-memory-utilization 0.85 --tool-call-parser hermes"
  "holo1.5-7b|Hcompany/Holo1.5-7B|--max-model-len 32768 --gpu-memory-utilization 0.90 --tool-call-parser hermes"
  "ui-tars-1.5-7b|ByteDance-Seed/UI-TARS-1.5-7B|--max-model-len 32768 --gpu-memory-utilization 0.85 --tool-call-parser hermes"
  "holo2-8b|Hcompany/Holo2-8B|--max-model-len 16384 --gpu-memory-utilization 0.90 --tool-call-parser hermes"
  "qwen3-vl-32b-nvfp4|RedHatAI/Qwen3-VL-32B-Instruct-NVFP4|--max-model-len 16384 --gpu-memory-utilization 0.92 --tool-call-parser hermes --enforce-eager"
  "qwen2.5-vl-32b-awq|Qwen/Qwen2.5-VL-32B-Instruct-AWQ|--max-model-len 32768 --gpu-memory-utilization 0.85 --tool-call-parser hermes --enforce-eager"
  "qwen2.5-vl-72b-awq|Qwen/Qwen2.5-VL-72B-Instruct-AWQ|--max-model-len 32768 --gpu-memory-utilization 0.92 --tool-call-parser hermes --enforce-eager"
  "holo3-35b-a3b|Hcompany/Holo3-35B-A3B|--kv-cache-dtype fp8 --max-model-len 32768 --max-num-seqs 256 --gpu-memory-utilization 0.92 --tool-call-parser hermes --enforce-eager"
  "holo2-30b-a3b|Hcompany/Holo2-30B-A3B|--kv-cache-dtype fp8 --max-model-len 32768 --max-num-seqs 256 --gpu-memory-utilization 0.92 --tool-call-parser hermes --enforce-eager"
)

log()  { echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }

teardown() {
  docker rm -f vllm-smoke-$$ >/dev/null 2>&1
}

bring_up() {
  local hf=$1; local served=$2; shift 2
  docker run -d --name vllm-smoke-$$ \
    --network=proxy-net --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=$BLACKWELL_UUID \
    -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN \
    -e VLLM_FLASHINFER_WORKSPACE_BUFFER_SIZE=1073741824 \
    -e VLLM_USE_FLASHINFER_MOE_FP4=1 \
    --shm-size=16gb --ipc=host \
    -v /mnt/steam/forge/shared/models:/root/.cache/huggingface \
    -v /mnt/fire/forge/shared/models/hub:/mnt/fire/forge/shared/models/hub \
    vllm/vllm-openai:v0.20.0-cu130-ubuntu2404 \
    --model "$hf" --served-model-name "$served" \
    --enable-prefix-caching --trust-remote-code --enable-auto-tool-choice \
    --host 0.0.0.0 --port 8000 \
    --api-key "$VLLM_API_KEY" \
    "$@" >> $LOG 2>&1 || return 1
  for i in $(seq 1 90); do
    sleep 20
    local ip
    ip=$(docker inspect vllm-smoke-$$ --format '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}' 2>/dev/null) || true
    if [[ -n $ip ]] && curl -sS -m 5 \
        -H "Authorization: Bearer $VLLM_API_KEY" \
        "http://${ip}:8000/v1/models" | grep -q '"id"'; then
      echo "$ip"
      return 0
    fi
  done
  return 2
}

probe_tool_call() {
  local ip=$1; local served=$2
  python3 - <<PYEOF
import sys, json, urllib.request, re
sys.path.insert(0, "$RB_DIR/bin")
from agent_loop import parse_tool_calls, _detokenize_bpe
body = {
  "model": "$served",
  "messages": [
    {"role": "system", "content": (
      "You have tools: view(path), bash(cmd), finish(note). "
      "Each tool call must be in a fenced code block tagged \`tool\` "
      "with a JSON body like:\n\n\`\`\`tool\n"
      "{\"name\": \"view\", \"args\": {\"path\": \"/tasks/2048/SKILL_tier1.md\"}}\n"
      "\`\`\`\n\nALWAYS emit at least one tool call per turn."
    )},
    {"role": "user", "content": "Start by viewing /tasks/2048/SKILL_tier1.md."}
  ],
  "tool_choice": "none",
  "max_tokens": 400,
  "temperature": 0.0,
}
req = urllib.request.Request(
  "http://$ip:8000/v1/chat/completions",
  data=json.dumps(body).encode(),
  headers={"Content-Type": "application/json",
           "Authorization": "Bearer $VLLM_API_KEY"},
)
try:
  with urllib.request.urlopen(req, timeout=120) as r:
    j = json.loads(r.read())
except Exception as e:
  print("HTTP_ERROR:", str(e)[:200])
  sys.exit(1)
m = j["choices"][0]["message"]
raw = (m.get("reasoning") or "") + (m.get("content") or "")
clean = _detokenize_bpe(raw)
calls = parse_tool_calls(clean)
if calls:
  print(f"OK  tool={calls[0][0]} args={calls[0][1]}")
  sys.exit(0)
print(f"PARSE_FAIL raw={clean[:200]!r}")
sys.exit(1)
PYEOF
}

echo "=== smoke-test queue ===" | tee $LOG
PASS=()
FAIL=()
for entry in "${QUEUE[@]}"; do
  IFS='|' read -r served hf extra <<< "$entry"
  log "--- $served ($hf) ---"
  teardown
  ip=$(bring_up "$hf" "$served" $extra) || {
    log "  FAIL bring_up"
    FAIL+=("$served: bring_up")
    continue
  }
  if probe_tool_call "$ip" "$served" 2>&1 | tee -a $LOG | grep -q "^OK"; then
    log "  PASS"
    PASS+=("$served")
  else
    log "  FAIL probe"
    FAIL+=("$served: probe")
  fi
done
teardown

echo
echo "=== SUMMARY ===" | tee -a $LOG
echo "PASS (${#PASS[@]}): ${PASS[*]}" | tee -a $LOG
echo "FAIL (${#FAIL[@]}): ${FAIL[*]}" | tee -a $LOG
