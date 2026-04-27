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


## Architecture — TOGAF-style layered structure

This section organises every architecture decision in Forge by the
TOGAF ADM phase it belongs to. The point is **layering**: a decision
about wiki concept structure (Phase B) lives one layer below "Forge
saves human time" (Phase A), and a decision about which embedding
model (Phase D) lives two layers below that. When you read this
file you do not have to wade through libblas3 to reach the mission;
when you debug embed_helpers.py you do not have to re-derive why
the wiki exists.

We adopt TOGAF *vocabulary and layering*, not certification. We do
not produce Architecture Vision Statements, Architecture Definition
Documents, or Architecture Roadmaps as formal deliverables. Each lab
keeps its own concrete artefacts in `labs/<lab>/docs/` (ADRs,
experiments, STATE-OF-THE-LAB.md).

### Phase A — Architecture Vision

This phase answers *who* cares about Forge as an architecture, *why*
they care, and *what target state* the architecture exists to reach.
The product portfolio (which products and their value streams) is not
here — that lives in Phase B.

**Vision statement.** Forge builds AI tools that save human time on
cognitive work — both consuming information and writing/optimizing
programs.

**Stakeholders.**

- **Architect of record** — one person (the repo owner). Sole driver
  of trajectory changes, sole reviewer, today the only consumer of
  every output.
- **Future operator** — the architect's future self, who will inherit
  these docs, debug failures, and extend the platform. Most of what
  is written here is for them.
- **End users** — TBD. Currently identical with the architect; the
  Practical-Time-Saved goal becomes meaningful only once there are
  non-architect users.

**Drivers.**

- Time spent consuming information from Russian psychology lectures
  (Kurpatov: ~60-90 min each, ~200 in catalog).
- Time spent writing/optimizing programs in domains where RL with
  verifiable rewards (RLVR) can do the slog automatically.
- Architect-velocity: every minute the architect spends recovering
  GPUs or rerunning failed pilots is a minute not spent on the real
  work.

**Goals (Motivation-layer; quantified in Phase H trajectories).**

- **TTS — Theoretical Time Saved.** Minutes saved per use,
  conditional on the product's quality dimensions holding.
- **PTS — Practical Time Saved.** Cumulative minutes saved across
  all users (= TTS × users × engagement).
- **EB — Economic Balance.** Revenue minus operational cost
  (GPU-hours + storage + architect-hours at shadow rate).
- **Architect-velocity.** Capability advances per architect-hour.
  Cross-cuts every other goal — speed of forge's own improvement.

**Principles.**

- **Single architect of record.** No committee, no formal review
  process beyond AGENTS.md conventions.
- **Capability trajectories.** Every capability has Level 1 (today)
  and Level 2 (next planned state). When L2 is reached, it becomes
  the new L1 and the prior L1 is deleted from docs; git is the
  archive. No `Withdrawn` / `Deprecated` / `Closed` status flags in
  the working tree.
- **Containers-only execution** (`docs/policies/containers.md`).
- **Single-server deployment** on `mikhailov.tech` — all services
  share one host, one network, two GPUs.

### Phase B — Business Architecture

Forge is, first and foremost, an **R&D organization**. Its primary
business capability is research-and-development: turning ideas about
AI saving human time on cognitive work into shipped, falsifiable
tools. Products (Kurpatov Wiki, rl-2048) are *outputs* of that R&D —
not the top of the architecture.

**Primary capability: R&D**

| Capability sub-area                       | Quality dimension                                  |
|-------------------------------------------|----------------------------------------------------|
| Run hypothesis-driven experiments         | Architect-velocity: capability advances per architect-hour |
| Reproduce + audit experiments             | Replay from `(Dockerfile + raw transcripts)` only |
| Ship verified outputs to consumers        | Branch hygiene; verify-by-artifact, not by agent  |

**Labs realize R&D, they are not products.** Each lab is a specialized
"workshop" inside forge that hosts a slice of R&D for one domain or
one production-framework component. Labs have services + components
(Phase D) and trajectories (Phase H) but no separate Phase A vision
of their own — their vision is a lab-scoped restatement of forge's
R&D vision.

