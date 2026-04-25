#!/usr/bin/env bash
# tests/synthetic/run.sh — TDD synthetic test for H-Q2 / H-Q5 / H-Q-plan.
#
# Usage:
#   ./run.sh                      # default: 4 sources, skill v2 (helper-tools)
#   ./run.sh --skill v1           # baseline: 4 sources, skill v1 (no helper-tools)
#   ./run.sh --sources 2          # legacy: only 2 sources
#
# Pre-stages 2 or 4 raw transcripts + a minimal wiki skill, mounts both
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

# --- arg parsing ---
SKILL=v2
SOURCES=4
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill) SKILL="${2:?}"; shift 2 ;;
    --sources) SOURCES="${2:?}"; shift 2 ;;
    -h|--help)
      sed -n '2,12p' "$0"; exit 0 ;;
    *)
      echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

case "$SKILL" in
  v1|v2) ;;
  *) echo "skill must be v1 or v2 (got: $SKILL)" >&2; exit 2 ;;
esac

# --- preflight ---
IMG="kurpatov-wiki-bench:${OPENHANDS_VERSION}"
docker image inspect "$IMG" >/dev/null 2>&1 || {
  echo "FATAL: image $IMG not built. Run 'make build' in $LAB_ROOT" >&2
  exit 2
}

served=$(curl -fsS "${INFERENCE_BASE_URL}/models" \
  -H "Authorization: Bearer ${VLLM_API_KEY}" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data') or [{}])[0].get('id',''))" 2>/dev/null \
  || echo "")
[[ -n "$served" ]] || { echo "FATAL: ${INFERENCE_BASE_URL}/models unreachable" >&2; exit 2; }
echo "[synth] served model: $served"
echo "[synth] skill: $SKILL"
echo "[synth] sources: $SOURCES"

# --- build synthetic workspace under /tmp ---
ts=$(date +"%Y-%m-%d-%H%M%S")
WORK="/tmp/synth-run-${SKILL}-${ts}"
mkdir -p "$WORK/raw" "$WORK/wiki" "$WORK/run"

# raw repo: 2 or 4 sources
SRC_DIRS=()
case "$SOURCES" in
  2)
    SRC_DIRS+=("001 Парето и Мур" "002 Парето и Эверест")
    SRC_FILES=("001.json" "002.json")
    ;;
  4)
    SRC_DIRS+=("001 Парето и Мур" "002 Парето и Эверест" "003 Мур и Сатурн" "004 Эверест и Пи")
    SRC_FILES=("001.json" "002.json" "003.json" "004.json")
    ;;
  *) echo "sources must be 2 or 4" >&2; exit 2 ;;
esac

for i in "${!SRC_DIRS[@]}"; do
  dir="$WORK/raw/data/ТестКурс/999 Тестовый модуль/${SRC_DIRS[$i]}"
  mkdir -p "$dir"
  cp "$HERE/fixtures/raw/${SRC_FILES[$i]}" "$dir/raw.json"
done

( cd "$WORK/raw" \
  && git init -q -b main \
  && git -c user.email=synth@test.local -c user.name=synth add -A \
  && git -c user.email=synth@test.local -c user.name=synth commit -qm "synth raw" )

# wiki repo: skill (v1 or v2) + helper scripts (only for v2) + empty data
mkdir -p "$WORK/wiki/skills/synth-benchmark/scripts" \
         "$WORK/wiki/data/sources" \
         "$WORK/wiki/data/concepts"

case "$SKILL" in
  v1) cp "$HERE/fixtures/wiki/SKILL.md"   "$WORK/wiki/skills/synth-benchmark/SKILL.md" ;;
  v2) cp "$HERE/fixtures/wiki/SKILL-v2.md" "$WORK/wiki/skills/synth-benchmark/SKILL.md"
      cp "$HERE/fixtures/wiki/scripts/get_known_claims.py" \
         "$WORK/wiki/skills/synth-benchmark/scripts/get_known_claims.py"
      cp "$HERE/fixtures/wiki/scripts/factcheck.py" \
         "$WORK/wiki/skills/synth-benchmark/scripts/factcheck.py"
      chmod +x "$WORK/wiki/skills/synth-benchmark/scripts/"*.py
      ;;
esac

cat > "$WORK/wiki/data/concept-index.json" <<'EOF'
{
  "processed_sources": [],
  "concepts": {}
}
EOF

( cd "$WORK/wiki" \
  && git init -q -b main \
  && git -c user.email=synth@test.local -c user.name=synth add -A \
  && git -c user.email=synth@test.local -c user.name=synth commit -qm "synth wiki seed (skill=$SKILL, sources=$SOURCES)" )

# --- prepare launch prompt ---
case "$SKILL" in
  v1) launch="$HERE/fixtures/launch.md" ;;
  v2) launch="$HERE/fixtures/launch-v2.md" ;;
esac
task=$(sed "s|__SERVED__|$served|g" "$launch")

# --- run agent (one shot) ---
echo "[synth] launching agent (max ~10 min for 4-source v2)..."
set +e
docker run --rm \
  --name "synth-test-${SKILL}-${ts}" \
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
echo "Assertions (skill=$SKILL, sources=$SOURCES):"
echo "================================================================"
python3 "$HERE/assert.py" "$WORK/run" "$WORK/wiki" "$served" "$SKILL" "$SOURCES"
assert_rc=$?

echo ""
echo "[synth] full artifacts under: $WORK"
exit $assert_rc
