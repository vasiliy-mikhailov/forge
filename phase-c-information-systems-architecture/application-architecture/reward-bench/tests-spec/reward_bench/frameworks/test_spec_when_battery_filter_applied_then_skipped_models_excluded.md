# `test_when_battery_filter_applied_then_skipped_models_excluded`

Pins `select_battery`'s filter: entries with `bench_skip: True` are dropped; missing `bench_skip` key counts as not-skipped; original order preserved.

## Contract

- **Arrange**: list of 5 dicts: `[{id:'a-1',bench_skip:False},{id:'b-2',bench_skip:True},{id:'c-3'},{id:'d-4',bench_skip:True},{id:'e-5',bench_skip:False}]`.
- **Act**: `picks = select_battery(models)`.
- **Assert**: `[m['id'] for m in picks] == ['a-1', 'c-3', 'e-5']`.

## Model client injection point

- **Seam**: none — pure function.
- **Mode**: n/a

Test code: [`../../../tests/reward_bench/frameworks/test_run_battery.py`](../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_battery_filter_applied_then_skipped_models_excluded`.

## Runtime scope

> **Runtime scope**: unit only.
