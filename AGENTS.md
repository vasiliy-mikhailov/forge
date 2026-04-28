# CLAUDE.md / AGENTS.md — instructions for LLM agents in this repo

This file is read by agents (Claude Code, Codex CLI, Cowork, etc.)
before they change anything. Keep it short and practical — tools
don't digest verbose prose well. The depth lives in the per-phase
folders below; this file is the navigation index.

## What this repo is

**forge** is my home-lab monorepo for experiments with ML / RL /
LLM on a single machine `mikhailov.tech` with two GPUs (Blackwell +
RTX 5090). Not production, but all the key services run
production-style behind caddy + basic auth and must survive a host
reboot.

The repo is structured by **TOGAF ADM phase** at the top level
(folders `phase-a-…` through `phase-h-…`). Inside Phase C lives the
**application architecture** — four labs (application components):

- `phase-c-information-systems-architecture/application-architecture/wiki-compiler/`
  — vLLM serving the LLM that compiles raw transcripts into wiki articles.
- `phase-c-information-systems-architecture/application-architecture/wiki-bench/`
  — agent harness that benchmarks LLMs on the compiler task and runs
  pilot productions.
- `phase-c-information-systems-architecture/application-architecture/wiki-ingest/`
  — the "media → raw transcript" pipeline (whisper, etc.).
- `phase-c-information-systems-architecture/application-architecture/rl-2048/`
  — Jupyter sandbox for RL/GRPO experiments. Includes its own
  `mlflow/` sublab.