| Lab                          | R&D scope                                                 |
|------------------------------|-----------------------------------------------------------|
| `kurpatov-wiki-compiler`     | LLM inference research + reliable serving infrastructure  |
| `kurpatov-wiki-bench`        | Benchmarking methodology + the wiki-compilation harness   |
| `kurpatov-wiki-ingest`       | Audio→text pipeline research + maintenance                |
| `rl-2048`                    | Program-synthesis-via-RLVR methodology research           |

**R&D output #1: the Kurpatov Wiki product**

Value stream: lecture → smart-reading wiki (collect → filter → adapt).

| Capability                           | Quality dimension                          |
|--------------------------------------|--------------------------------------------|
| Compile lecture into source.md       | **Fast for reading** — bullets, TL;DR, no narrative bloat |
| Cross-source dedup of claims         | **No repetitions** — REPEATED markers, retrieval-augmented |
| Fact-check empirical claims          | **No fake statements** — Wikipedia URLs, CONTRADICTS_FACTS markers |
| Concept extraction + linking         | (in service of the above three) |
| Benchmark open-weight LLMs vs Opus   | (gates the production runs) |

**R&D output #2: rl-2048 (program-synthesis methodology)**

Value stream: verifiable-reward problem → AI-written solver
(observe → train → emit).

| Capability                           | Quality dimension                          |
|--------------------------------------|--------------------------------------------|
| Solve 2048 faster                    | (TBD — falsifiable metric to be locked) |
| RLVR training loop                   | (TBD) |

(The rl-2048 row is a stub — populate when its STATE-OF-THE-LAB.md
gets written.)

### Phase C — Information Systems Architecture

| Data set                                  | Shape                                    |
|-------------------------------------------|------------------------------------------|
| `kurpatov-wiki-raw`                       | per-source `raw.json` (whisper segments) |
| `kurpatov-wiki-wiki:skill-v2`             | `data/sources/<slug>.md`, `data/concepts/<slug>.md`, `data/concept-index.json` |
| Bench artefacts                           | `${STORAGE_ROOT}/labs/kurpatov-wiki-bench/experiments/<run_id>/` |
| Retrieval index (D8)                      | `wiki/data/embeddings/{claims,concepts}.{sqlite,npz}` (numpy + sqlite hybrid) |

Per-product detailed shapes live in their lab's STATE-OF-THE-LAB.md.

### Phase D — Technology Architecture

The Forge platform realises Phase B capabilities through a small set
of **technology services**, each provided by one or more **technology
components / system software**. Capabilities live upstairs (Phase A/B);
this section is about *how* they are realised, not *what* they are.

Trajectories (Level 1 / Level 2) attach to **service quality
dimensions**, not to components. Replacing a component (e.g. vLLM
0.19.1 → 0.20) is just the next step on the same trajectory; we don't
keep "Was vLLM 0.19.1" annotations — git remembers.

Cross-cutting tech-quality dimensions (analogous to TTS/PTS/EB at the
Motivation layer): **throughput**, **latency**, **stability**
(mean-time-to-crash), **cost-per-output-token**. These feed
architect-velocity and EB; they do not directly move TTS.

**Service: LLM inference**
- Component: vLLM 0.19.1 (cu130) serving Qwen3.6-27B-FP8 on the
  Blackwell, 128 K context via YaRN factor 4.0, single-card.
- Lab: `kurpatov-wiki-compiler/`.
- L1 throughput: ~47 tok/s decode batch=1, ~6.3 K tok/s prefill.
- L1 stability: ~50 % UVM-crash rate within 2.5 h at default settings;
  failure mode is `gdn_linear_attn._forward_core` →
  `cudaErrorLaunchFailure` followed by kernel-side
  `BUG uvm_gpu_chunk_5`.
- L2 stability: ≤ 5 % crash rate over 7-source pilots
  (G1 experiment: 400 W power cap + persistence on +
  `--gpu-memory-utilization 0.85`).

**Service: Agent orchestration & sub-agent delegation**
- Component: OpenHands SDK 1.17.0 + TaskToolSet, file-based
  sub-agent definitions.
- Lab: `kurpatov-wiki-bench/orchestrator/`.
- L1: top-orch context bounded per source (Invariant A — Python-loop
  driver creates fresh `Conversation` per source); but 0 % KV-cache
  reuse across sub-agent delegations within a Conversation, so each
  call re-prefills its system prompt.
- L2: KV-cache reuse across same-Conversation sub-agent calls (vLLM
  prefix-cache + openhands integration). Estimated impact:
  ~5-10× fewer prefill tokens per source, ~3-4 min saved per source
  on a 7-source run.

