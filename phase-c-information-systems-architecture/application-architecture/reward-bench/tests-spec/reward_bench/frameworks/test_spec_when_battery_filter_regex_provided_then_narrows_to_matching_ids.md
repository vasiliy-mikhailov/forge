# `test_when_battery_filter_regex_provided_then_narrows_to_matching_ids`

Pins `select_battery`'s optional `filter_regex` narrowing on the `id` field. `bench_skip: True` still drops models even when they match the regex.

## Contract

- **Arrange**: 5 models: two `qwen3.6-27b-*`, one `llama-3.3-70b-nvfp4`, `gpt-oss-20b` (not skipped), `gpt-oss-120b` (`bench_skip: True`).
- **Act**: `select_battery(models, filter_regex='27b')` and `select_battery(models, filter_regex='gpt-oss')`.
- **Assert**: first returns the two `27b` ids; second returns only `gpt-oss-20b` (the 120b is dropped by skip even though regex matches).

## Model client injection point

- **Seam**: none — pure function.
- **Mode**: n/a

Test code: [`../../../tests/reward_bench/frameworks/test_run_battery.py`](../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_battery_filter_regex_provided_then_narrows_to_matching_ids`.

## Runtime scope

> **Runtime scope**: unit only.
