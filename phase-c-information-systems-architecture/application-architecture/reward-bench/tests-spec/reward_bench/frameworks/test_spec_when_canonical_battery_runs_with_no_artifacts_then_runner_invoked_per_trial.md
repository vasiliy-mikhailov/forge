# `test_when_canonical_battery_runs_with_no_artifacts_then_runner_invoked_per_trial`

Pins the no-prior-artifacts branch of `run_canonical_battery`: every `(model, trial)` runs, in deterministic `[model0_trial0, ..., modelN_trialM]` order.

## Contract

- **Arrange**: tmp yml with `[a, b]`; recorder runner returning a synthetic artifact dict.
- **Act**: `run_canonical_battery(n_trials=3, registry_path=yml, experiments_root=tmp_path/'exp', runner=recorder)`.
- **Assert**: `calls == [('a',0),('a',1),('a',2),('b',0),('b',1),('b',2)]`.

## Model client injection point

- **Seam**: `runner` injected.
- **Mode**: fake (recorder).

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_runs_with_no_artifacts_then_runner_invoked_per_trial`.

## Runtime scope

> **Runtime scope**: unit only.
