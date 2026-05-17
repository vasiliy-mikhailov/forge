# `test_when_run_battery_called_then_runner_invoked_per_non_skipped_model`

Pins `run_battery` driver: invokes the injected `runner` callable once per non-skipped model, returns the list of `(model_id, returncode)` tuples in order.

## Contract

- **Arrange**: tmp yml with `models: [alpha (not skipped), beta (skipped), gamma (not skipped)]`. Recorder runner appending `model_id` and returning 0.
- **Act**: `run_battery(tier=1, task='2048', registry_path=yml, runner=recorder)`.
- **Assert**: `calls == ['alpha', 'gamma']`; `results == [('alpha', 0), ('gamma', 0)]`.

## Model client injection point

- **Seam**: `runner` callable injected per-test.
- **Mode**: fake (recorder).

Test code: [`../../../tests/reward_bench/frameworks/test_run_battery.py`](../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_run_battery_called_then_runner_invoked_per_non_skipped_model`.

## Runtime scope

> **Runtime scope**: unit only.
