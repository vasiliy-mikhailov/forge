# `test_when_smoke_bench_runs_on_devstral_2_123b_nvfp4_then_canonical_mean_above_zero`

Pins the **smoke screen** per [ADR 0009](
../../../../docs/adr/0009-multi-model-smoke-bench-convention.md)
for `ModelTarget(id='devstral-2-123b-nvfp4',
hf_path='BrainForge/Devstral-2-123B-Instruct-2512-NVFP4',
served_name='devstral-2-123b-nvfp4',
max_model_len=32768,
tool_call_parser='mistral')`.

- **Arrange**: vLLM container `reward-bench-vllm` swapped to serve
  `devstral-2-123b-nvfp4` via
  [`ensure_serving_model(target)`](../../../../src/tier1/inference.py)
  (cycle 42).
- **Act**: `result = main(model_id='devstral-2-123b-nvfp4',
  config=SMOKE_CONFIG)` with
  `SMOKE_CONFIG = BenchConfig(max_iters=10, n_trials=1,`
  `temperature=0.7, finish_floor=0.0, hard_wall_sec=60.0)`.
- **Assert**: `result.mean_score > 0` — i.e. the model produced
  a submission that played at least one canonical seed to a
  non-zero score.

- **Artifact**: `experiments/2026-05-14-smoke-devstral-2-123b-nvfp4.json`,
  recording `model_id`, `config`, `mean_score`, `median_score`,
  `max_max_tile`, `n_games`, `aggregate_walltime_sec`,
  `solver_protocol_valid`.

Per ADR 0009, a smoke FAIL on this model is reported truth, not
a bench correctness bug. The failure reason is captured in the
artifact's `mean_score / median_score / max_max_tile / games[*].final_state`
fields and rolled into the leaderboard row for `devstral-2-123b-nvfp4`.

Test code: parametrised in
[`tests/reward_bench/frameworks/smoke/test_smoke_all_models.py`](../../../../tests/reward_bench/frameworks/smoke/test_smoke_all_models.py).
