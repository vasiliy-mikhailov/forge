# `test_when_load_models_missing_top_key_then_value_error`

Pins the error branch: a yaml file without the top-level `models:` key raises `ValueError` with a message mentioning `models`.

## Contract

- **Arrange**: tmp yml with `other_key: []` only.
- **Act**: `load_models(yml)` inside `pytest.raises(ValueError, match='models')`.
- **Assert**: the raise happens; the error message matches `'models'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_run_battery.py`](../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_load_models_missing_top_key_then_value_error`.

## Runtime scope

> **Runtime scope**: unit only.
