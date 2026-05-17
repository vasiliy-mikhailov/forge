# `test_when_load_models_called_then_returns_yaml_list`

Pins `load_models`'s happy path: reads `models:` key from a yaml file and returns it as a list.

## Contract

- **Arrange**: tmp yml with `models:\n  - id: foo\n  - id: bar\n`.
- **Act**: `out = load_models(yml)`.
- **Assert**: `isinstance(out, list)`; `[m['id'] for m in out] == ['foo', 'bar']`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_run_battery.py`](../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_load_models_called_then_returns_yaml_list`.

## Runtime scope

> **Runtime scope**: unit only.
