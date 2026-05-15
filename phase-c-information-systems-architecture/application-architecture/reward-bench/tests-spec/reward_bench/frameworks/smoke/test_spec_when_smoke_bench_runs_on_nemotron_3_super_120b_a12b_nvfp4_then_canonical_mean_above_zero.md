# `test_when_smoke_bench_runs_on_nemotron_3_super_120b_a12b_nvfp4_then_canonical_mean_above_zero`

Pins the **smoke screen** per [ADR 0009 v2](
../../../../docs/adr/0009-multi-model-smoke-bench-convention.md)
for `ModelTarget(id='nemotron-3-super-120b-a12b-nvfp4',
hf_path='nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4',
served_name='nemotron-3-super-120b-a12b-nvfp4',
max_model_len=32768,
tool_call_parser='hermes')`.

- **Arrange**: vLLM container `reward-bench-vllm` swapped to serve
  `nemotron-3-super-120b-a12b-nvfp4` via
  [`ensure_serving_model(target)`](../../../../src/tier1/inference.py)
  (cycle 42).
- **Act**: `result = main(model_id='nemotron-3-super-120b-a12b-nvfp4',
  config=SMOKE_CONFIG)` with
  `SMOKE_CONFIG = BenchConfig(max_iters=100, n_trials=1,`
  `temperature=0.7, finish_floor=0.0, hard_wall_sec=60.0,`
  `smoke_early_stop=True)` (cycle-76 ADR 0009 v2 — 100-iter
  cap with bench-forced early-stop on first `dev_mean > 0`).
- **Assert**: `result.mean_score > 0` — i.e. the model produced
  a submission that played at least one canonical seed to a
  non-zero score.

- **Artifact**: `experiments/2026-05-15-smoke-nemotron-3-super-120b-a12b-nvfp4.json`,
  recording `model_id`, `config`, `mean_score`, `median_score`,
  `max_max_tile`, `n_games`, `aggregate_walltime_sec`,
  `solver_protocol_valid`.

Per [ADR 0009 v2](../../../../docs/adr/0009-multi-model-smoke-bench-convention.md),
a `canonical_mean == 0.0` result under the v2 convention is
treated as a **bug signal**, not a model verdict — candidate
causes: tool-call parser mismatch, tokenizer issue, dev/canonical
budget asymmetry (cycle 77 deferred), payload data drift, etc.
Each such FAIL triggers a per-model investigation cycle.

Test code: parametrised in
[`tests/reward_bench/frameworks/smoke/test_smoke_all_models.py`](../../../../tests/reward_bench/frameworks/smoke/test_smoke_all_models.py).
