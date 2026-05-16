# `test_when_main_completes_then_attempt_result_best_dev_mean_matches_run_loop_return`

Pins the **best_dev_mean wiring** per [ADR 0009 v3](../../../../docs/adr/0009-multi-model-smoke-bench-convention.md):
when [`main()`](../../../../src/reward_bench/frameworks/main.py) finishes, the
returned `AttemptResult.best_dev_mean` equals the `best_dev_mean` field
that [`run_loop`](../../../../src/tier1/agent_loop.py) returned. This is
the primary signal smoke tests assert on (cycle 79 v3).

- **Arrange**: monkeypatch `main`'s `ensure_serving_model`, `run_loop`,
  and write a stub submission so `score_submission` returns a normal
  `AttemptResult`. The fake `run_loop` returns
  `{'iterations': 5, 'messages': [...], 'finished': True, 'best_dev_mean': 1234.5}`.
- **Act**: `main(model_id='qwen3.6-27b-awq', config=BenchConfig(max_iters=1, n_trials=1))`.
- **Assert**: `result.best_dev_mean == 1234.5` (not None, propagated).

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

