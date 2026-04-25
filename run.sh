#!/usr/bin/env bash
# kurpatov-wiki-bench/run.sh — one bench run, sandboxed in Docker.
#
# Architecture (v4):
#   - The OpenHands CLI runs INSIDE a Docker container we build
#     ourselves (Dockerfile in this repo). The agent sees only
#     /workspace (its own scratch) and /runs/current (output).
#     The host's $HOME, ~/.ssh, ~/.config/gh, ~/forge, and the
#     docker socket are NOT mounted; the agent cannot reach them.
#   - Inference is delegated to forge/inference (vLLM behind caddy)
#     over the public TLS endpoint. Same path Hermes Agent would use.
#   - Per-run artifacts under ${STORAGE_ROOT}/kurpatov-wiki-bench/
#     runs/<run_id>/.
#
# Usage:
#   ./run.sh                                 # uses .env defaults
#   INFERENCE_SERVED_NAME=qwen3-32b ./run.sh # override per invocation
#
# Pre-reqs:
#   - .env populated (copy from .env.example, fill VLLM_API_KEY).
#   - bin/openhands present (curl per README).
#   - Image built (`make build`).

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# --- load .env ---
[[ -f .env ]] || { echo "FATAL: .env not found. Copy .env.example to .env." >&2; exit 2; }
set -a; source .env; set +a

: "${STORAGE_ROOT:?must be set}"
: "${INFERENCE_BASE_URL:?must be set}"
: "${VLLM_API_KEY:?must be set}"
: "${INFERENCE_SERVED_NAME:?must be set}"
: "${OPENHANDS_VERSION:?must be set}"
: "${WIKI_REPO_URL:?must be set}"
: "${RAW_REPO_URL:?must be set}"
: "${SANDBOX_MEMORY:=16g}"
: "${SANDBOX_CPUS:=4}"
: "${SANDBOX_PIDS:=256}"

IMAGE_TAG="kurpatov-wiki-bench:${OPENHANDS_VERSION}"

# --- gh token (host-side; passed into container as env) ---
command -v gh >/dev/null 2>&1 || { echo "FATAL: gh CLI not installed." >&2; exit 2; }
GITHUB_TOKEN=$(gh auth token 2>/dev/null) || { echo "FATAL: gh auth token failed. Run 'gh auth login'." >&2; exit 2; }

# --- preflight: image present? ---
if ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
  echo "FATAL: image $IMAGE_TAG not found. Run 'make build' first." >&2
  exit 2
fi

# --- preflight: vLLM up + serving expected model ---
served=$(curl -fsS "${INFERENCE_BASE_URL}/models" -H "Authorization: Bearer ${VLLM_API_KEY}" | jq -r '.data[0].id')
if [[ "$served" != "$INFERENCE_SERVED_NAME" ]]; then
  echo "FATAL: vLLM serves '$served' but .env expects '$INFERENCE_SERVED_NAME'." >&2
  exit 3
fi
echo "[preflight] OK — vLLM serves '$served'"

# --- run id + dir on STORAGE_ROOT ---
ts=$(date +"%Y-%m-%d-%H%M%S")
slug=$(echo "$INFERENCE_SERVED_NAME" | tr '/' '-')
run_id="${ts}-${slug}"
runs_root="${STORAGE_ROOT}/kurpatov-wiki-bench/runs"
mkdir -p "$runs_root"
run_dir="${runs_root}/${run_id}"
mkdir -p "$run_dir"
echo "[run] run_id=$run_id"
echo "[run] dir   =$run_dir"

curl -fsS "${INFERENCE_BASE_URL}/models" -H "Authorization: Bearer ${VLLM_API_KEY}" > "${run_dir}/vllm-snapshot-start.json"

# --- task prompt: launch.md + GitHub token for git push ---
task_template=$(cat prompts/launch.md | sed "s|__INFERENCE_SERVED_NAME__|$INFERENCE_SERVED_NAME|g")
task=$(printf '%s\n\nGITHUB_TOKEN for HTTPS git push (use as the password with username "x-access-token"): %s\n' "$task_template" "$GITHUB_TOKEN")

