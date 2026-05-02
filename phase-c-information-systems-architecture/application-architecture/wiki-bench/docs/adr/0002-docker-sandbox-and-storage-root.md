# ADR 0002 — Docker sandbox for the agent + STORAGE_ROOT-rooted artifacts

## Status
Accepted (2026-04-25).

## Context
ADR 0001 set the agent harness up server-side using the standalone
OpenHands SDK CLI binary. That solved the laptop-Hermes flake but
left a real exposure: the binary ran directly as the `vmihaylov`
user on the host. The agent's tool actions (shell, file ops, git)
executed against the host filesystem with full home-directory
reach. An agent gone weird could:

- Delete or modify anything `vmihaylov` owns: `~/forge/`,
  `~/.ssh/`, `~/.config/gh/`, `${STORAGE_ROOT}` data, etc.
- Use `~/.config/gh/` to access the user's GitHub account beyond
  the wiki repos this bench needs.
- Stop or remove forge containers (the user is in the docker group).
- Edit `forge/.env` and corrupt the inference setup we just built.

Operationally we never want any of that, even by accident. The
benchmark should never have side-effects outside its scratch dir
and the wiki repo.

## Decision
**Wrap the OpenHands CLI in a Docker container we build ourselves**
(`Dockerfile` in this repo, image tag
`kurpatov-wiki-bench:${OPENHANDS_VERSION}`). The agent runs inside
this container; the host is not visible to it.

Plus: **all per-run artifacts live under `${STORAGE_ROOT}`**, not in
the repo. This matches the forge convention that heavy data lives
on the data disk rather than in version control or home directory.

### Sandbox shape
The image is intentionally minimal: `python:3.12-slim` + git + jq +
curl + ca-certificates + the OpenHands binary at
`/usr/local/bin/openhands`. No docker-in-docker, no sudo, no host
mounts beyond a single bind to the per-run output dir.

`docker run` invocation (full form in `run.sh`):

```
docker run --rm \
  --name "bench-${run_id}" \
  --network bridge \
  --memory ${SANDBOX_MEMORY} \
  --cpus ${SANDBOX_CPUS} \
  --pids-limit ${SANDBOX_PIDS} \
  -v "${run_dir}:/runs/current:rw" \
  -e LLM_BASE_URL ... \
  kurpatov-wiki-bench:${OPENHANDS_VERSION} \
  --headless --json --always-approve --override-with-envs -t "$task"
```

Deliberately **not** present:
- `-v /var/run/docker.sock` — would let the agent escape via
  sibling containers.
- `-v $HOME` or any subset (`~/.ssh`, `~/.config/gh`,
  `~/forge`, `~/.openhands-state`) — host filesystem stays
  invisible.
- `--privileged`, `--cap-add`, `--security-opt seccomp=unconfined`
  — defaults are fine; no escalation.

### What the agent CAN reach
- `/workspace` inside the container — its own scratch. Where it
  clones the wiki + raw repos, edits files, runs python.
- `/runs/current` — the only bridge to the host. Bind-mounted
  read-write to `${STORAGE_ROOT}/wiki-bench/runs/<run_id>/`.
- HTTPS to `inference.mikhailov.tech` (vLLM) and `github.com`
  (clone + push). Default bridge network, no special routes.
- The GitHub token via `GITHUB_TOKEN` env var passed by `run.sh`.

### Storage layout
- Per-run artifacts:
  `${STORAGE_ROOT}/wiki-bench/runs/<run_id>/`
  — `events.jsonl`, `stderr.log`, `summary.json`,
  `vllm-snapshot-{start,end}.json`, optional `bench-report.md`.
- vLLM HF cache (already in place via `phase-c-information-systems-architecture/application-architecture/wiki-compiler/`):
  `${STORAGE_ROOT}/models/` mounted at `/root/.cache/huggingface`
  inside the vLLM container. No change here; documenting the
  convention.
- The bench repo itself stays in `~/wiki-bench/` for
  source control. Only `bin/openhands` (85 MB binary) is
  gitignored; everything else is version-controlled.

## GitHub auth
Reuses the host's `gh` CLI token (`gh auth token`). `run.sh`
fetches it at invocation and passes it to the container as
`GITHUB_TOKEN` env var, plus inlined into the agent's task
prompt for HTTPS git clone/push.

Considered but rejected: a dedicated SSH deploy key registered
on `kurpatov-wiki-wiki`. Pros: narrower blast radius (one repo,
not all repos in the user's account). Cons: another secret to
manage, doesn't compose with the agent's HTTPS-by-default
preferences. The token approach is consistent with how forge
already pushes to its own repo.

## Resource caps
First defaults (in `.env.example`):
- `SANDBOX_MEMORY=16g` — generous for a 27-72B context-window
  agent loop; plenty of room for git, python, tool buffers.
- `SANDBOX_CPUS=4` — agent is mostly I/O-bound waiting for vLLM;
  4 cores is enough for git clone + python + jq.
- `SANDBOX_PIDS=256` — caps fork bombs from a misbehaving agent
  while leaving room for normal subprocess work.

Bump if a run dies on OOM or pid-limit. Track these in summary.json
so we can see correlations across runs.

## Consequences

**Positive.**
- Agent cannot damage host. Worst case: container is unusable, we
  `docker rm` it.
- Reproducibility: each run starts in an identical container
  filesystem.
- Storage layout consistent with forge — one disk-management
  story across the lab.

**Negative / accepted.**
- Files written by the agent to `/runs/current` end up
  root-owned on the host (uid 0 inside the slim image). Acceptable
  — they're readable by everyone in the `steam` group; deletion
  needs `sudo` or `chown` (run.sh could clean this up but we'd
  rather keep run.sh small).
- Image rebuild required when bumping `OPENHANDS_VERSION` (and
  swapping `bin/openhands`). Documented in README.
- ~100 MB image, plus 85 MB binary in repo (gitignored). Not
  significant.

## Reversibility
High. To revert to direct binary execution: drop the Dockerfile,
restore the v3 `run.sh` from git history. The tradeoff would be
re-exposing the host home directory.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
