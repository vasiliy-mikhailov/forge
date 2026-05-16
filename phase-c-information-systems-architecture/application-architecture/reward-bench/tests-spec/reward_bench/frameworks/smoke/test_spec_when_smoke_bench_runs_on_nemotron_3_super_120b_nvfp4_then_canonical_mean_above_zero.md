# `test_when_smoke_bench_runs_on_nemotron_3_super_120b_nvfp4_then_canonical_mean_above_zero`

Pins the **smoke screen** per [ADR 0009 v3](
../../../../docs/adr/0009-multi-model-smoke-bench-convention.md)
for `ModelTarget(id='nemotron-3-super-120b-nvfp4',
hf_path='nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4',
served_name='nemotron-3-super-120b-nvfp4',
max_model_len=16384,
tool_call_parser='hermes')`.

Test name retains the historical filename for git continuity;
the asserted contract is now v3 (best_dev_mean > 0, NOT
canonical_mean > 0).

- **Arrange**: vLLM container `reward-bench-vllm` swapped to serve
  `nemotron-3-super-120b-nvfp4` via
  [`ensure_serving_model(target)`](../../../../src/tier1/inference.py)
  (cycle 42).
- **Act**: `result = main(model_id='nemotron-3-super-120b-nvfp4',
  config=SMOKE_CONFIG)` with
  `SMOKE_CONFIG = BenchConfig(max_iters=100, n_trials=1,`
  `temperature=0.7, finish_floor=0.0, hard_wall_sec=60.0,`
  `smoke_early_stop=True)` (cycle 76, ADR 0009 v2 — 100-iter cap
  with bench-forced early-stop on first `dev_mean > 0`).
- **Assert (cycle 79, ADR 0009 v3)**: `(result.best_dev_mean or 0) > 0`
  — i.e. the model produced AT LEAST ONE `execute_submission`
  observation whose dev games scored above zero.

- **Artifact**: `experiments/2026-05-15-smoke-nemotron-3-super-120b-nvfp4.json`,
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

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