started_at=$(date -Iseconds)

# --- launch sandboxed ---
# Mounts:
#   ${run_dir}:/runs/current  — the only bridge between agent and host
# Env:
#   LLM_BASE_URL, LLM_API_KEY, LLM_MODEL — what OpenHands uses to call vLLM
# Resource caps:
#   --memory, --cpus, --pids-limit per .env
# What's deliberately NOT here:
#   -v /var/run/docker.sock      (no docker-in-docker escape)
#   -v $HOME, -v ~/.ssh, etc.    (no host filesystem access)
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
  -e LLM_MODEL="openai/$INFERENCE_SERVED_NAME" \
  -e OPENHANDS_SUPPRESS_BANNER=1 \
  "$IMAGE_TAG" \
  --headless --json --always-approve --override-with-envs -t "$task" \
  > "${run_dir}/events.jsonl" 2> "${run_dir}/stderr.log"
exit_code=$?
set -e

finished_at=$(date -Iseconds)

curl -fsS "${INFERENCE_BASE_URL}/models" -H "Authorization: Bearer ${VLLM_API_KEY}" > "${run_dir}/vllm-snapshot-end.json" || true

# --- post-run: did the agent push a branch? ---
expected_branch="bench/$(date +%Y-%m-%d)-${slug}"
branch_pushed="unknown"
commits_on_branch=0

auth_url="${WIKI_REPO_URL/https:\/\//https:\/\/x-access-token:$GITHUB_TOKEN@}"
if git ls-remote --exit-code --heads "$auth_url" "$expected_branch" >/dev/null 2>&1; then
  branch_pushed="$expected_branch"
  tmp_clone=$(mktemp -d)
  git clone --depth 50 --branch "$expected_branch" "$auth_url" "$tmp_clone" >/dev/null 2>&1 || true
  if [[ -d "$tmp_clone/.git" ]]; then
    commits_on_branch=$(git -C "$tmp_clone" log --oneline main.."$expected_branch" 2>/dev/null | wc -l)
    commits_on_branch=${commits_on_branch:-0}
    commits_on_branch=${commits_on_branch// /}
    [[ -f "$tmp_clone/bench-report.md" ]] && cp "$tmp_clone/bench-report.md" "${run_dir}/bench-report.md"
  fi
  rm -rf "$tmp_clone"
fi

# --- summary.json ---
jq -n \
  --arg run_id "$run_id" \
  --arg started_at "$started_at" \
  --arg finished_at "$finished_at" \
  --arg base_url "$INFERENCE_BASE_URL" \
  --arg served_name "$INFERENCE_SERVED_NAME" \
  --arg openhands_version "$OPENHANDS_VERSION" \
  --argjson exit_code "$exit_code" \
  --arg branch_pushed "$branch_pushed" \
  --argjson commits_on_branch "$commits_on_branch" \
  --arg sandbox_memory "$SANDBOX_MEMORY" \
  --arg sandbox_cpus "$SANDBOX_CPUS" \
  --arg sandbox_pids "$SANDBOX_PIDS" \
  --arg image "$IMAGE_TAG" \
  '{
    run_id: $run_id,
    started_at: $started_at,
    finished_at: $finished_at,
    inference: { base_url: $base_url, served_name: $served_name },
    sandbox: {
      image: $image,
      memory: $sandbox_memory,
      cpus: $sandbox_cpus,
      pids_limit: $sandbox_pids
    },
    openhands_version: $openhands_version,
    exit_code: $exit_code,
    wiki: { branch_pushed: $branch_pushed, commits_on_branch: $commits_on_branch }
  }' > "${run_dir}/summary.json"

echo
echo "=================================================="
echo "[run] done. exit=$exit_code  branch=$branch_pushed  commits=$commits_on_branch"
echo "[run] dir=$run_dir"
echo "=================================================="
exit "$exit_code"
