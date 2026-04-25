#!/usr/bin/env bash
# kurpatov-wiki-bench/run.sh — one bench run, sandboxed in Docker.
#
# Architecture (v5, post-ADR-0008):
#   - The OpenHands CLI runs INSIDE a Docker container we build
#     ourselves (Dockerfile in this repo). The agent sees only
#     /workspace (its own scratch) and /runs/current (output).
#     The host's $HOME, ~/.ssh, ~/.config/gh, ~/forge, and the
#     docker socket are NOT mounted; the agent cannot reach them.
#   - Inference is delegated to the kurpatov-wiki-compiler lab
#     (vLLM behind caddy) over the public TLS endpoint.
#   - The active model is determined by the compiler lab — bench reads
#     the served_name from `/v1/models` rather than from .env, so a
#     .env / compiler drift fails preflight here, not silently.
#   - Per-experiment artifacts under
#     ${STORAGE_ROOT}/labs/kurpatov-wiki-bench/experiments/<run_id>/.
#
# Usage:
#   ./run.sh
#
# Pre-reqs:
#   - forge/.env populated (VLLM_API_KEY, GITHUB_TOKEN via gh, etc.).
#   - Compiler lab up (`make kurpatov-wiki-compiler` from forge root).
#   - bin/openhands present.
#   - Image built (`make build`).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

FORGE_ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "$FORGE_ROOT" || ! -f "$FORGE_ROOT/.env" ]]; then
  echo "FATAL: cannot locate forge/.env (run from inside the forge repo)." >&2
  exit 2
fi
set -a; source "$FORGE_ROOT/.env"; [[ -f .env ]] && source .env; set +a

: "${STORAGE_ROOT:?must be set}"
: "${INFERENCE_BASE_URL:?must be set}"
: "${VLLM_API_KEY:?must be set}"
: "${EXPERIMENTS_ROOT:=$STORAGE_ROOT/labs/kurpatov-wiki-bench/experiments}"
: "${OPENHANDS_VERSION:?must be set}"
: "${WIKI_REPO_URL:?must be set}"
: "${RAW_REPO_URL:?must be set}"
: "${SANDBOX_MEMORY:=16g}"
: "${SANDBOX_CPUS:=4}"
: "${SANDBOX_PIDS:=256}"

IMAGE_TAG="kurpatov-wiki-bench:${OPENHANDS_VERSION}"

command -v gh >/dev/null 2>&1 || { echo "FATAL: gh CLI not installed." >&2; exit 2; }
GITHUB_TOKEN=$(gh auth token 2>/dev/null) || { echo "FATAL: gh auth token failed. Run 'gh auth login'." >&2; exit 2; }

if ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
  echo "FATAL: image $IMAGE_TAG not found. Run 'make build' first." >&2
  exit 2
fi

