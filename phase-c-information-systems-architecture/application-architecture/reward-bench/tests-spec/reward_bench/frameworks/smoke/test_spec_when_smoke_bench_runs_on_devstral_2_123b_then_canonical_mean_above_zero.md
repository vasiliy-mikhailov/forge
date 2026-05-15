# `test_when_smoke_bench_runs_on_devstral_2_123b_then_canonical_mean_above_zero`

Pins the **smoke screen** per [ADR 0009 v3](
../../../../docs/adr/0009-multi-model-smoke-bench-convention.md)
for `ModelTarget(id='devstral-2-123b',
hf_path='cyankiwi/Devstral-2-123B-Instruct-2512-AWQ-4bit',
served_name='devstral-2-123b',
max_model_len=131072,
tool_call_parser='mistral')`.

Test name retains the historical filename for git continuity;
the asserted contract is now v3 (best_dev_mean > 0, NOT
canonical_mean > 0).

- **Arrange**: vLLM container `reward-bench-vllm` swapped to serve
  `devstral-2-123b` via
  [`ensure_serving_model(target)`](../../../../src/tier1/inference.py)
  (cycle 42).
- **Act**: `result = main(model_id='devstral-2-123b',
  config=SMOKE_CONFIG)` with
  `SMOKE_CONFIG = BenchConfig(max_iters=100, n_trials=1,`
  `temperature=0.7, finish_floor=0.0, hard_wall_sec=60.0,`
  `smoke_early_stop=True)` (cycle 76, ADR 0009 v2 — 100-iter cap
  with bench-forced early-stop on first `dev_mean > 0`).
- **Assert (cycle 79, ADR 0009 v3)**: `(result.best_dev_mean or 0) > 0`
  — i.e. the model produced AT LEAST ONE `execute_submission`
  observation whose dev games scored above zero.

- **Artifact**: `experiments/2026-05-15-smoke-devstral-2-123b.json`,
  recording `best_dev_mean` (PRIMARY signal), plus informational
  `mean_score` (canonical), `median_score`, `max_max_tile`,
  `n_games`, `aggregate_walltime_sec`, `solver_protocol_valid`.

Per ADR 0009 v3, a `best_dev_mean == 0` (or None) result is a
BUG signal — candidate causes: tool-call parser mismatch, the
model emitting only `view` / planning tools and never trying
`execute_submission`, tokenizer truncation, payload drift,
registry data drift. Each such FAIL triggers a per-model
investigation cycle.

Test code: parametrised in
[`tests/reward_bench/frameworks/smoke/test_smoke_all_models.py`](../../../../tests/reward_bench/frameworks/smoke/test_smoke_all_models.py).
