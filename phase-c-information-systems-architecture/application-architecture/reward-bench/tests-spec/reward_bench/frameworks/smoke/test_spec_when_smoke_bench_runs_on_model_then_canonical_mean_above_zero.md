# `test_when_smoke_bench_runs_on_model_then_canonical_mean_above_zero`

Pins the **smoke screen** per
[ADR 0009](../../../../docs/adr/0009-multi-model-smoke-bench-convention.md)
for every model in
[`MODEL_REGISTRY`](../../../../src/reward_bench/use_cases/model_registry.py).

Parametrised in
[`tests/reward_bench/frameworks/smoke/test_smoke_all_models.py`](../../../../tests/reward_bench/frameworks/smoke/test_smoke_all_models.py)
via `@pytest.mark.parametrize("target", MODEL_REGISTRY, ids=lambda t: t.id)`.
Every parameter value runs the SAME contract; this spec describes that one
contract once. Per the cycle-110/112 CATS rule, we do not fork a
per-model spec file — the registry IS the parameter list.

## Contract (per `target` in `MODEL_REGISTRY`)

- **Arrange**: vLLM container `reward-bench-vllm` swapped to serve
  `target.served_name` via
  [`ensure_serving_model(target)`](../../../../src/tier1/inference.py).
- **Act**: `result = main(model_id=target.id, config=SMOKE_CONFIG)`
  with `SMOKE_CONFIG = BenchConfig(max_iters=100, n_trials=1,
  temperature=0.7, finish_floor=0.0, hard_wall_sec=60.0,
  smoke_early_stop=True)` — ADR 0009 100-iter cap with bench-forced
  early-stop on first `dev_mean > 0`.
- **Assert**: `(result.best_dev_mean or 0) > 0` — i.e. the model
  produced AT LEAST ONE `execute_submission` observation whose dev
  games scored above zero.

- **Artifact**: `experiments/2026-05-15-smoke-<target.id>.json`,
  recording `best_dev_mean` (PRIMARY signal), plus informational
  `mean_score` (canonical), `median_score`, `max_max_tile`,
  `n_games`, `aggregate_walltime_sec`, `solver_protocol_valid`.

Per ADR 0009, a `best_dev_mean == 0` (or None) result is a BUG signal.
Candidate causes: tool-call parser mismatch, the model emitting only
`view` / planning tools and never trying `execute_submission`,
tokenizer truncation, payload drift, registry data drift. Each such
FAIL triggers a per-model investigation cycle — the spec stays
parametrised; the investigation produces an ADR (or a new spec only
if the per-model behaviour is genuinely different from "smoke screen
passes").

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **smoke** — opt-in via `pytest -m smoke`; uses live vLLM.
- **Override**: pass `model_client=` per-test, OR mark
  `@pytest.mark.live` / `@pytest.mark.no_fake`.
