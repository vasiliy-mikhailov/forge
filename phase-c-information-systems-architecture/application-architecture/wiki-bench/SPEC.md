# wiki-bench — agent benchmark harness

## Purpose
Server-side, **Docker-sandboxed** agent runner that executes the
`wiki/skills/benchmark/SKILL.md` skill (in `kurpatov-wiki-wiki`)
against an open-weight model served by the local `phase-c-information-systems-architecture/application-architecture/wiki-compiler/`
vLLM endpoint. Each invocation produces a versioned per-run artifact
directory under `${STORAGE_ROOT}/labs/wiki-bench/experiments/` and a
branch-on-origin in the wiki repo. Multiple model runs are compared
offline against the same fixed task.

Bench is a **lab** inside forge (since [ADR 0007](../../../phase-g-implementation-governance/adr/0007-labs-restructure-self-contained-caddy.md)) but functionally a *client* of the compiler lab — it talks to `${INFERENCE_DOMAIN}`
over HTTPS like any other external agent. Bench has no caddy and no
port binding, so it is the one lab that **co-runs** with another lab
(specifically, `phase-c-information-systems-architecture/application-architecture/wiki-compiler/`).

## Non-goals
- Not a general-purpose evaluation framework. Wired to one task: the
  per-source authoring loop in
  `kurpatov-wiki-wiki/skills/benchmark/SKILL.md`.
- Not a model server. We consume the vLLM endpoint that
  `phase-c-information-systems-architecture/application-architecture/wiki-compiler/` exposes; we do not start or stop vLLM.
- Not a long-running service. Each `make bench` runs to completion
  (or fails) and exits.
- Not a UI. Headless only.

## Architecture

### Why server-side
Earlier iterations on the operator's macOS laptop (Hermes Agent CLI)
hit Cyrillic-path failures, HTTP timeouts mid-stream, and context
exhaustion before STEP 1 of the skill. Moving the agent to the same
server as vLLM eliminates the laptop sandbox entirely. Full rationale:
[`docs/adr/0001`](docs/adr/0001-openhands-on-server.md).

### Why Docker-sandboxed
The standalone OpenHands binary, run directly as the `vmihaylov`
user, has full home-directory reach: ~/.ssh, ~/.config/gh, ~/forge,
${STORAGE_ROOT}, all visible. We containerize it so the agent sees
only `/workspace` (its own scratch) and `/runs/current` (the per-run
output dir). Rationale, mounts/env detail, and resource caps:
[`docs/adr/0002`](docs/adr/0002-docker-sandbox-and-storage-root.md).

### Container topology
One container per `make bench` invocation, image
`kurpatov-wiki-bench:${OPENHANDS_VERSION}` (built from the local
`Dockerfile`). Image is `python:3.12-slim` + git/jq/curl/ca-certs +
the OpenHands SDK CLI binary. No docker socket, no host home mount.
The agent reaches vLLM over the public TLS path (`bridge` network).

### Mode mutex
None at the GPU level. The bench harness is CPU-only.
`phase-c-information-systems-architecture/application-architecture/wiki-compiler/` must be up; `forge/phase-c-information-systems-architecture/application-architecture/rl-2048/` is irrelevant.

## Storage layout
Per-run artifacts: `${STORAGE_ROOT}/labs/wiki-bench/experiments/<run_id>/`.
Matches the forge convention (heavy data on the data disk, not in repos).

vLLM HF cache (configured in `phase-c-information-systems-architecture/application-architecture/wiki-compiler/`):
`${STORAGE_ROOT}/shared/models/` mounted at `/root/.cache/huggingface`.
Bench doesn't touch this directly; it's a property of the compiler.
No
change here; documenting that the cache lives on the same disk as
bench artifacts.

## Data contracts

### Required env (read from `.env`)
- `STORAGE_ROOT` — data-disk root, matches forge.
- `INFERENCE_BASE_URL` — vLLM endpoint, e.g.
  `https://inference.mikhailov.tech/v1`.
- `VLLM_API_KEY` — same value as in `forge/.env`.
- `INFERENCE_SERVED_NAME` — name vLLM advertises at `/v1/models`.
- `OPENHANDS_VERSION` — pins both the bundled binary and the image tag.
- `WIKI_REPO_URL`, `RAW_REPO_URL` — HTTPS clone URLs.
- `SANDBOX_MEMORY`, `SANDBOX_CPUS`, `SANDBOX_PIDS` — container caps.

### Output per run
`${STORAGE_ROOT}/labs/wiki-bench/experiments/<run_id>/`:
- `events.jsonl` — OpenHands event trace.
- `stderr.log` — container stderr.
- `summary.json` — run metadata + sandbox config + outcome.
- `vllm-snapshot-{start,end}.json` — `/v1/models` at run boundaries.
- `bench-report.md` — fetched from the wiki branch the agent
  pushed (if it got that far).

`run_id` = `<YYYY-MM-DD-HHMMSS>-<served_name>`.

### Output to wiki repo
`bench/<YYYY-MM-DD>-<served_name>` branch on `kurpatov-wiki-wiki`
origin, with one commit per source the agent authored plus
`bench-report.md` at the end (skill contract).

## Invariants
1. `INFERENCE_BASE_URL` is reachable and `/v1/models` returns
   `INFERENCE_SERVED_NAME` before the container starts (preflight
   check in `run.sh`).
2. The `kurpatov-wiki-bench:${OPENHANDS_VERSION}` image exists locally
   (`make build` produces it).
3. `${STORAGE_ROOT}/labs/wiki-bench/experiments/` exists (`make
   storage-init`).
4. `gh auth token` returns a non-empty value with `repo` scope.

## Status
New (2026-04-25). Architecture validated end-to-end: container-only
agent answered a trivial prompt and saved an artifact through the
`/runs/current` mount. Ready for the first real bench run against
the wiki skill.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain (OKRs) inherited from the lab's AGENTS.md.
