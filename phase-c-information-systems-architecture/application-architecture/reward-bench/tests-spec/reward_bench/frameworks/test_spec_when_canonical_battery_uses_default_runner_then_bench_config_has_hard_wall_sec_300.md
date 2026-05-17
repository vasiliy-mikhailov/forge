# `test_when_canonical_battery_uses_default_runner_then_bench_config_has_hard_wall_sec_300`

Pins production-default-runner wiring: when no `runner` is passed, the closure constructs a `BenchConfig` with `hard_wall_sec=300.0` (the canonical default) and passes it to `main()`.

## Contract

- **Arrange**: tmp yml with `[bar]`. Monkeypatch `main_mod.main` with a `fake_main` that records `config` into `captured`. No `runner` arg.
- **Act**: `run_canonical_battery(n_trials=1, registry_path=yml, experiments_root=tmp_path/'exp')`.
- **Assert**: `captured['config']` is not None; `captured['config'].hard_wall_sec == 300.0`.

## Model client injection point

- **Seam**: `main_mod.main` (monkeypatched).
- **Mode**: fake.

Test code: [`../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_uses_default_runner_then_bench_config_has_hard_wall_sec_300`.

## Runtime scope

> **Runtime scope**: unit only.
