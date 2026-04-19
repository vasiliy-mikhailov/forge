# CLAUDE.md / AGENTS.md — instructions for LLM agents in this repo

This file is read by agents (Claude Code, Codex CLI, Cowork, etc.) before
they change anything. Keep it short and practical — tools don't digest
verbose prose well.

## What this repo is

**forge** is my home-lab monorepo for experiments with ML / RL / LLM on a
single machine `mikhailov.tech` with two GPUs (Blackwell + RTX 5090). Not
production, but all the key services run production-style behind caddy +
basic auth and must survive a host reboot.

Current subsystems (each in its own folder):

- `caddy/` — edge proxy + Let's Encrypt.
- `mlflow/` — tracking server (SQLite + artifacts on HDD).
- `rl-2048/` — Jupyter sandbox for RL/GRPO experiments.
- `kurpatov-wiki/` — the "video → raw transcript → wiki" pipeline
  (Karpathy-style LLM notes on Kurpatov's psychology lectures).
- `docs/` — repo-level docs (architecture, operations, ADRs).
- Root `Makefile` + `common.mk` — one remote control: `make <service>`,
  `make <service>-down`, `make <service>-build`, `make base`, `make stop-gpu`.

## First thing an agent should do

1. Read this file.
2. Read `README.md` and `docs/architecture.md` to understand the physical
   layout (where `STORAGE_ROOT` lives, what docker network, which images).
3. Open the SPEC.md of the service being edited (`<service>/SPEC.md`).
4. Skim `docs/adr/` and `<service>/docs/adr/` — architectural decisions
   there must not be silently undone.

## Rules for edits

- **Idempotency.** Any change to a Dockerfile, compose file, or Makefile
  must survive a rebuild and restart. No manual "ssh in and do X" steps.
- **One change per edit.** Don't mix refactors with new features.
- **Secrets only in `.env`.** No tokens, passwords, certificates in git.
  If you see something that looks like a secret — stop and ask.
- **Data lives under `${STORAGE_ROOT}`**, not in the repo. `vault/`,
  `videos/`, `models/`, `checkpoints/`, `mlruns/` are never committed.
- **ADR for irreversible decisions.** If on-disk data format changes, the
  framework choice changes, or the network topology changes — add
  `docs/adr/NNNN-*.md` or `<service>/docs/adr/NNNN-*.md` where NNNN is the
  next free number.
- **SPEC.md is source of truth.** If code diverges from SPEC, don't
  silently change code — either update SPEC or reconcile code to spec.

## How to run

Fill `.env` from the template:

```bash
cp .env.example .env
# Fill in ACME_EMAIL, BASIC_AUTH_HASH (see comment in .env.example),
# domains, and GPU UUIDs (nvidia-smi -L).
```

Create on-disk layout (creates `${STORAGE_ROOT}` and subdirs):

```bash
make setup
```

Base services:

```bash
make base        # caddy + mlflow
```

GPU services (bring them up one by one so errors don't blur together):

```bash
make kurpatov-wiki
make rl-2048
```

Diagnostics:

```bash
make ps    # containers
make gpu   # GPU load
make du    # on-disk sizes under STORAGE_ROOT
```

## What NOT to do

- Do not run multiple writers against the mlflow SQLite at the same time.
- Do not give rl-2048 and kurpatov-wiki the same GPU UUID — the second
  service will hit OOM.
- Do not commit `.ipynb` files or large `.pt`/`.bin` blobs.
- Do not change the `vault/raw/<path>/raw.json` format without an ADR —
  the watcher and every downstream layer depend on it.
- Do not reinstall the proprietary nvidia driver (without `-open`) and
  do not delete `/etc/modprobe.d/nvidia-uvm.conf`. Multi-GPU on Blackwell
  does not forgive this. Details and symptoms →
  `docs/adr/0004-nvidia-driver-open-plus-hmm-off.md`, diagnostics →
  `docs/operations.md` → "GPU suddenly unavailable".

## Useful commands for the agent

- There is no task tracker in the repo. Active work lives in git history
  and in `docs/` (ADRs + SPECs).
- Service logs: `make <service>-logs` (tail -f of `docker logs <container>`).
- Enter a container: `docker exec -it <container> bash`.
