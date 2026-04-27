# CLAUDE.md / AGENTS.md — instructions for LLM agents in this repo

This file is read by agents (Claude Code, Codex CLI, Cowork, etc.) before
they change anything. Keep it short and practical — tools don't digest
verbose prose well.

## What this repo is

**forge** is my home-lab monorepo for experiments with ML / RL / LLM on a
single machine `mikhailov.tech` with two GPUs (Blackwell + RTX 5090). Not
production, but all the key services run production-style behind caddy +
basic auth and must survive a host reboot.

forge is now organized as a **lab metaphor**: each major workload
lives under `labs/<slug>/` as a fully self-contained "room" with
its own caddy, docker-compose, SPEC, ADRs. Top-level holds only
docs, scripts, and the root Makefile that dispatches into labs.

Labs:

- `labs/kurpatov-wiki-compiler/` — vLLM serving the LLM that
  *compiles* raw transcripts into wiki articles.
- `labs/kurpatov-wiki-ingest/` — the "media → raw transcript"
  pipeline (Whisper, etc.).
- `labs/kurpatov-wiki-bench/` — agent harness that benchmarks
  different LLMs on the compiler task.
- `labs/rl-2048/` — Jupyter sandbox for RL/GRPO experiments.
  Includes its own `mlflow/` sublab (mlflow used to live at
  forge top-level; only rl-2048 uses it, so it moved in).

Each lab carries:

- Its own `caddy/` (binds host :80/:443 — labs are mutex on
  these ports).
- Own `docker-compose.yml` for its core services.
- Own `SPEC.md` + `docs/adr/`.

Top-level:

- `docs/` — cross-lab docs + ADRs (this restructure is ADR 0007).
- `scripts/` — cross-lab tooling (smoke, push-sources).
- `Makefile` — dispatcher: `make <lab>`, `make <lab>-down`,
  `make stop-all`.
- `common.mk` — shared Make machinery (finds forge root via
  `git rev-parse --show-toplevel` so it works at any nesting depth).

