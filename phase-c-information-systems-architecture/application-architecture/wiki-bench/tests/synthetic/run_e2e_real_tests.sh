#!/bin/bash
# E2E test #2 — production orchestrator on REAL raw.json (compacted) data.
#
# Goal: bridge the synth/production reproducibility gap captured in
# ADR 0010 + the K1 silent-skip incident. Run the FULL production
# orchestrator (run-d8-pilot.py with D8_PILOT_SKIP_CLONE=1) inside the
# bench container against a fixture of 4 compacted real raw.json sources.
#
# If verify-fail reproduces here, the bug is data-shape-driven.
# If not, the bug is long-running-state-driven (heap/fd/dentry).
#
# Per ADR 0012 (no silent skip): we use D8_PILOT_FAIL_POLICY=continue
# to OBSERVE every verify outcome, but the test runner asserts on the
# manifest at the end. Skip count > 0 is a TEST FAILURE, not a pass.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(cd "$HERE/../../../../.." && pwd)"
ORCHESTRATOR_DIR="$FORGE_ROOT/phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator"

# Source forge .env for LLM credentials + GH_TOKEN (commit_and_push uses gh).
set -a; source "$FORGE_ROOT/.env"; set +a

WORKSPACE=/tmp/e2e-real-workspace

echo "=== building fixture on host ==="
python3 "$HERE/build_e2e_real_fixture.py" --fixture-root "$WORKSPACE"

echo
echo "=== running orchestrator inside bench container ==="
echo "  course  = Психолог-консультант"
echo "  module  = 001 …"
echo "  policy  = continue (P6: surfaces every skip)"
echo "  workdir = /workspace (= host $WORKSPACE)"
echo

# Fix permissions so the container's user (whatever it is) can write
# under /workspace. The fixture builder ran as the host user.
chmod -R a+rwX "$WORKSPACE"

docker run --rm \
  --network proxy-net \
  --entrypoint python3 \
  -e D8_PILOT_WORKDIR=/workspace \
  -e D8_PILOT_SKIP_CLONE=1 \
  -e D8_PILOT_FAIL_POLICY=continue \
  -e D8_PILOT_COURSE="Психолог-консультант" \
  -e D8_PILOT_MODULES="001 Глубинная психология и психодиагностика в консультировании" \
  -e D8_PILOT_BRANCH="e2e-real-test" \
  -e D8_PILOT_SOURCES_LIMIT=4 \
  -e ORCH_DIR=/opt/forge \
  -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 \
  -e LLM_BASE_URL="${INFERENCE_BASE_URL:-https://inference.mikhailov.tech/v1}" \
  -e LLM_API_KEY="$VLLM_API_KEY" \
  -e LLM_MODEL="openai/qwen3.6-27b-fp8" \
  -e GITHUB_TOKEN="${GITHUB_TOKEN:-}" \
  -v "$WORKSPACE:/workspace" \
  -v "$ORCHESTRATOR_DIR/run-d8-pilot.py:/opt/forge/run-d8-pilot.py" \
  -v "$ORCHESTRATOR_DIR/embed_helpers.py:/opt/forge/embed_helpers.py" \
  kurpatov-wiki-bench:1.17.0-d8-cal \
  /opt/forge/run-d8-pilot.py

echo
echo "=== orchestrator exit code: $? ==="
echo
echo "=== verify outcomes ==="
echo "wiki commits added during run:"
( cd "$WORKSPACE/wiki" && git log --oneline skill-v2..HEAD 2>/dev/null || git log --oneline -10 )
echo
echo "source.md files written:"
find "$WORKSPACE/wiki/data/sources" -name "*.md" 2>/dev/null | wc -l
echo
echo "(if D8_PILOT_FAIL_POLICY=continue surfaces N skipped sources, the"
echo " bug reproduced; if all 4 verified ok, the bug is state-pressure-"
echo " driven and the next layer is N=20 sequential agents in one process.)"
