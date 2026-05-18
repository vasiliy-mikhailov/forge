# `test_when_context_snapshot_constructed_then_carries_all_fields`

Pins the `ContextSnapshot` value type per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§2. The orchestrator builds one per iter from cumulative state and
hands it to the `SolutionGenerator`. Frozen so the SolutionGenerator
cannot mutate it; immutable so two orchestrators in a comparison
can share the same snapshot type without aliasing risk.

- **Arrange**: an `env_spec` string; a `best_so_far` `Submission`;
  a `history_digest` tuple of two `Submission`s; `iters_remaining=5`;
  `time_remaining_sec=120.0`; `budget_sec_per_seed=12.0`.
- **Act**: construct `ContextSnapshot(...)`.
- **Assert**: all six fields round-trip.

Test code: [`../../../../tests/reward_bench/entities/test_context_snapshot.py`](../../../../tests/reward_bench/entities/test_context_snapshot.py)::`test_when_context_snapshot_constructed_then_carries_all_fields`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default).

## Runtime scope

> **Runtime scope**: unit only — frozen-dataclass invariant.
