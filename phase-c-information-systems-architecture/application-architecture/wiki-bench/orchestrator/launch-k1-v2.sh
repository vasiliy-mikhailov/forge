#!/bin/bash
# K1 v2 — clean restart from skill-v2 HEAD, modules 000+001.
#
# Prerequisites verified by this script:
#   - K1 v1 has been stopped (no other bench-image container running)
#   - Orchestrator has the NFC/NFD HAZARD prompt (commit 1e0a882)
#   - Orchestrator enforces ADR 0012 (commit 50f66e5)
#   - E2E #2 has been re-run green (operator-confirmed)
#
# Policy:
#   D8_PILOT_FAIL_POLICY=fail_fast (the post-ADR-0012 default).
#   If a verify-fail happens, the orchestrator exits with the error.
#   This is by design: any verify-fail in K1 v2 means there is a NEW
#   bug we have not yet surfaced, and we want to know within minutes
#   instead of hours.
#
#   If you EXPLICITLY accept the risk of partial progress (operator
#   override), pass FAIL_POLICY=continue as env var to this script.
#   The orchestrator will write skipped_sources.json + WIKI INCOMPLETE
#   banner + non-zero exit on completion.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_ROOT="$(cd "$HERE/../../../.." && pwd)"

# Source forge .env for LLM credentials + GH_TOKEN.
set -a; source "$FORGE_ROOT/.env"; set +a

WORKSPACE=/tmp/k1-v2-pilot
BRANCH="experiment/K1-v2-$(date +%Y-%m-%d)-modules-000-001-qwen3.6-27b-fp8-nfc"
FAIL_POLICY="${FAIL_POLICY:-fail_fast}"

echo "=== K1 v2 — clean restart, NFC/NFD-fixed agent + ADR 0012 enforcement ==="
echo "  branch        = $BRANCH"
echo "  workspace     = $WORKSPACE"
echo "  fail_policy   = $FAIL_POLICY"
echo "  modules       = 000 + 001"
echo "  expected wall = ~12 hours"
echo

# Pre-flight: confirm no other bench container is running on this host.
RUNNING=$(docker ps --filter "ancestor=kurpatov-wiki-bench:1.17.0-d8-cal" -q | wc -l)
if [ "$RUNNING" -ne 0 ]; then
    echo "ABORT: $RUNNING bench-image container(s) already running:"
    docker ps --filter "ancestor=kurpatov-wiki-bench:1.17.0-d8-cal"
    exit 2
fi

# Wipe any prior K1 v2 attempt's workspace via docker (handles root-owned files).
docker run --rm -v /tmp:/host_tmp ubuntu:24.04 \
  rm -rf "/host_tmp/$(basename $WORKSPACE)" 2>/dev/null || true
mkdir -p "$WORKSPACE"

# Rebuild bench image with whatever orchestrator scripts are at HEAD on the
# host. Layer caching makes this seconds when only Python files changed
# (apt+pip+e5-base download are all cached). The image is the single source
# of truth; we do NOT bind-mount scripts over it. See phase-g-…/adr/0012-…
echo "=== rebuilding bench image (Docker layer cache makes this seconds) ==="
( cd "$FORGE_ROOT/phase-c-information-systems-architecture/application-architecture/wiki-bench" \
  && docker build -t kurpatov-wiki-bench:1.17.0-d8-cal . > /tmp/bench-build.log 2>&1 \
  && tail -3 /tmp/bench-build.log )

docker run --rm \
  --name k1-v2-pilot \
  --network proxy-net \
  --entrypoint python3 \
  -e D8_PILOT_WORKDIR=/workspace \
  -e D8_PILOT_FAIL_POLICY="$FAIL_POLICY" \
  -e D8_PILOT_COURSE="Психолог-консультант" \
  -e D8_PILOT_MODULES="000 Путеводитель по программе|001 Глубинная психология и психодиагностика в консультировании" \
  -e D8_PILOT_BRANCH="$BRANCH" \
  -e ORCH_DIR=/opt/forge \
  -e LC_ALL=C.UTF-8 -e LANG=C.UTF-8 \
  -e LLM_BASE_URL="${INFERENCE_BASE_URL:-https://inference.mikhailov.tech/v1}" \
  -e LLM_API_KEY="$VLLM_API_KEY" \
  -e LLM_MODEL="openai/qwen3.6-27b-fp8" \
  -e GITHUB_TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}" \
  -v "$WORKSPACE:/workspace" \
  kurpatov-wiki-bench:1.17.0-d8-cal \
  /opt/forge/run-d8-pilot.py
EXIT=$?

echo
echo "=== K1 v2 exit: $EXIT ==="
echo "  branch: $BRANCH"
echo "  wiki at: $WORKSPACE/wiki"
if [ -f "$WORKSPACE/skipped_sources.json" ]; then
    echo "  skipped_sources.json present:"
    cat "$WORKSPACE/skipped_sources.json"
fi
exit $EXIT
