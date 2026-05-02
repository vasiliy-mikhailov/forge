# ADR 0007 — labs/ restructure, self-contained per-lab caddy, MLflow inside rl-2048

## Status
Accepted (2026-04-25).

## Context
Up to ADR 0006, forge was a flat collection of subsystems —
`caddy/`, `mlflow/`, `inference/`, `kurpatov-wiki/`, `rl-2048/` —
with shared infra (one caddy fronting all FQDNs, one mlflow used
by everything that wanted experiment tracking) and ad-hoc GPU
mutex (only `rl-2048` and `kurpatov-wiki` scheduled around the
two cards).

Three things converged that called for a redesign:

1. The new bench-as-battery (ADR 0006 wiki-bench) added
   a fourth GPU-using subsystem. The flat structure was already
   crowded; adding bench as another sibling at the top level
   would have made it harder to read what's an "experiment" vs
   what's "infrastructure".
2. Going to dual-GPU TP for 70B+ dense models on the inference
   side means the compiler subsystem will eventually take both
   the Blackwell and the RTX 5090. That breaks the old "one
   service per GPU" partition; we need a cleaner mutex story.
3. MLflow was top-level but only `rl-2048` actually uses it.
   Compiler doesn't track experiments through MLflow (per-run
   artifacts under `${STORAGE_ROOT}/labs/wiki-bench/experiments/`),
   ingest doesn't either. MLflow at the root was implying a
   shared dependency that wasn't real.

The operator pushed for a "physical lab" metaphor: each lab is a
room with its own instruments, max self-contained, where you walk
in and find everything you need. caddy and mlflow stop being
shared infra, become per-lab kit.

## Decision

**Move every GPU-using subsystem under `labs/<slug>/`.** Each
lab is fully self-contained:

```
forge/
├── docs/                          ← repo-level docs + ADRs
├── labs/
│   ├── wiki-compiler/    ← was forge/inference/  — vLLM serving
│   │   ├── SPEC.md
│   │   ├── docker-compose.yml
│   │   ├── caddy/                 ← own caddy (binds 80/443)
│   │   │   ├── Caddyfile
│   │   │   └── docker-compose.yml
│   │   └── docs/adr/
│   ├── wiki-ingest/      ← was forge/kurpatov-wiki/  — transcribe
│   │   ├── SPEC.md, Dockerfile*, docker-compose.yml
│   │   ├── caddy/
│   │   └── docs/adr/
│   ├── wiki-bench/       ← was the standalone repo — agent harness
│   │   ├── SPEC.md, Dockerfile, docker-compose.yml
│   │   ├── configs/models.yml     ← bench-as-battery config
│   │   ├── run.sh, run-battery.sh
│   │   └── docs/adr/
│   └── rl-2048/                   ← was forge/rl-2048/  — GRPO sandbox
│       ├── SPEC.md, Dockerfile, docker-compose.yml
│       ├── caddy/
│       ├── mlflow/                ← MLflow now lives inside rl-2048
│       │   ├── docker-compose.yml
│       │   └── data/
│       └── notebooks/
├── scripts/                       ← cross-lab tooling (smoke, push-sources)
├── tests/
├── common.mk                      ← shared Make machinery
├── Makefile                       ← labs/<lab> dispatcher
├── CLAUDE.md
└── README.md
```

### Naming choices
- **`labs/`** beats `experiments/`, `usecases/`, `workspaces/`.
  An "experiment" is a single run/trial (in `wiki-bench`,
  e.g. "experiment 148 = qwen3.6-27b-fp8 on 2026-04-25"). A "lab"
  is the room those experiments happen in. Reusing the word
  "experiment" for the room would be confusing.
- **`wiki-compiler`** beats `-inference`, `-author`. The
  inference-server is just the instrument; the *purpose* is to
  compile raw transcripts into wiki articles. The compiler
  metaphor (raw → wiki, like source → binary) makes the bench
  lab's job legible too: it tests different compilers on the
  same source set.
- **`wiki-bench`** keeps the existing repo name; gets
  imported here.
- **`rl-2048`** unchanged.

### Per-lab caddy
Each lab owns its own caddy with its own `Caddyfile` and
`docker-compose.yml`. Caddy data (cert state, config) lives at
`${STORAGE_ROOT}/labs/<lab>/caddy-{data,config}/` so cert reissue
doesn't collide across labs.

