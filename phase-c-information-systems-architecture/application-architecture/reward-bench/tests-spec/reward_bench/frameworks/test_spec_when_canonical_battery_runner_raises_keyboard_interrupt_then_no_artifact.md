# `test_when_canonical_battery_runner_raises_keyboard_interrupt_then_no_artifact`

Pins Ctrl-C safety: when the runner raises `KeyboardInterrupt`, NO artifact is written for the interrupted `(model, trial)`. On a future resume the trial is re-attempted.

## Contract

- **Arrange**: tmp yml with `[only]`; runner that raises `KeyboardInterrupt`.
- **Act**: `run_canonical_battery(n_trials=2, registry_path=yml, experiments_root=exp, runner=raising_runner)` inside `pytest.raises(KeyboardInterrupt)`.
- **Assert**: `canonical_artifact_path('only', 0, ...)` does NOT exist after the raise.

## Model client injection point

- **Seam**: filesystem + injected `runner`.
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_runner_raises_keyboard_interrupt_then_no_artifact`.

## Runtime scope

> **Runtime scope**: unit only.
