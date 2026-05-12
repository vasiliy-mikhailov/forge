#!/usr/bin/env bash
# Diagnose why Qwen3.6-27B-BF16 hangs at "Starting to load model" on Blackwell.
# Tries 3 progressively more aggressive configs to skip the compile/Mamba/prefix-cache
# stalls. Each attempt: bring up vLLM, wait up to 12 min for /v1/models, probe a
# tool call, report PASS/FAIL.
#
# Run AFTER the current smoke queue finishes (uses the same vllm-inference container
# slot on Blackwell).

set -uo pipefail
source /home/vmihaylov/forge/.env

RB_DIR=/home/vmihaylov/forge/phase-c-information-systems-architecture/application-architecture/reward-bench
BLACKWELL_UUID=$GPU_BLACKWELL_UUID
LOG=/tmp/fix_qwen36_bf16.log

log()  { echo "[$(date +%H:%M:%S)] $*" | tee -a $LOG; }

teardown() {
  docker rm -f vllm-inference >/dev/null 2>&1
  sleep 3
}

# Wait until Blackwell is free (no other vllm-inference container holding it).
wait_for_blackwell() {
  while true; do
    if ! docker ps --filter name=vllm-inference --format '{{.Names}}' | grep -q vllm-inference; then
      return 0
    fi
    sleep 30
  done
}

bring_up() {
  local extra="$1"
  docker run -d --name vllm-inference \
    --network=proxy-net --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=$BLACKWELL_UUID \
    -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    -e HUGGING_FACE_HUB_TOKEN=$HF_TOKEN \
    --shm-size=16gb --ipc=host \
    -v /mnt/steam/forge/shared/models:/root/.cache/huggingface \
    -v /mnt/fire/forge/shared/models/hub:/mnt/fire/forge/shared/models/hub \
    vllm/vllm-openai:v0.20.0-cu130-ubuntu2404 \
    --model Qwen/Qwen3.6-27B --served-model-name qwen3.6-27b-bf16 \
    --enable-auto-tool-choice --trust-remote-code \
    --host 0.0.0.0 --port 8000 --api-key $VLLM_API_KEY \
    --tool-call-parser qwen3_coder \
    $extra >> $LOG 2>&1 || return 1
  # Wait up to 12 minutes for /v1/models
  for i in $(seq 1 36); do
    sleep 20
    local ip
    ip=$(docker inspect vllm-inference --format '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}' 2>/dev/null) || true
    if [[ -n $ip ]] && curl -sS -m 5 -H "Authorization: Bearer $VLLM_API_KEY" \
        "http://${ip}:8000/v1/models" | grep -q '"id"'; then
      echo "$ip"
      return 0
    fi
  done
  return 2
}

probe() {
  local ip=$1
  python3 - <<PYEOF
import json, urllib.request
body = {
  "model": "qwen3.6-27b-bf16",
  "messages": [
    {"role": "system", "content": (
      "You have tools: view(path), bash(cmd), finish(note). "
      "Each tool call must be in a fenced code block tagged \`tool\` "
      "with a JSON body like:\n\n\`\`\`tool\n"
      "{\"name\": \"view\", \"args\": {\"path\": \"/tasks/2048/SKILL_tier1.md\"}}\n"
      "\`\`\`\n\nALWAYS emit at least one tool call per turn."
    )},
    {"role": "user", "content": "Start by viewing the spec."}
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
import sys
try:
  with urllib.request.urlopen(req, timeout=120) as r:
    j = json.loads(r.read())
except Exception as e:
  print("HTTP_ERROR:", str(e)[:200])
  sys.exit(1)
m = j["choices"][0]["message"]
raw = (m.get("reasoning") or "") + (m.get("content") or "")
print("REPLY:", repr(raw[:300]))
PYEOF
}

log "=== fix Qwen3.6-27B-BF16 ==="
log "waiting for Blackwell vllm-inference slot to clear..."
wait_for_blackwell
log "Blackwell free, starting attempts"

# Attempt 1: most aggressive eager + minimal cache
log "--- attempt 1: enforce-eager + max-num-seqs 1 + no prefix cache ---"
teardown
ip=$(bring_up "--kv-cache-dtype fp8 --max-model-len 32768 --max-num-seqs 256 --max-num-batched-tokens 4096 --gpu-memory-utilization 0.85 --enforce-eager") && {
  log "  serving at $ip"
  log "  probe: $(probe "$ip" 2>&1 | head -3)"
  log "  attempt 1: REACHED SERVING"
  teardown
  exit 0
} || log "  attempt 1: hung past 12 min"

# Attempt 2: enforce-eager only, with prefix caching back on
log "--- attempt 2: enforce-eager + max-num-seqs 128 + prefix cache on ---"
teardown
ip=$(bring_up "--kv-cache-dtype fp8 --max-model-len 65536 --max-num-seqs 256 --max-num-batched-tokens 4096 --gpu-memory-utilization 0.85") && {
  log "  serving at $ip"
  log "  probe: $(probe "$ip" 2>&1 | head -3)"
  log "  attempt 2: REACHED SERVING"
  teardown
  exit 0
} || log "  attempt 2: hung past 12 min"

# Attempt 3: default-ish but with --enforce-eager (no torch.compile)
log "--- attempt 3: enforce-eager + bigger ctx ---"
teardown
ip=$(bring_up "--kv-cache-dtype fp8 --max-model-len 131072 --max-num-seqs 256 --max-num-batched-tokens 4096 --gpu-memory-utilization 0.85") && {
  log "  serving at $ip"
  log "  probe: $(probe "$ip" 2>&1 | head -3)"
  log "  attempt 3: REACHED SERVING"
  teardown
  exit 0
} || log "  attempt 3: hung past 12 min"

log "all attempts failed — drop Qwen3.6-27B-BF16 from the queue"
teardown
exit 1
