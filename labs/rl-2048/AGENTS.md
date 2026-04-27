# rl-2048 — agent context

This file follows the same Phase A-H structure as forge-level
`AGENTS.md`. Read forge-level first for cross-cutting rules; this
file is scoped to the rl-2048 lab.

## Phase A — Architecture Vision

**Vision (lab-scoped).** Explore "AI writes programs from verifiable
rewards" using 2048 as the first verifiable-reward domain. The product
is the methodology + harness; future siblings (other RLVR domains)
plug in alongside.

**Lab-scoped stakeholders.**

- **Architect of record** (forge-wide).
- **Lab consumer** — currently the architect (no external users).

**Lab-scoped drivers.**

- Time spent hand-coding solvers for verifiable-reward problems
  (the meta-driver for this whole lab).
- The wiki product is the *information-consumption* sibling; rl-2048
  is the *program-synthesis* sibling. Both serve the same
  forge-level goal: save human time on cognitive work.

**Lab-scoped goals.**

- **Falsifiable 2048-solver-quality metric** locked + a baseline
  run recorded in MLflow.
- **First end-to-end RLVR loop** that produces a checkpoint better
  than a hand-coded baseline.

**Lab-scoped principles.**

- The Blackwell hosts compiler OR rl-2048, not both. Mutex.
- MLflow SQLite is single-writer; one trainer at a time.
- `.ipynb` files are NOT committed; mature notebooks port to
  `.py` modules.
- Large checkpoints (`.pt`, `.bin`) live under `${STORAGE_ROOT}`,
  never in git.

## Phase B — Business Architecture

The wiki and rl-2048 are different products with different
quality-dimension slates:

| Capability                  | Quality dimension                              |
|-----------------------------|------------------------------------------------|
| Solve 2048 faster than hand-coded baselines | Score distribution; wall-clock per board (TBD — falsifiable metric to be locked) |
| RLVR training loop         | Sample efficiency; programmer-hours saved per program produced (TBD) |
| Notebook-driven experimentation | Time from idea to falsifiable result (TBD) |

(All "TBD" — rl-2048 is in the Jupyter-sandbox phase, pre-spec.)

## Phase C — Information Systems Architecture

(In flux. Currently:)

- **Game traces:** state-action-reward tuples from 2048 environment
  rollouts.
- **Trained policies:** PyTorch checkpoints in
  `${STORAGE_ROOT}/labs/rl-2048/checkpoints/`.
- **MLflow run records:** `${STORAGE_ROOT}/labs/rl-2048/mlruns/`
  (the SQLite + artifact tree that `mlflow ui` reads).

## Phase D — Technology Architecture

**Service: Notebook sandbox** (consumer: rl-2048 only).

- Component: Jupyter (in `labs/rl-2048/jupyter/`).
- Component: caddy 2 at `jupyter-rl-2048.mikhailov.tech`.

**Service: ML training tracking** (consumer: rl-2048 only).

- Component: MLflow (in `labs/rl-2048/mlflow/` — the mlflow service
  used to live at forge top-level; it moved here when rl-2048 was
  identified as the only consumer).
- Component: caddy 2 at `mlflow.mikhailov.tech`.

**Service: LoRA / RFT fine-tuning** (consumer: rl-2048 only;
*planned*, not yet active).

- Component: unsloth (planned).

L1: Jupyter sandbox, MLflow tracking. Working but no methodology
locked yet.

L2: TBD when STATE-OF-THE-LAB.md is written. Likely first L2 is
"falsifiable 2048-solver-quality metric locked + a baseline run
recorded in MLflow".

## Phase E — Opportunities and Solutions

Gap analysis for this lab — what capabilities are not yet at Level 2.
If a `STATE-OF-THE-LAB.md` exists, it is the canonical gap audit;
otherwise the Phase H trajectories table below stands in.

## Phase F — Migration Planning

Active experiment specs at `docs/experiments/<id>.md` are the
sequenced work packages closing those gaps. Only Active and
Closed-but-still-cited experiments are kept; superseded ones go to
git history per Phase H.


(None active. Lab is in pre-methodology phase.)

## Phase G — Implementation Governance

- **GPU choice:** the Blackwell hosts rl-2048 *or*
  `kurpatov-wiki-compiler`, not both. The two labs are mutex on the
  Blackwell GPU UUID (`KURPATOV_WIKI_GPU_UUID` /
  `RL_2048_GPU_UUID` in `.env`). Bring one down before bringing the
  other up.
- **MLflow SQLite is single-writer.** Don't run two trainers writing
  to it concurrently — the SQLite will lock or corrupt. (Forge-level
  "What NOT to do" #1.)
- **`.ipynb` files are NOT committed.** Notebooks are personal
  scratch space; once an experiment matures, port the code into
  proper `.py` modules under `src/` and reference notebooks only as
  exploratory artefacts.
- **Large checkpoints (`.pt`, `.bin`) are NOT committed.** Live
  under `${STORAGE_ROOT}/labs/rl-2048/checkpoints/`.
- **MLflow artifact paths are stable.** Don't restructure
  `mlruns/` directory layout — `mlflow ui` and downstream tooling
  encode the paths.

## Phase H — Architecture Change Management

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| Solve 2048 faster than hand-coded baselines | TBD — no falsifiable quality metric locked | locked metric + baseline run recorded in MLflow | (TBD) |
| RLVR training loop | (none) | first end-to-end loop produces a checkpoint | (TBD) |

## Cross-references

- Forge-level: `forge/CLAUDE.md` Phase A (Motivation: rl-2048 is
  the program-optimization sibling of Kurpatov Wiki under the same
  "save human time on cognitive work" goal).
- Forge-level Phase D: ML training tracking + Notebook sandbox +
  LoRA-fine-tuning rows in the service-tenancy table.
- ADR 0007 (forge labs-restructure): why mlflow lives inside this
  lab now instead of at forge top-level.
