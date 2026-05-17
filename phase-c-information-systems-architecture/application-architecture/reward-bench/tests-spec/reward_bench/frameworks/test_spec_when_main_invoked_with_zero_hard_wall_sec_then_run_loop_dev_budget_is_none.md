# `test_when_main_invoked_with_zero_hard_wall_sec_then_run_loop_dev_budget_is_none`

Pins back-compat: when canonical `hard_wall_sec=0.0` (cap disabled), `main()` passes `dev_hard_wall_sec=None` so the dev path uses the module default `DEV_HARD_WALL_S` (30s).

## Contract

- **Arrange**: Same monkeypatch pattern: `run_loop` recorder, stubbed `ensure_serving_model`, `score_submission`.
- **Act**: `main(model_id='qwen3.6-27b-awq', config=BenchConfig(max_iters=1, n_trials=1, hard_wall_sec=0.0))`.
- **Assert**: `captured['dev_hard_wall_sec'] is None`.

## Model client injection point

- **Seam**: `run_loop` (monkeypatched in main_mod).
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_main.py`](../../../tests/reward_bench/frameworks/test_main.py)::`test_when_main_invoked_with_zero_hard_wall_sec_then_run_loop_dev_budget_is_none`.

## Runtime scope

> **Runtime scope**: unit only.
