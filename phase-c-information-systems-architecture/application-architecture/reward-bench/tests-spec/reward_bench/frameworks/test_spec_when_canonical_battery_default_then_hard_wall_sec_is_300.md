# `test_when_canonical_battery_default_then_hard_wall_sec_is_300`

Pins the default `canonical_hard_wall_sec=300.0` on `run_canonical_battery`'s signature.

## Contract

- **Arrange**: import `inspect`; read the function signature.
- **Act**: `sig.parameters['canonical_hard_wall_sec'].default`.
- **Assert**: `'canonical_hard_wall_sec' in sig.parameters` and `default == 300.0`.

## Model client injection point

- **Seam**: none — pure function.
- **Mode**: n/a

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_default_then_hard_wall_sec_is_300`.

## Runtime scope

> **Runtime scope**: unit only.
