# `test_when_canonical_battery_override_then_caller_value_propagates`

Pins override propagation: `canonical_hard_wall_sec=600.0` passed by the caller flows through to the `BenchConfig` that the default-runner closure constructs.

## Contract

- **Arrange**: tmp yml with `[baz]`. Same `fake_main` recorder pattern.
- **Act**: `run_canonical_battery(n_trials=1, registry_path=yml, experiments_root=tmp_path/'exp', canonical_hard_wall_sec=600.0)`.
- **Assert**: `captured['config'].hard_wall_sec == 600.0`.

## Model client injection point

- **Seam**: `main_mod.main` (monkeypatched).
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_override_then_caller_value_propagates`.

## Runtime scope

> **Runtime scope**: unit only.
