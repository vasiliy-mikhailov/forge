# forge

Home-lab monorepo for ML / RL / LLM experiments on a single machine with two
GPUs. Pulls several independent docker-compose stacks under one Makefile:
a caddy reverse proxy, an mlflow tracker, an RL sandbox, and a
"Kurpatov lectures → wiki" pipeline.

This is not a production product. The goal is that if the server burns down,
I can `git clone` + drop `.env` from the password manager + run a couple of
make targets — and rebuild the whole environment.

## Subsystems

| Lab                                | What it does                                              | SPEC                                                                              |
| ---------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `labs/kurpatov-wiki-compiler/`     | vLLM serving the LLM that compiles raw → wiki              | [SPEC](labs/kurpatov-wiki-compiler/SPEC.md)                                       |
| `labs/kurpatov-wiki-ingest/`       | Media → raw transcript pipeline (Whisper, etc.)            | [SPEC](labs/kurpatov-wiki-ingest/SPEC.md)                                         |
| `labs/kurpatov-wiki-bench/`        | Agent harness: benchmark LLMs on the compiler task         | [SPEC](labs/kurpatov-wiki-bench/SPEC.md)                                          |
| `labs/rl-2048/`                    | Jupyter sandbox: vLLM + unsloth + transformers + MLflow    | [SPEC](labs/rl-2048/SPEC.md)                                                      |

Each lab is fully self-contained: own caddy, own docker-compose,
own SPEC. Labs are mutex on host ports 80/443 (each lab's caddy
binds them). See [docs/adr/0007](docs/adr/0007-labs-restructure-self-contained-caddy.md).

## Quick start

> On a fresh host, do the **GPU host setup** from
> [docs/phase-g-implementation-governance/operations.md](docs/phase-g-implementation-governance/operations.md) first — `nvidia-driver-590-open`
> and `uvm_disable_hmm=1` do not install themselves, and multi-GPU on Blackwell
> will not come up without them. This is not optional; see
> [ADR 0004](docs/adr/0004-nvidia-driver-open-plus-hmm-off.md).

```bash
# 1. Fill in secrets and GPU identifiers.
cp .env.example .env
$EDITOR .env

# 2. Create the directory layout on the big disk (STORAGE_ROOT).
make setup

# 3. Bring up one lab. Labs are mutex on ports 80/443 + GPU.
make kurpatov-wiki-compiler   # vLLM for wiki authoring
# or:
make kurpatov-wiki-ingest     # transcription pipeline
# or:
make rl-2048                  # GRPO + jupyter + MLflow
# Bench co-runs with compiler:
# make kurpatov-wiki-compiler && make kurpatov-wiki-bench
```

Diagnostics and control:

```bash
make help                  # list targets
make ps                    # containers
make gpu                   # GPU utilization
make du                    # size of on-disk data
make kurpatov-wiki-ingest-logs   # tail -f one lab's logs
make stop-all              # stop every lab
```

## Architecture (very short)

- One docker network `proxy-net`, every service attached to it.
- Public services are fronted by **per-lab caddy**: each lab carries its
  own `caddy/` and binds host :80/:443 — labs are mutex on these ports
  (see [ADR 0007](docs/adr/0007-labs-restructure-self-contained-caddy.md)).
  Auth is basic, on top of TLS from Let's Encrypt; the inference
  endpoint is the documented exception (vLLM Bearer auth, see
  [ADR 0005](docs/adr/0005-inference-subsystem.md)).
- Heavy data (models, sources, transcripts, checkpoints, mlflow artifacts)
  live on a separate disk at `STORAGE_ROOT` (on my box it's a ZFS pool at
  `/mnt/steam/forge`); layout: `${STORAGE_ROOT}/{shared/models,labs/<lab>/...}`.
  Never enters git.
- Each lab is a standalone docker-compose project under `labs/<lab>/`.
  The root `Makefile` delegates targets into them via `%-down`/`%-logs`/
  `%-build` pattern rules.

More detail in `docs/phase-d-technology-architecture/architecture.md` and the SPEC of each service.

## Docs

- [CLAUDE.md](CLAUDE.md) — instructions for LLM agents working on this repo.
  `AGENTS.md` is a symlink to the same file for cross-tool compatibility.
- [docs/phase-d-technology-architecture/architecture.md](docs/phase-d-technology-architecture/architecture.md) — overall architecture.
- [docs/phase-g-implementation-governance/operations.md](docs/phase-g-implementation-governance/operations.md) — runbook: host prerequisites,
  backups, disaster recovery, GPU rotation.
- [docs/adr/](docs/adr/) — repo-level architecture decision records.
- [tests/](tests/) — plain-English test model (goals + signals + edge
  cases) that `scripts/smoke.sh` and friends derive from. TDD source
  of truth.
- `labs/<lab>/SPEC.md` — per-lab spec.
- `labs/<lab>/docs/adr/` — per-lab ADRs.

## Disaster recovery

See `docs/phase-g-implementation-governance/operations.md`. In short:

1. `git clone https://github.com/vasiliy-mikhailov/forge.git`
2. Restore `.env` from the password manager.
3. Make sure DNS A records for the domains point at this host and ports
   80/443 are free.
4. Do the GPU host setup (driver, UVM, container toolkit, reboot).
5. `make setup && make base`
6. Drop source media back into `${STORAGE_ROOT}/labs/kurpatov-wiki-ingest/sources/...`,
   adjust `.env`, start the services you need.

Code and configs are in git. Data (models, sources, vault, mlflow) lives
outside and needs its own backup strategy (see `docs/phase-g-implementation-governance/operations.md`).