# --- preflight: vLLM up + resolve actually-served name ---
served=$(curl -fsS "${INFERENCE_BASE_URL}/models" \
  -H "Authorization: Bearer ${VLLM_API_KEY}" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data') or [{}])[0].get('id',''))" 2>/dev/null \
  || echo "")
if [[ -z "$served" ]]; then
  echo "FATAL: ${INFERENCE_BASE_URL}/models is unreachable or returned no model." >&2
  echo "       Bring up the compiler lab first: make kurpatov-wiki-compiler" >&2
  exit 3
fi
echo "[preflight] OK — vLLM serves '$served'"

# --- consistency check: registry says active model should serve $served? ---
ACTIVE_ID=$(grep -E '^INFERENCE_ACTIVE_MODEL_ID=' "$FORGE_ROOT/.env" | head -1 | cut -d= -f2- || echo "")
if [[ -n "$ACTIVE_ID" ]]; then
  expected=$(python3 - "$FORGE_ROOT/labs/kurpatov-wiki-compiler/configs/models.yml" "$ACTIVE_ID" <<'PY' 2>/dev/null || true
import sys, yaml
data = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
m = next((x for x in data["models"] if x["id"] == sys.argv[2]), None)
print(m["served_name"] if m else "")
PY
)
  if [[ -n "$expected" && "$served" != "$expected" ]]; then
    echo "FATAL: drift — INFERENCE_ACTIVE_MODEL_ID=$ACTIVE_ID expects '$expected', vLLM serves '$served'." >&2
    echo "       Re-run: make kurpatov-wiki-compiler-down && make kurpatov-wiki-compiler" >&2
    exit 3
  fi
fi

# --- run id + dir on STORAGE_ROOT ---
ts=$(date +"%Y-%m-%d-%H%M%S")
slug=$(echo "$served" | tr '/' '-')
run_id="${ts}-${slug}"
runs_root="$EXPERIMENTS_ROOT"
mkdir -p "$runs_root"
run_dir="${runs_root}/${run_id}"
mkdir -p "$run_dir"
echo "[run] run_id=$run_id"
echo "[run] dir   =$run_dir"

curl -fsS "${INFERENCE_BASE_URL}/models" -H "Authorization: Bearer ${VLLM_API_KEY}" > "${run_dir}/vllm-snapshot-start.json"

# --- task prompt: launch.md + GitHub token for git push, model name from /v1/models ---
task_template=$(cat "${LAUNCH_PROMPT:-prompts/launch.md}" | sed "s|__INFERENCE_SERVED_NAME__|$served|g")
task=$(printf '%s\n\nGITHUB_TOKEN for HTTPS git push (use as the password with username "x-access-token"): %s\n' "$task_template" "$GITHUB_TOKEN")

started_at=$(date -Iseconds)

set +e
docker run --rm \
  --name "bench-${run_id}" \
  --network bridge \
  --memory "$SANDBOX_MEMORY" \
  --cpus "$SANDBOX_CPUS" \
  --pids-limit "$SANDBOX_PIDS" \
  -v "${run_dir}:/runs/current:rw" \
  -e LLM_BASE_URL="$INFERENCE_BASE_URL" \
  -e LLM_API_KEY="$VLLM_API_KEY" \
  -e LLM_MODEL="openai/$served" \
  -e OPENHANDS_SUPPRESS_BANNER=1 \
  "$IMAGE_TAG" \
  --headless --json --always-approve --override-with-envs -t "$task" \
  > "${run_dir}/events.jsonl" 2> "${run_dir}/stderr.log"
exit_code=$?
set -e

finished_at=$(date -Iseconds)

curl -fsS "${INFERENCE_BASE_URL}/models" -H "Authorization: Bearer ${VLLM_API_KEY}" > "${run_dir}/vllm-snapshot-end.json" || true

# --- post-run: did the agent push a branch? ---
branch_pushed="bench/$(date +%Y-%m-%d)-${slug}"
commits_on_branch=$(git ls-remote --heads "${WIKI_REPO_URL}" "$branch_pushed" 2>/dev/null | wc -l)

# --- summary.json ---
jq -n \
  --arg run_id "$run_id" \
  --arg served "$served" \
  --arg active_id "$ACTIVE_ID" \
  --arg started_at "$started_at" \
  --arg finished_at "$finished_at" \
  --arg openhands_version "$OPENHANDS_VERSION" \
  --argjson exit_code "$exit_code" \
  --arg branch_pushed "$branch_pushed" \
  --argjson commits_on_branch "$commits_on_branch" \
  '{
    run_id: $run_id,
    served_name: $served,
    active_model_id: $active_id,
    started_at: $started_at,
    finished_at: $finished_at,
    openhands_version: $openhands_version,
    exit_code: $exit_code,
    wiki: { branch_pushed: $branch_pushed, commits_on_branch: $commits_on_branch }
  }' > "${run_dir}/summary.json"

echo "[run] exit_code=$exit_code"
echo "[run] summary: ${run_dir}/summary.json"
exit $exit_code