This means **only one lab's caddy can hold ports 80/443 at a
time** — labs become mutex on the host port. We accept this:
- `wiki-bench` doesn't run a caddy (it's a client of
  `wiki-compiler`'s endpoint), so compiler + bench can
  co-run.
- All other lab combinations are already mutex by GPU anyway
  once we go dual-GPU TP, so the port mutex doesn't add
  meaningful constraint.

### MLflow inside rl-2048
`mlflow/` moves from `forge/mlflow/` to
`forge/labs/rl-2048/mlflow/`. Storage at
`${STORAGE_ROOT}/labs/rl-2048/mlruns/`. Brought up by
`make rl-2048` automatically (the lab's Makefile chains it).
MLflow's caddy site block (`mlflow.*` domain) lives in
rl-2048's `caddy/Caddyfile` alongside `jupyter-rl-2048.*`.

### Storage layout
```
${STORAGE_ROOT}/
├── shared/
│   └── models/                          ← HF cache, shared by every lab
└── labs/
    ├── wiki-compiler/{caddy-data,caddy-config}/
    ├── wiki-ingest/{sources,vault/raw,checkpoints,caddy-data,caddy-config}/
    ├── wiki-bench/experiments/<NN-timestamp-slug>/
    └── rl-2048/{checkpoints,mlruns,caddy-data,caddy-config}/
```

The HF cache stays shared because pulling `Qwen/Qwen3.6-27B-FP8`
twice (once for compiler, once for rl-2048) would waste 30 GB.
Self-contained "labs" doesn't have to mean self-contained
caches — model weights are read-only public artifacts.

## Consequences

**Positive.**
- One mental model: a forge contains labs; a lab is a room with
  every tool the experiment needs. New collaborators can read
  one lab's `SPEC.md` + `docs/adr/` and understand it without
  cross-lab dependencies.
- Bench harness joins forge instead of being a separate repo to
  remember. Single source of truth for everything in this lab.
- MLflow becomes optional infra — only spun up when its lab
  (rl-2048) is active. Saves a permanent container slot.
- Adding a new lab is a localized change: copy a template lab
  folder, edit, register in root Makefile's `LABS :=` line.

**Negative / accepted.**
- Lab-mutex on ports 80/443 means once-co-running services
  (`mlflow` + `inference` + `jupyter-kurpatov-wiki` simultaneously
  reachable) become serialized. We accept because: (a) the GPU
  mutex was about to enforce it anyway with dual-GPU TP, and
  (b) cross-lab work is rare enough that the operator can
  schedule.
- Migration: existing `${STORAGE_ROOT}/{models,kurpatov-wiki,
  mlflow,rl-2048}` directories need a one-time `mv` into the
  new layout. Same filesystem so the rename is instant; no
  data copy. Done in this commit.

## Touched files
- `git mv inference/ → phase-c-information-systems-architecture/application-architecture/wiki-compiler/`
- `git mv kurpatov-wiki/ → phase-c-information-systems-architecture/application-architecture/wiki-ingest/`
- `git mv rl-2048/ → phase-c-information-systems-architecture/application-architecture/rl-2048/`
- `git mv mlflow/ → phase-c-information-systems-architecture/application-architecture/rl-2048/mlflow/`
- `git rm -rf caddy/`
- New per-lab `caddy/` folders with extracted site blocks.
- Compose volume paths updated: `${STORAGE_ROOT}/models →
  /shared/models`, `${STORAGE_ROOT}/kurpatov-wiki/ → /labs/
  wiki-ingest/`, etc.
- Root Makefile rewritten as labs/ dispatcher.
- `common.mk` now finds forge root via `git rev-parse
  --show-toplevel`, so it works at any nesting depth.
- New top-level ADR (this file).
- CLAUDE.md, README.md, phase-d-technology-architecture/architecture.md updated.
- `wiki-bench` repo content imported under
  `phase-c-information-systems-architecture/application-architecture/wiki-bench/` (separate commit / subtree).


## Measurable motivation chain (OKRs)
Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: original `labs/` dir conflated multi-tenant
  Caddy + per-Lab compose; broke P4 mutex on :80/:443.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95). Realises Service-operation Capability (clean per-Lab tenancy).
- **Outcome**: each Lab self-contained under
  phase-c-…/application-architecture/<lab>/; Caddy mux per
  Lab.
- **Measurement source**: quality-ledger: pre_prod_share (per ADR 0021)
