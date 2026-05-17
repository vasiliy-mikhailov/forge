# `test_when_canonical_battery_filter_regex_then_only_matching_models_run`

Pins `filter_regex` narrowing inside `run_canonical_battery`: only models whose `id` matches the regex are scheduled.

## Contract

- **Arrange**: tmp yml with `[qwen-27b, llama-70b]`; recorder runner.
- **Act**: `run_canonical_battery(n_trials=1, registry_path=yml, experiments_root=tmp_path/'exp', filter_regex='qwen', runner=recorder)`.
- **Assert**: `calls == ['qwen-27b']`.

## Model client injection point

- **Seam**: injected `runner`.
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_filter_regex_then_only_matching_models_run`.

## Runtime scope

> **Runtime scope**: unit only.
