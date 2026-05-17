# `test_when_run_battery_runner_returns_mixed_rc_then_all_calls_still_made`

Pins resilience: a non-zero `returncode` from one model does NOT short-circuit the battery — remaining models still run.

## Contract

- **Arrange**: tmp yml with `[a, b, c]` all not skipped. Recorder runner returning 2 for `b`, 0 for others.
- **Act**: `run_battery(tier=1, task='2048', registry_path=yml, runner=recorder)`.
- **Assert**: `calls == ['a', 'b', 'c']` (all three attempted); `results == [('a',0), ('b',2), ('c',0)]`.

## Model client injection point

- **Seam**: `runner` callable injected per-test.
- **Mode**: fake (recorder).

Test code: [`../../../tests/reward_bench/frameworks/test_run_battery.py`](../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_run_battery_runner_returns_mixed_rc_then_all_calls_still_made`.

## Runtime scope

> **Runtime scope**: unit only.
