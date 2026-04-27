#!/usr/bin/env bash
# Smoke for kurpatov-wiki-bench lab.
#
# Source of truth: smoke.md (this dir).
#
# Bench is a one-shot agent harness, not a service. This smoke is
# static / pre-flight: image built, OpenHands binary present, GitHub
# auth works, compiler endpoint reachable.
#
# Bench is co-runnable with kurpatov-wiki-compiler (compiler is its
# inference endpoint). Unlike the other lab smokes, bench's smoke
# does NOT require its own caddy to be up (bench has no caddy).

set -u
set -o pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
FORGE_ROOT=$(git -C "$HERE" rev-parse --show-toplevel)

if [[ ! -f "$FORGE_ROOT/.env" ]]; then
  echo "ERROR: $FORGE_ROOT/.env not found" >&2
  exit 2
fi
set -a; . "$FORGE_ROOT/.env"; set +a
[[ -f "$FORGE_ROOT/labs/kurpatov-wiki-bench/.env" ]] && set -a && \
  . "$FORGE_ROOT/labs/kurpatov-wiki-bench/.env" && set +a

. "$FORGE_ROOT/scripts/smoke-lib.sh"

require_env OPENHANDS_VERSION INFERENCE_BASE_URL VLLM_API_KEY INFERENCE_SERVED_NAME

# ---------- 1. OpenHands CLI binary present ----------
section "OpenHands binary"
bench_dir="$FORGE_ROOT/labs/kurpatov-wiki-bench"
if [[ -x "$bench_dir/bin/openhands" ]]; then
  pass "bin/openhands exists and is executable"
else
  fail "bin/openhands missing or not executable (see README → 'Install the CLI binary')"
fi

# ---------- 2. Bench docker image built ----------
section "bench image"
img_tag="kurpatov-wiki-bench:${OPENHANDS_VERSION}"
if docker image inspect "$img_tag" >/dev/null 2>&1; then
  pass "image $img_tag built"
else
  fail "image $img_tag not built (run 'make build' in bench dir)"
fi

# ---------- 3. GitHub auth ----------
section "GitHub auth"
if command -v gh >/dev/null 2>&1; then
  if gh auth token >/dev/null 2>&1; then
    pass "gh auth token works (used to authenticate git push from sandbox)"
  else
    fail "gh CLI installed but 'gh auth token' fails — run 'gh auth login'"
  fi
else
  fail "gh CLI not installed (required by bench/run.sh for GitHub push auth)"
fi

# ---------- 4. compiler endpoint reachable + serving expected model ----------
section "compiler preflight"
served=$(curl -fsS --max-time 8 \
  "${INFERENCE_BASE_URL}/models" \
  -H "Authorization: Bearer ${VLLM_API_KEY}" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data')or[{}])[0].get('id',''))" 2>/dev/null || echo "")

if [[ -z "$served" ]]; then
  fail "compiler endpoint ${INFERENCE_BASE_URL} unreachable (is kurpatov-wiki-compiler lab up?)"
elif [[ "$served" == "$INFERENCE_SERVED_NAME" ]]; then
  pass "compiler serves '$served' (matches INFERENCE_SERVED_NAME)"
else
  fail "compiler serves '$served' but .env expects '$INFERENCE_SERVED_NAME' (model swap drift)"
fi

summary_and_exit