**Service: Vector retrieval (claim and concept dedup)**
- Component: `orchestrator/embed_helpers.py` +
  `intfloat/multilingual-e5-base` + numpy + sqlite. Index lives in
  the wiki repo at `wiki/data/embeddings/{claims,concepts}.{sqlite,npz}`.
- Lab: `kurpatov-wiki-bench/`.
- L1 claim retrieval: wired into source-author per-claim via
  `find-claims --k 5`; threshold 0.78 for REPEATED (calibrated against
  e5-base paraphrase distribution — see step9 synth gate).
- L1 concept retrieval: NOT wired into curator (curator does naive
  exact-slug `ls` check); `find-concepts` CLI exists but unused.
- L1 cost: per-CLI fork of `embed_helpers.py` re-loads e5-base
  (~280 MB) — ~5 s per invocation. At 100 claims × 200 sources scale
  this is ~28 hours of pure model-load.
- L2: `find-concepts` wired into curator with 0.85 dedup threshold;
  embed_helpers daemonized so the model loads once.

**Service: Container runtime + GPU isolation**
- Component: Docker + CUDA 13 + nvidia-container-toolkit. Image
  `kurpatov-wiki-bench:1.17.0-d8-cal` bakes openhands-sdk +
  sentence-transformers + e5-base + bench scripts under `/opt/forge/`.
- L1 stability: works for steady-state, but `docker rm -f` on a
  CUDA-active container leaves an orphan kernel-side context (G1-H3:
  observed 2026-04-27 when killing a side-experiment container left
  the *other* GPU at 100 % util / 110 W draw with no userspace owner;
  per-GPU reset failed; orphan only cleared by full driver reload).
- L2 stability: convention codified — always `docker stop` (SIGTERM
  + grace) before `docker rm -f` for CUDA containers.

**Service: Audio → text transcription**
- Component: faster-whisper.
- Lab: `kurpatov-wiki-ingest/`.
- L1: ~200 Курпатов lectures transcribed end-to-end. Output is the
  `raw.json` whisper-segment shape consumed downstream.
- L2: stable; not on the active trajectory.

**Service: Source-of-truth + per-experiment branch storage**
- Component: GitHub remotes — `kurpatov-wiki-raw` (transcripts,
  pushed by raw-pusher), `kurpatov-wiki-wiki` (compiled wiki,
  experiment branches `experiment/D*-...-<served>`).
- L1: 50 GB-class repos within free quota; bench branches for every
  pilot.
- L2: stable.

**Forge-wide invariants (apply to every service):**
- Single-server deployment on `mikhailov.tech`.
- Containers-only execution (`docs/policies/containers.md`).
- Persistence-aware GPU power management
  (`/etc/systemd/system/nvidia-power-limit.service` — 400 W cap with
  `-pm 1`).

#### Service tenancy — forge-wide vs lab-local

Some services are provided centrally and consumed by every lab; some
live inside one lab. The split helps decide where a change lands.

| Service                                  | Provided by                                | Consumed by                                                |
|------------------------------------------|--------------------------------------------|------------------------------------------------------------|
| Container runtime + GPU isolation        | host (Docker + nvidia-container-toolkit)   | every lab                                                  |
| Persistence-aware GPU power mgmt         | host (`nvidia-power-limit.service`)        | every GPU-using lab                                        |
| Reverse proxy + TLS termination          | per-lab caddy (mutex on host :80/:443)     | the lab's own public services                              |
| Source-of-truth + per-experiment branch storage | GitHub remotes                       | every lab                                                  |
| LLM inference                            | `kurpatov-wiki-compiler` (vLLM)            | `kurpatov-wiki-bench`, future RL trainers                  |
| Audio → text transcription               | `kurpatov-wiki-ingest` (faster-whisper)    | `kurpatov-wiki-wiki` source-of-truth                       |
| Agent orchestration & sub-agent delegation | `kurpatov-wiki-bench` (OpenHands SDK)    | bench's per-source pipelines                               |
| Vector retrieval (claim/concept dedup)   | `kurpatov-wiki-bench` (`embed_helpers.py`) | bench's source-author + (planned) curator                  |
| ML training tracking                     | `rl-2048/mlflow/` (MLflow)                 | rl-2048 only                                               |
| Notebook sandbox                         | `rl-2048/jupyter/`                         | rl-2048 only                                               |
| LoRA / RFT fine-tuning                   | `rl-2048` (unsloth, planned)               | rl-2048 only (currently)                                   |

