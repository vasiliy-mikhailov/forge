# `test_when_main_invoked_with_nonzero_hard_wall_sec_then_run_loop_receives_scaled_dev_budget`

Pins the per-seed budget derivation: `dev_hard_wall_sec = config.hard_wall_sec * 5 / len(seeds)`. With canonical 60s + 20 seeds → dev=15.0s.

## Contract

- **Arrange**: Monkeypatch `run_loop` with a `fake_run_loop` recorder; stub `ensure_serving_model`, `VLLM_API_KEY`, `score_submission` to a synthetic `AttemptResult`.
- **Act**: `main(model_id='qwen3.6-27b-awq', seeds=range(1000,1020), config=BenchConfig(max_iters=1, n_trials=1, hard_wall_sec=60.0))`.
- **Assert**: `captured['dev_hard_wall_sec'] == 15.0`.

## Model client injection point

- **Seam**: `run_loop` (monkeypatched in main_mod).
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_main.py`](../../../tests/reward_bench/frameworks/test_main.py)::`test_when_main_invoked_with_nonzero_hard_wall_sec_then_run_loop_receives_scaled_dev_budget`.

## Runtime scope

> **Runtime scope**: unit only.
