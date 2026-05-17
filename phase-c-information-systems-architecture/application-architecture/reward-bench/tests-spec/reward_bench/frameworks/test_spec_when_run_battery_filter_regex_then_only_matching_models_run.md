# `test_when_run_battery_filter_regex_then_only_matching_models_run`

Pins end-to-end filter-regex behaviour through `run_battery`: only matching models reach the runner.

## Contract

- **Arrange**: tmp yml with `[qwen-27b, qwen-32b, llama-70b]`. Recorder runner.
- **Act**: `run_battery(tier=1, task='2048', registry_path=yml, filter_regex='qwen', runner=recorder)`.
- **Assert**: `calls == ['qwen-27b', 'qwen-32b']`.

## Model client injection point

- **Seam**: `runner` callable injected per-test.
- **Mode**: fake (recorder).

Test code: [`../../../tests/reward_bench/frameworks/test_run_battery.py`](../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_run_battery_filter_regex_then_only_matching_models_run`.

## Runtime scope

> **Runtime scope**: unit only.
