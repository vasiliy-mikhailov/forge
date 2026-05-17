# `test_when_model_registry_inspected_then_size_matches_advertised_count`

Pins the size invariant of the Python `MODEL_REGISTRY` tuple. Currently 22 entries; mismatch indicates drift between the Python mirror and the YAML source of truth.

## Contract

- **Arrange**: no fixtures — `MODEL_REGISTRY` is a module-level tuple.
- **Act**: `n = len(MODEL_REGISTRY)`.
- **Assert**: `n == 22`.

## Model client injection point

- **Seam**: none — pure function.
- **Mode**: n/a

Test code: [`../../../tests/reward_bench/use_cases/test_model_registry.py`](../../../tests/reward_bench/use_cases/test_model_registry.py)::`test_when_model_registry_inspected_then_size_matches_advertised_count`.

## Runtime scope

> **Runtime scope**: unit only.