The "experiment" word is reserved for individual run-instances
inside a lab (e.g. "experiment 148 = qwen3.6-27b-fp8 on
2026-04-25" inside the bench lab). A lab is a room; an
experiment is a run.

## First thing an agent should do

1. Read this file.
2. Read `README.md` and `docs/architecture.md` to understand the physical
   layout (where `STORAGE_ROOT` lives, what docker network, which images).
3. Open the SPEC.md of the service being edited (`labs/<lab>/SPEC.md`).
4. Skim `docs/adr/` and `labs/<lab>/docs/adr/` — architectural decisions
   there must not be silently undone.
5. If you are about to change observable behavior, also open `tests/` —
   that directory is the source of truth for what the smoke test (and
   future test scripts) must verify. Update the model there **before**
   editing `scripts/smoke.sh`. See `tests/README.md` for the TDD loop.

## Rules for edits

- **Idempotency.** Any change to a Dockerfile, compose file, or Makefile
  must survive a rebuild and restart. No manual "ssh in and do X" steps.
- **One change per edit.** Don't mix refactors with new features.
- **Secrets only in `.env`.** No tokens, passwords, certificates in git.
  If you see something that looks like a secret — stop and ask.
- **Data lives under `${STORAGE_ROOT}`**, not in the forge repo.
  `vault/`, `sources/`, `models/`, `checkpoints/`, `mlruns/` are never
  committed to forge. Note: `vault/raw/` (under `${STORAGE_ROOT}/labs/kurpatov-wiki-ingest/vault/raw/`) **is** a git working tree —
  but for a *separate* repo (`kurpatov-wiki-raw`), pushed by the
  `kurpatov-wiki-raw-pusher` container. See
  `labs/kurpatov-wiki-ingest/docs/adr/0005-split-transcribe-and-push.md`.
- **ADR for irreversible decisions.** If on-disk data format changes, the
  framework choice changes, or the network topology changes — add
  `docs/adr/NNNN-*.md` or `labs/<lab>/docs/adr/NNNN-*.md` where NNNN is the
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

Bring up one lab (labs are mutex on host :80/:443; only one at a time):

```bash
make kurpatov-wiki-compiler   # vLLM endpoint
make kurpatov-wiki-ingest     # whisper + ingest
make rl-2048                  # GRPO sandbox
# ↑ labs are mutex on host :80/:443 — bring up only one (bench co-runs with compiler).
```

Diagnostics:

```bash
make ps    # containers
make gpu   # GPU load
make du    # on-disk sizes under STORAGE_ROOT
```

## What NOT to do

- Do not run multiple writers against the mlflow SQLite at the same time.
- Labs are mutex on host ports 80/443 (each lab's caddy binds them).
  `kurpatov-wiki-compiler` + `kurpatov-wiki-bench` is the one
  permitted co-running combination (bench is a client without a
  caddy). All other lab combinations: stop one, start another via
  `make <a>-down && make <b>`.
- Do not give two labs overlapping GPU UUIDs in `.env`. The
  Blackwell hosts compiler OR rl-2048 (not both); the RTX 5090
  hosts kurpatov-wiki-ingest. Going to dual-GPU TP for compiler
  takes both cards — kurpatov-wiki-ingest must be down then.
- Do not commit `.ipynb` files or large `.pt`/`.bin` blobs.
- Do not change the `${STORAGE_ROOT}/labs/kurpatov-wiki-ingest/vault/raw/data/<path>/raw.json` format without an ADR —
  the watcher and every downstream layer depend on it.
- Do not reinstall the proprietary nvidia driver (without `-open`) and
  do not delete `/etc/modprobe.d/nvidia-uvm.conf`. Multi-GPU on Blackwell
  does not forgive this. Details and symptoms →
  `docs/adr/0004-nvidia-driver-open-plus-hmm-off.md`, diagnostics →
  `docs/operations.md` → "GPU suddenly unavailable".

## Useful commands for the agent

- There is no task tracker in the repo. Active work lives in git history
  and in `docs/` (ADRs + SPECs).
- Service logs: `make <lab>-logs` (tail -f of `docker logs <container>`).
- Enter a container: `docker exec -it <container> bash`.


## Architecture management — TOGAF-style (lite)

We follow **TOGAF-style** discipline for experiments and architecture
decisions. This is a *style*, not strict compliance — we adopt
TOGAF's vocabulary (Baseline / Target / Transition Architecture,
Architecture Repository, supersession, Compliance Review) and a small
set of operating routines, without formal deliverables (no Architecture
Vision Statement, no Architecture Definition Document, no Capability
Maturity assessments).

Concrete artefacts (the Architecture Repository):

- **Baseline state** — `labs/<lab>/docs/STATE-OF-THE-LAB.md` (where it
  exists) is the as-is / to-be / gaps audit; updated when a major
  experiment closes.
- **ADRs** — `labs/<lab>/docs/adr/NNNN-<slug>.md`. Status header is
  authoritative: `Proposed | Accepted | Superseded by NNNN | Withdrawn`.
  When an ADR is superseded, the originating ADR's Status header is
  updated *in the same commit* that lands the successor.
- **Experiments** — `labs/<lab>/docs/experiments/<id>.md`. Status
  header: `Active | Closed | Superseded by <id>`. Closed experiments
  remain as research records; superseded experiments stay verbatim
  with a one-line pointer.
- **Legacy code/docs** — superseded artefacts move to a sibling
  `legacy/` directory with a one-line README pointing at the
  canonical successor. Never delete; never edit in place.
- **Post-mortems** — withdrawn proposals and design notes that didn't
  ship live in `labs/<lab>/docs/post-mortems/`.

Routines:

| Routine                 | Trigger                                  | Output                                                                       |
|-------------------------|------------------------------------------|------------------------------------------------------------------------------|
| **Supersession review** | ADR or experiment closes                 | Status flip on the superseded ADR/experiment + one-line pointer to successor |
| **Baggage pruning**     | (cadence — see open question below)      | Stale historical content removed from active docs; legacy content moved to `legacy/` |
| **Compliance review**   | PR adding/changing an ADR-level artefact | Reviewer checks against the lab's AGENTS.md invariants                       |
| **Baseline refresh**    | Major experiment closes                  | STATE-OF-THE-LAB.md updated                                                  |

Open governance questions (intentionally unspecified — codify when
answered, see commit history for the most recent decision):

- Cadence and scope of baggage pruning sweeps
- Whether peer review is required for ADR/experiment supersession, or
  whether a single architect approves
- Whether to introduce a formal `archive/` tier for content >1 year old

Reference: <https://www.opengroup.org/togaf>. We do not claim
certification or full compliance — only the discipline.
