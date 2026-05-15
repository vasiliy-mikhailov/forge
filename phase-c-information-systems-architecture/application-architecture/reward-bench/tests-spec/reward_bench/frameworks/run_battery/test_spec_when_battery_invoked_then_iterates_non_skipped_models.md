# `test_when_battery_invoked_then_iterates_non_skipped_models`

Pins the **`make reward-battery`** contract from
[SPEC.md §Make targets](../../../../SPEC.md):

> make reward-battery TIER=<N> [--filter <regex>]
>     Iterate over every model in wiki-compiler/configs/models.yml with
>     bench_tier ≠ skip; run one attempt at the given TIER for each.

Cycle 78 ran this sweep manually via 22 per-model CATS tasks. Cycle 94
codifies it as
[`src/reward_bench/frameworks/run_battery.py`](../../../../src/reward_bench/frameworks/run_battery.py).

## Schema note

The registry schema has `bench_skip: bool` as the inclusion gate
(separate from `bench_tier: A|B|C|D` which classifies models by
hardware footprint). The SPEC text "bench_tier ≠ skip" predates this
split; the implemented rule is `bench_skip != True`.

## Filter function — `select_battery(models, filter_regex=None)`

- **Arrange**: a small in-memory model list mixing `bench_skip: True`,
  `bench_skip: False`, and entries without the key.
- **Act**: `select_battery(models)` and
  `select_battery(models, filter_regex='27b')`.
- **Assert**:
  - No-filter call drops only the `bench_skip: True` entries.
  - Regex-filter call further narrows to ids matching `27b`.
  - Registry order is preserved.

## Driver function — `run_battery(...)`

- **Arrange**: a tiny in-memory registry (3 models, one skipped), and
  a `runner` callable that records calls and returns rc=0.
- **Act**: `run_battery(tier=1, task='2048', registry_path=tmp_yml,
  runner=recorder)`.
- **Assert**:
  - Recorder was invoked exactly N times where N = non-skipped count.
  - Returned tuples are (model_id, returncode).
  - On a mixed-rc runner, the final return is non-zero only when ≥1
    runner call exits non-zero.

Test code: [`tests/reward_bench/frameworks/test_run_battery.py`](../../../../tests/reward_bench/frameworks/test_run_battery.py).
