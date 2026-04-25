# kurpatov-wiki-bench

Server-side, Docker-sandboxed agent harness for benchmarking
open-weight models on the
[`kurpatov-wiki-wiki/skills/benchmark/SKILL.md`](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/blob/main/skills/benchmark/SKILL.md)
authoring task.

One `make bench` invocation runs an [OpenHands](https://github.com/OpenHands/OpenHands)
agent inside an isolated Docker container against whatever model the
local vLLM endpoint is currently serving. Per-run artifacts (event
trace + summary + the bench branch the agent pushed) land under
`${STORAGE_ROOT}/labs/kurpatov-wiki-bench/experiments/<run_id>/`.

This used to be a standalone repo; as of forge ADR 0007 it lives at `labs/kurpatov-wiki-bench/` inside forge alongside the other labs (compiler, ingest, rl-2048).

forge is the lab infrastructure (vLLM, MLflow, rl-2048, caddy); this
repo is one specific evaluation pipeline that consumes forge as a
black box.

## Architecture in one paragraph

The agent runs inside `kurpatov-wiki-bench:${OPENHANDS_VERSION}`, a
~400 MB image we build ourselves (`Dockerfile`). It cannot see the
host's home directory, SSH keys, gh token store, forge, or the
docker socket — only its own `/workspace` scratch and a single
`/runs/current` bind mount that surfaces artifacts back. It reaches
vLLM via `https://inference.mikhailov.tech` (the same TLS path any
external client takes). GitHub auth is the host's `gh` token, passed
into the container as `GITHUB_TOKEN` env. Resource caps:
`--memory 16g --cpus 4 --pids-limit 256`, all configurable in
`.env`. Full design: [`SPEC.md`](SPEC.md). Sandbox + storage rationale:
[`docs/adr/0002`](docs/adr/0002-docker-sandbox-and-storage-root.md).

## Quick start

```bash
# 1. Configure.
cp .env.example .env
$EDITOR .env       # set VLLM_API_KEY (from forge/.env), confirm INFERENCE_SERVED_NAME

# 2. Install the OpenHands CLI binary (gitignored at 85 MB).
mkdir -p bin
curl -fsSL -o bin/openhands \
  https://github.com/OpenHands/OpenHands-CLI/releases/download/${OPENHANDS_VERSION:-1.17.0}/openhands-linux-x86_64
chmod +x bin/openhands

# 3. Build the image.
make build

# 4. Initialize the storage dir under STORAGE_ROOT.
make storage-init

# 5. Confirm vLLM is up + serving the expected model.
make preflight

# 6. Run.
make bench
```

## Per-run output

```
${STORAGE_ROOT}/labs/kurpatov-wiki-bench/experiments/<run_id>/
├── events.jsonl              — OpenHands event trace
├── stderr.log                — container stderr
├── summary.json              — {run_id, model, sandbox config, exit_code, branch_pushed, ...}
├── vllm-snapshot-start.json  — /v1/models at run start
├── vllm-snapshot-end.json    — /v1/models at run end
└── bench-report.md           — fetched from the wiki branch the agent pushed (if it got that far)
```

`run_id` = `<YYYY-MM-DD-HHMMSS>-<served_name>`.

## Comparing model runs

Each successful run pushes `bench/<YYYY-MM-DD>-<served_name>` to the
wiki repo origin. Cross-model comparison is `git fetch && git diff
bench/<a> bench/<b>` on a wiki clone, plus diffing `summary.json`
files locally. Findings get logged at
`kurpatov-wiki-wiki/skills/benchmark/findings/`.

## Files

- [`SPEC.md`](SPEC.md) — design rationale, contracts, invariants.
- [`docs/adr/`](docs/adr/) — architectural decisions (server-side,
  Docker sandbox, storage root).
- [`Dockerfile`](Dockerfile) — sandbox image definition.
- [`run.sh`](run.sh) — the load-bearing wrapper (preflight + docker
  run + summary).
- [`prompts/launch.md`](prompts/launch.md) — agent task prompt that
  points at the wiki skill.

## Status

Architecture validated 2026-04-25. Agent runs sandboxed against the
live vLLM endpoint, artifacts land in STORAGE_ROOT. First-iteration
shape; expect churn as we evaluate models.
