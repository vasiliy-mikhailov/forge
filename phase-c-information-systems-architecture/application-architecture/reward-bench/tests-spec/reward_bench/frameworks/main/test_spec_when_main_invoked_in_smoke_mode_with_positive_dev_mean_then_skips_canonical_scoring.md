# `test_when_main_invoked_in_smoke_mode_with_positive_dev_mean_then_skips_canonical_scoring`
Pins the **canonical-skip optimisation** in
[`main()`](../../../../src/reward_bench/frameworks/main.py) v3 +.
When `config.smoke_early_stop` is True AND `run_loop` returns a
positive `best_dev_mean`, `main()` MUST NOT call `score_submission`.
Instead it returns an `AttemptResult` carrying just the
`best_dev_mean` (and informational zeros for the other fields).
Rationale: smoke's contract is "did the model
produce ANY working code?". The signal is `dev_mean > 0` from
`execute_submission`. The 60s+ canonical second-stage scoring is
pure overhead in smoke mode.
- **Arrange**: monkeypatch `main`'s `ensure_serving_model`, `run_loop`
 (returns `best_dev_mean=42.0`), `load_submission` (returns a stub
 module with a working Solver), and **the score_submission name**
 so we can detect whether it gets called.
- **Act**: `main(model_id='qwen3.6-27b-awq',
 config=BenchConfig(max_iters=1, n_trials=1, smoke_early_stop=True))`.
- **Assert**:
 - `score_submission` was **never called** (call count == 0).
 - `result.best_dev_mean == 42.0`.
 - `result.mean_score == 0.0` (informational zero).
 - `result.n_games == 0`.
Negative-control case (NOT smoke mode): unchanged. With
`smoke_early_stop=False`, `main()` calls `score_submission` as it
always has. (Pre-existing tests pin this.)
Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.

Test code: [`../../../../tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py)::`test_when_main_invoked_in_smoke_mode_with_positive_dev_mean_then_skips_canonical_scoring`.
