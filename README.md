# forge

Home-lab monorepo for ML / RL / LLM experiments on a single machine with two
GPUs. Pulls several independent docker-compose stacks under one Makefile:
a caddy reverse proxy, an mlflow tracker, an RL sandbox, and a
"Kurpatov lectures → wiki" pipeline.

This is not a production product. The goal is that if the server burns down,
I can `git clone` + drop `.env` from the password manager + run a couple of
make targets — and rebuild the whole environment.

## Subsystems

| Service            | What it does                                            | SPEC                                      |
| ------------------ | ------------------------------------------------------- | ----------------------------------------- |
| `caddy/`           | HTTPS reverse proxy + basic auth for public services    | [caddy/SPEC.md](caddy/SPEC.md)            |
| `mlflow/`          | Experiment tracking server                              | [mlflow/SPEC.md](mlflow/SPEC.md)          |
| `rl-2048/`         | Jupyter sandbox: vLLM + unsloth + transformers          | [rl-2048/SPEC.md](rl-2048/SPEC.md)        |
| `kurpatov-wiki/`   | Transcription of lectures + Karpathy-style wiki build   | [kurpatov-wiki/SPEC.md](kurpatov-wiki/SPEC.md) |

## Quick start

> On a fresh host, do the **GPU host setup** from
> [docs/operations.md](docs/operations.md) first — `nvidia-driver-590-open`
> and `uvm_disable_hmm=1` do not install themselves, and multi-GPU on Blackwell
> will not come up without them. This is not optional; see
> [ADR 0004](docs/adr/0004-nvidia-driver-open-plus-hmm-off.md).

```bash
# 1. Fill in secrets and GPU identifiers.
cp .env.example .env
$EDITOR .env

# 2. Create the directory layout on the big disk (STORAGE_ROOT).
make setup

# 3. Bring up base services.
make base          # caddy + mlflow

# 4. Bring up heavy GPU services one at a time.
make kurpatov-wiki
make rl-2048
```

Diagnostics and control:

```bash
make help                  # list targets
make ps                    # containers
make gpu                   # GPU utilization
make du                    # size of on-disk data
make kurpatov-wiki-logs    # tail -f logs
make stop-gpu              # stop rl-2048 + kurpatov-wiki
```

## Architecture (very short)

- One docker network `proxy-net`, every service attached to it.
- Public services (jupyter-*, mlflow) are fronted by caddy, routed by
  hostname → container:port. Auth is basic, on top of TLS from Let's Encrypt.
- Heavy data (models, sources, transcripts, checkpoints, mlflow artifacts)
  live on a separate disk at `STORAGE_ROOT` (on my box it's a ZFS pool at
  `/mnt/steam/forge`) and never enter git.
- Each service is a standalone docker-compose project. The root `Makefile`
  delegates targets into subfolders via `%-build`, `%-down`, `%-logs`
  pattern rules.

More detail in `docs/architecture.md` and the SPEC of each service.

## Docs

- [CLAUDE.md](CLAUDE.md) — instructions for LLM agents working on this repo.
  `AGENTS.md` is a symlink to the same file for cross-tool compatibility.
- [docs/architecture.md](docs/architecture.md) — overall architecture.
- [docs/operations.md](docs/operations.md) — runbook: host prerequisites,
  backups, disaster recovery, GPU rotation.
- [docs/adr/](docs/adr/) — repo-level architecture decision records.
- [tests/](tests/) — plain-English test model (goals + signals + edge
  cases) that `scripts/smoke.sh` and friends derive from. TDD source
  of truth.
- `<service>/SPEC.md` — per-service spec.
- `<service>/docs/adr/` — per-service ADRs.

## Disaster recovery

See `docs/operations.md`. In short:

1. `git clone https://github.com/vasiliy-mikhailov/forge.git`
2. Restore `.env` from the password manager.
3. Make sure DNS A records for the domains point at this host and ports
   80/443 are free.
4. Do the GPU host setup (driver, UVM, container toolkit, reboot).
5. `make setup && make base`
6. Drop source media back into `${STORAGE_ROOT}/kurpatov-wiki/sources/...`,
   adjust `.env`, start the services you need.

Code and configs are in git. Data (models, sources, vault, mlflow) lives
outside and needs its own backup strategy (see `docs/operations.md`).
