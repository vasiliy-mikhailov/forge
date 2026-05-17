# `test_when_canonical_battery_completes_a_trial_then_artifact_written`

Pins the artifact-on-completion contract: a successful runner call writes the artifact JSON to `canonical_artifact_path(model, trial)`.

## Contract

- **Arrange**: tmp yml with one model `foo`; runner returning `{model_id:'foo', trial:0, mean_score:42.0, ...}`.
- **Act**: `run_canonical_battery(n_trials=1, registry_path=yml, experiments_root=exp, runner=recorder)`.
- **Assert**: `canonical_artifact_path('foo', 0, exp)` exists; loaded JSON has `mean_score == 42.0` and `trial == 0`.

## Model client injection point

- **Seam**: filesystem + injected `runner`.
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_completes_a_trial_then_artifact_written`.

## Runtime scope

> **Runtime scope**: unit only.