Each lab carries its own `caddy/` (binds host :80/:443 — labs are
mutex on these ports), its own `docker-compose.yml`, its own
`SPEC.md`, its own ADRs (referenced per phase from the lab's AGENTS.md),
  and its own AGENTS.md scoped Phase
A-H.

The "experiment" word is reserved for individual run-instances
inside a lab. A lab is a room; an experiment is a run.

## First thing an agent should do

1. Read this file.
2. Read `README.md` and
   [`phase-d-technology-architecture/architecture.md`](phase-d-technology-architecture/architecture.md)
   to understand the physical layout (where `STORAGE_ROOT` lives,
   what docker network, which images).
3. Open the SPEC.md of the service being edited
   (`phase-c-information-systems-architecture/application-architecture/<lab>/SPEC.md`).
4. Skim the relevant Phase folder's `adr/` and the lab's
   own ADRs (each per-lab `AGENTS.md` lists its ADRs by phase) —
   architectural decisions there must not be silently undone.
5. If you are about to change observable behavior, also open
   `tests/` — that directory is the source of truth for what the
   smoke test (and future test scripts) must verify. Update the
   model there **before** editing `scripts/smoke.sh`. See
   `tests/README.md` for the TDD loop.

## Rules for edits

- **Idempotency.** Any change to a Dockerfile, compose file, or
  Makefile must survive a rebuild and restart. No manual "ssh in
  and do X" steps.
- **One change per edit.** Don't mix refactors with new features.
- **Secrets only in `.env`.** No tokens, passwords, certificates in
  git. If you see something that looks like a secret — stop and ask.
- **Data lives under `${STORAGE_ROOT}`**, not in the forge repo.
  `vault/`, `sources/`, `models/`, `checkpoints/`, `mlruns/` are
  never committed to forge. Note: `vault/raw/` (under
  `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/`) **is** a git
  working tree — but for a *separate* repo (`kurpatov-wiki-raw`),
  pushed by the `kurpatov-wiki-raw-pusher` container. See
  [`phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md`](phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md).
- **ADR for irreversible decisions.** If on-disk data format
  changes, the framework choice changes, or the network topology
  changes — add `phase-<x>/adr/NNNN-*.md` (or
  `phase-c-…/application-architecture/<lab>/docs/adr/NNNN-*.md` (or the flatter `<lab>/adr/NNNN-*.md`)
  for lab-scoped) where NNNN is the next free number.
- **SPEC.md is source of truth.** If code diverges from SPEC, don't
  silently change code — either update SPEC or reconcile code to
  spec.

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

Bring up one lab (labs are mutex on host :80/:443; only one at a
time, except wiki-bench co-running with wiki-compiler):

```bash
make wiki-compiler   # vLLM endpoint
make wiki-ingest     # whisper + ingest
make rl-2048         # GRPO sandbox
```

Diagnostics:

```bash
make ps    # containers
make gpu   # GPU load
make du    # on-disk sizes under STORAGE_ROOT
```

## What NOT to do

- Do not run multiple writers against the mlflow SQLite at the same
  time.
- Labs are mutex on host ports 80/443 (each lab's caddy binds
  them). `wiki-compiler` + `wiki-bench` is the one permitted
  co-running combination (bench is a client without a caddy). All
  other lab combinations: stop one, start another via
  `make <a>-down && make <b>`.
- Do not give two labs overlapping GPU UUIDs in `.env`. The
  Blackwell hosts compiler OR rl-2048 (not both); the RTX 5090
  hosts wiki-ingest. Going to dual-GPU TP for compiler takes both
  cards — wiki-ingest must be down then.
- Do not commit `.ipynb` files or large `.pt`/`.bin` blobs.
- Do not change the
  `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/data/<path>/raw.json`
  format without an ADR — the watcher and every downstream layer
  depend on it.
- Do not reinstall the proprietary nvidia driver (without `-open`)
  and do not delete `/etc/modprobe.d/nvidia-uvm.conf`. Multi-GPU
  on Blackwell does not forgive this. Details and symptoms →
  [`phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md`](phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md);
  diagnostics →
  [`phase-g-implementation-governance/operations.md`](phase-g-implementation-governance/operations.md)
  → "GPU suddenly unavailable".

## Useful commands for the agent

- Service logs: `make <lab>-logs` (tail -f of `docker logs <container>`).
- Enter a container: `docker exec -it <container> bash`.

## Architecture — TOGAF-style layered structure (navigation index)

The repo is organized by TOGAF ADM phase. Each phase folder carries
its own README + topical files; each lab inside Phase C carries its
own AGENTS.md scoped Phase A-H. This file keeps a one-paragraph
synthesis per phase so an agent can decide where to drill in.

We adopt TOGAF *vocabulary and layering*, not certification. We do
not produce Architecture Vision Statements or Architecture
Definition Documents as formal deliverables.

### [Phase A — Architecture Vision](phase-a-architecture-vision/)

Who cares about Forge, why, what target state. Vision: AI tools
that save human time on cognitive work. Goals: TTS / PTS / EB /
Architect-velocity. Single-architect-of-record + capability-
trajectories + containers-only + single-server are the principles
every other phase obeys. Drill in:
[`vision.md`](phase-a-architecture-vision/vision.md),
[`stakeholders.md`](phase-a-architecture-vision/stakeholders.md),
[`drivers.md`](phase-a-architecture-vision/drivers.md),
[`goals.md`](phase-a-architecture-vision/goals.md),
[`principles.md`](phase-a-architecture-vision/principles.md).

### [Phase B — Business Architecture](phase-b-business-architecture/)

What forge can do (capabilities), who does it (org units), what
those capabilities ship (products). Four forge-level capabilities:
R&D, Service operation, Product delivery, Architecture knowledge
management. One org unit today (the architect). Three products:
Kurpatov Wiki (active, canonical), Tarasov Wiki (pre-pilot),
rl-2048 (pre-methodology). Drill in:
[`capabilities/`](phase-b-business-architecture/capabilities/),
[`products/`](phase-b-business-architecture/products/),
[`org-units.md`](phase-b-business-architecture/org-units.md).

### [Phase C — Information Systems Architecture](phase-c-information-systems-architecture/)

Application Architecture (four lab components: wiki-compiler,
wiki-bench, wiki-ingest, rl-2048; the wiki-* are content-agnostic)
+ Data Architecture (raw.json + skill-v2 wiki shape + retrieval
index). Each lab has its own AGENTS.md / SPEC.md / Dockerfile /
ADRs (cited per-phase from each lab's AGENTS.md). Drill in:
[`application-architecture/components.md`](phase-c-information-systems-architecture/application-architecture/components.md),
[`data-architecture/data-sets.md`](phase-c-information-systems-architecture/data-architecture/data-sets.md).

### [Phase D — Technology Architecture](phase-d-technology-architecture/)

How Phase B capabilities are realised — six technology services
(LLM inference, agent orchestration, vector retrieval, container
runtime, transcription, source-of-truth) each provided by some
component (vLLM 0.19.1, OpenHands SDK 1.17.0, embed_helpers + e5,
Docker, faster-whisper, GitHub). Trajectories attach to service
quality dimensions, not to components. Drill in:
[`services/`](phase-d-technology-architecture/services/),
[`invariants.md`](phase-d-technology-architecture/invariants.md),
[`service-tenancy.md`](phase-d-technology-architecture/service-tenancy.md),
[`architecture.md`](phase-d-technology-architecture/architecture.md).

### [Phase E — Opportunities and Solutions](phase-e-opportunities-and-solutions/)

Per-lab gap analyses (Level 1 → Level 2). Combined gap set across
forge is the union of each lab's `STATE-OF-THE-LAB.md`. Active
state-of-the-lab today: wiki-bench. Drill in:
[`README.md`](phase-e-opportunities-and-solutions/README.md).

### [Phase F — Migration Planning](phase-f-migration-planning/)

The sequenced work that closes Phase E gaps — one experiment doc
per swing. Active / closed: G1 (Blackwell stability — closed by 400
W cap + persistence), G2 (MoE swap — falsified, decode is not the
binding lever), G3 (Gemma-4-31B dense — in flight). Drill in:
[`experiments/`](phase-f-migration-planning/experiments/).

### [Phase G — Implementation Governance](phase-g-implementation-governance/)

Roles + repo-wide rules + the per-lab AGENTS.md template every
component follows. One architect of record; containers-only;
AGENTS.md is canonical at every location; symlink convention. Drill
in: [`governance.md`](phase-g-implementation-governance/governance.md),
[`policies/`](phase-g-implementation-governance/policies/),
[`lab-AGENTS-template.md`](phase-g-implementation-governance/lab-AGENTS-template.md).

### [Phase H — Architecture Change Management](phase-h-architecture-change-management/)

How forge evolves: trajectory model (Level 1 / Level 2; delete on
promotion — git is the archive); the "brainstorm experiments"
meta-capability; periodic working-tree audits. Drill in:
[`trajectory-model.md`](phase-h-architecture-change-management/trajectory-model.md),
[`brainstorm-experiments.md`](phase-h-architecture-change-management/brainstorm-experiments.md),
[`audit-2026-04-25.md`](phase-h-architecture-change-management/audit-2026-04-25.md).

Reference: <https://www.opengroup.org/togaf>. Style only.