**Rule:** if a component is in column 2 of more than one row, it is
forge-wide (caddy is the obvious case — every lab runs its own, but
they share the same host-port-mutex constraint, so caddy itself is a
forge-wide concern even though instances are lab-local).

Specific version pins live in `Dockerfile`s and `.env`. Specific
*decisions* about why those versions/components were picked live in
lab ADRs.

### Phase E — Opportunities and Solutions

Per-lab gap analyses live in their lab’s `STATE-OF-THE-LAB.md`
(capability trajectories Level 1 → Level 2). The combined gap set
across forge is the union of those.

- `labs/kurpatov-wiki-bench/docs/STATE-OF-THE-LAB.md` — current
  capability trajectories for the wiki bench.
- `labs/rl-2048/docs/STATE-OF-THE-LAB.md` — TBD (when rl-2048
  grows beyond the Jupyter sandbox).

### Phase F — Migration Planning

Active experiment specs at `labs/<lab>/docs/experiments/<id>.md` are
the sequenced work packages that close those gaps. Only Active and
Closed-but-still-cited experiments are kept in the working tree;
superseded ones go to git history per Phase H.


Per lab, the active trajectory toward Level 2 (TOGAF would call this
the Transition Architecture). Updated when an experiment opens or
closes:

- `labs/kurpatov-wiki-bench/docs/STATE-OF-THE-LAB.md` — current
  capability trajectories for the wiki bench.
- `labs/rl-2048/docs/STATE-OF-THE-LAB.md` — TBD (when rl-2048 grows
  beyond the Jupyter sandbox).

Concrete experiment specs sit at `labs/<lab>/docs/experiments/<id>.md`
(only Active and Closed-but-still-cited experiments — superseded ones
go to git history per Phase H).

### Phase G — Implementation Governance

- **Architect of record**: one person (the repo owner). All trajectory
  changes pass through them.
- **All work runs in containers** (`docs/policies/containers.md`).
- **AGENTS.md per lab** carries operational rules for that lab; the
  forge-level CLAUDE.md (this file) carries cross-cutting rules.
- **No PR review automation** beyond the AGENTS.md convention.

#### Per-lab AGENTS.md must follow the canonical template

The TOGAF ADM phase structure is meant to *permeate*, not just live at
the top. Every lab’s `labs/<lab>/AGENTS.md` must use the canonical
phase headers (Phase A through Phase H, classic TOGAF names — see
`docs/lab-AGENTS-template.md`), scoped to that lab. The template is
the source of truth for section ordering and wording; copy from it
when adding or editing a lab AGENTS.md.

Symlink convention: each lab keeps `AGENTS.md` as the regular file and
`CLAUDE.md` as a symlink → `AGENTS.md`. Forge root inverts the direction
(`AGENTS.md` → `CLAUDE.md`) for historical reasons — leave that
as is.

Labs that don’t yet have AGENTS.md must add one when their next
substantive change lands. Until then, the forge-level CLAUDE.md is the
authoritative reference for those labs.

### Phase H — Architecture Change Management

Architecture is organised around capabilities, each with two states:

- **Level 1** = as-is (how the capability works today)
- **Level 2** = to-be (the next planned state)

When Level 2 is reached it **becomes** the new Level 1; the prior
Level 1 description is **deleted from docs**. Git history keeps every
prior level — that is the archive. We do not maintain `legacy/` tiers,
`Superseded by NNNN` cross-links, `archive/` directories, or
`Withdrawn`/`Deprecated`/`Closed` status flags. Presence of text in
the working tree means current; absence means git history.

**Brainstorm experiments** is itself a capability:

> Triggered by metric gaps. Single architect drives. Pruning baggage
> and proposing experiments are the same activity, both targeting
> time-to-market and token efficiency. Output: a new
> `docs/experiments/<id>.md` (Level 2 proposal) + deletions in any
> docs that contain stale historical content.

**Baggage** = anything that does not contribute to a current
capability's Level 1 or Level 2. Test: ask "if I delete this, does
any current architecture conversation lose information?" If no,
delete it.

Reference: <https://www.opengroup.org/togaf>. Style only.
