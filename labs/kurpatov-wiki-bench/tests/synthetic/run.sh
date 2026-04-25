#!/usr/bin/env bash
# tests/synthetic/run.sh — TDD synthetic test for harness capabilities
# (H-Q2: web search; H-Q5: prior-source reading).
#
# Pre-stages two raw transcripts + a minimal wiki skill, mounts both
# into the bench docker container, runs the OpenHands agent, captures
# events.jsonl + final wiki state, then runs assertions.

set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
FORGE_ROOT=$(git -C "$HERE" rev-parse --show-toplevel)
LAB_ROOT=$(cd -- "$HERE/.." &>/dev/null && pwd)

set -a; source "$FORGE_ROOT/.env"; set +a

: "${INFERENCE_BASE_URL:?must be set}"
: "${VLLM_API_KEY:?must be set}"
: "${OPENHANDS_VERSION:?must be set}"

# --- preflight: image present ---
IMG="kurpatov-wiki-bench:${OPENHANDS_VERSION}"
docker image inspect "$IMG" >/dev/null 2>&1 || {
  echo "FATAL: image $IMG not built. Run 'make build' in $LAB_ROOT" >&2
  exit 2
}

# --- preflight: compiler is up + serves something ---
served=$(curl -fsS "${INFERENCE_BASE_URL}/models" \
  -H "Authorization: Bearer ${VLLM_API_KEY}" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data') or [{}])[0].get('id',''))" 2>/dev/null \
  || echo "")
[[ -n "$served" ]] || { echo "FATAL: ${INFERENCE_BASE_URL}/models unreachable" >&2; exit 2; }
echo "[synth] served model: $served"

# --- build synthetic workspace under /tmp ---
ts=$(date +"%Y-%m-%d-%H%M%S")
WORK="/tmp/synth-run-${ts}"
mkdir -p "$WORK/raw" "$WORK/wiki" "$WORK/run"

# raw repo
mkdir -p "$WORK/raw/data/ТестКурс/999 Тестовый модуль/001 Парето и Мур" \
         "$WORK/raw/data/ТестКурс/999 Тестовый модуль/002 Парето и Эверест"
cp "$HERE/fixtures/raw/001.json" \
   "$WORK/raw/data/ТестКурс/999 Тестовый модуль/001 Парето и Мур/raw.json"
cp "$HERE/fixtures/raw/002.json" \
   "$WORK/raw/data/ТестКурс/999 Тестовый модуль/002 Парето и Эверест/raw.json"
( cd "$WORK/raw" \
  && git init -q -b main \
  && git -c user.email=synth@test.local -c user.name=synth add -A \
  && git -c user.email=synth@test.local -c user.name=synth commit -qm "synth raw" )

# wiki repo
mkdir -p "$WORK/wiki/skills/synth-benchmark" \
         "$WORK/wiki/data/sources" \
         "$WORK/wiki/data/concepts"
cp "$HERE/fixtures/wiki/SKILL.md" "$WORK/wiki/skills/synth-benchmark/SKILL.md"
cat > "$WORK/wiki/data/concept-index.json" <<'EOF'
{
  "processed_sources": [],
  "concepts": {}
}
EOF
( cd "$WORK/wiki" \
  && git init -q -b main \
  && git -c user.email=synth@test.local -c user.name=synth add -A \
  && git -c user.email=synth@test.local -c user.name=synth commit -qm "synth wiki seed" )

# --- prepare launch prompt ---
task=$(sed "s|__SERVED__|$served|g" "$HERE/fixtures/launch.md")

# --- run agent (one shot) ---
echo "[synth] launching agent (max ~3 min)..."
set +e
docker run --rm \
  --name "synth-test-${ts}" \
  --network bridge \
  --memory 16g \
  --cpus 4 \
  --pids-limit 256 \
  -v "$WORK/raw:/workspace/raw:rw" \
  -v "$WORK/wiki:/workspace/wiki:rw" \
  -v "$WORK/run:/runs/current:rw" \
  -e LLM_BASE_URL="$INFERENCE_BASE_URL" \
  -e LLM_API_KEY="$VLLM_API_KEY" \
  -e LLM_MODEL="openai/$served" \
  -e OPENHANDS_SUPPRESS_BANNER=1 \
  "$IMG" \
  --headless --json --always-approve --override-with-envs -t "$task" \
  > "$WORK/run/events.jsonl" 2> "$WORK/run/stderr.log"
exit_code=$?
set -e

echo "[synth] agent exit_code=$exit_code"
echo "[synth] events: $WORK/run/events.jsonl ($(wc -l < $WORK/run/events.jsonl 2>/dev/null) lines)"
echo "[synth] wiki final: $WORK/wiki"
echo ""
echo "================================================================"
echo "Assertions:"
echo "================================================================"
python3 "$HERE/assert.py" "$WORK/run" "$WORK/wiki" "$served"
assert_rc=$?

echo ""
echo "[synth] full artifacts under: $WORK"
exit $assert_rc
