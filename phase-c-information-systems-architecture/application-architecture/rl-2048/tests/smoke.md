# Smoke — rl-2048

Source of truth for [`./smoke.sh`](smoke.sh). Helpers come from
[`../../../../scripts/smoke-lib.sh`](../../../../scripts/smoke-lib.sh).

## Preconditions

- Lab is up: `make rl-2048`. Three containers (`jupyter-rl-2048`,
  `mlflow`, `rl-2048-caddy`).
- `forge/.env` has: `BASIC_AUTH_USER`, `MLFLOW_TRACKING_PASSWORD`
  (caddy basic-auth plaintext), `MLFLOW_DOMAIN`,
  `JUPYTER_RL_2048_DOMAIN`, `RL_2048_GPU_UUID`.

## Section 1 — containers up

### container up: jupyter-rl-2048 / mlflow / rl-2048-caddy

**Goal.** All three lab containers are running.

**Signals.** `docker ps` row matches name exactly, status starts with
`Up`.

## Section 2 — GPU partitioning

### jupyter-rl-2048 pinned to RL_2048_GPU_UUID

**Goal.** The jupyter container sees only the declared GPU. No
leakage from the kurpatov-wiki GPU.

**Signals.** `docker exec jupyter-rl-2048 nvidia-smi --query-gpu=uuid
--format=csv,noheader` (whitespace-stripped) equals
`$RL_2048_GPU_UUID`.

## Section 3 — torch.cuda matmul

### torch.cuda matmul inside jupyter-rl-2048

**Goal.** GPU is not just visible but actually usable for compute.

**Signals.** Same as ingest's section 3 — `python -c <snippet>` with
1024×1024 matmul on CUDA, exit 0.

**Edge cases.** Same OOM caveat — keep tensors small.

## Section 4 — caddy basic auth

### mlflow / jupyter-rl-2048 via caddy

**Goal.** Both public hostnames are fronted by caddy with basic auth.
Unauth → 401; auth → backend.

**Signals.**
- `curl https://$MLFLOW_DOMAIN/` → 401; with `-u` → 200 (mlflow
  landing page).
- `curl https://$JUPYTER_RL_2048_DOMAIN/` → 401; with `-u` → 200 or
  302 (jupyter redirects).

**Edge cases.** Same as ingest's section 4 — plaintext password is
`MLFLOW_TRACKING_PASSWORD`, `--max-time 8`, never log the full `-u`.

## Section 5 — mlflow REST API

### mlflow /api/2.0/mlflow/experiments/search

**Goal.** mlflow is not just reachable but actually answering API
calls with valid JSON. The basic-auth pass alone isn't enough — caddy
could be 200ing a stale cache or a misrouted backend.

**Signals.** `POST https://$MLFLOW_DOMAIN/api/2.0/mlflow/experiments/search`
body `{"max_results":1}`, basic auth, returns a body containing
`"experiments"`.

**Edge cases.**
- Substring match is deliberately loose — we don't want smoke breaking
  on minor JSON shape changes between mlflow versions. If the
  top-level key ever changes, update both this doc and the script in
  one commit.
- Failure message truncates the response to 200 chars to avoid
  flooding the terminal on a misrouted backend (which can return MB
  of HTML).
- API rejects form-encoded bodies; must use POST + Content-Type
  application/json.

## Known gaps

- mlflow stores artifacts under `${STORAGE_ROOT}/labs/rl-2048/mlruns`
  — not asserted that this volume mount is correct.
- No assertion that GRPO/PPO trainer notebook can actually
  import-+-instantiate the model classes; that's a build-time concern
  (Dockerfile), not a smoke concern.
