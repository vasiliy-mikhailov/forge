# mlflow — experiment tracking

## Purpose
Single tracking server for all ML experiments on this machine.

- Log params / metrics / artifacts from training (rl-2048, future
  kurpatov-wiki experiments with LLM summarization).
- Provide a UI I can hit from a browser to quickly compare runs.

## Non-goals
- Does not store datasets or entire models as artifacts for production
  rollout. Big checkpoints live under `${STORAGE_ROOT}/<service>/checkpoints`.
- No model registry / model serving. Intentionally out of scope.

## Architecture
Container `ghcr.io/mlflow/mlflow:v2.14.3`, listening on `:5000`, only
exposed externally via caddy (`MLFLOW_DOMAIN`). Backing store is SQLite on
SSD (`./data/mlflow.db`), artifacts on the big disk
(`${STORAGE_ROOT}/labs/rl-2048/mlflow/mlruns`).

Clients (jupyter-rl-2048, jupyter-kurpatov-wiki) reach tracking over HTTPS
with basic auth:

- `MLFLOW_TRACKING_URI=https://${MLFLOW_DOMAIN}`
- `MLFLOW_TRACKING_USERNAME=${BASIC_AUTH_USER}`
- `MLFLOW_TRACKING_PASSWORD=${MLFLOW_TRACKING_PASSWORD}`

## Data contracts
- `./data/mlflow.db` — SQLite database with tracking metadata. Not in git
  (excluded via `.gitignore`). Survives container restart; losing it means
  losing experiment history.
- `${STORAGE_ROOT}/labs/rl-2048/mlflow/mlruns` — binary artifacts (params, metrics as
  files, logged models). The path must exist before start (`make setup`).

## Invariants
1. The SQLite file must not be opened by multiple writers — mlflow can't
   do writer concurrency over sqlite anyway, and we have no second writer.
2. If `mlflow-data/` is lost, the backend just initializes an empty DB and
   references to old artifacts become dangling.
3. Image version is pinned by tag `v2.14.3` — no `latest`, for
   reproducibility.

## Status
Production. Stable.

## Open questions
- Move to Postgres? SQLite is fine with a single user and plenty of
  headroom.
- Turn on mlflow's own auth instead of basic auth at the proxy? Overkill
  for now.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain inherited from the lab's AGENTS.md.
