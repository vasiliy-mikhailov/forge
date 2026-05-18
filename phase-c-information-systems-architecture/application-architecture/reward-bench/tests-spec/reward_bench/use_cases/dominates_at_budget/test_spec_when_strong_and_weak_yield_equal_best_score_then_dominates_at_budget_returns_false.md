# `test_when_strong_and_weak_yield_equal_best_score_then_dominates_at_budget_returns_false`

Pins the strict `>` semantics of `dominates_at_budget` per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7. "Dominates" means *strictly better than*; a tie is not
domination. The §7 fitness gate
`test_when_orchestrators_compared_at_same_time_budget_then_
 subagent_per_iter_score_dominates_ralph_single_context` will
therefore fail on parity — the planned shape must beat the current
one, not merely match it.

- **Arrange**: two Submissions with identical scores (`50.0` each)
  and identical walltimes (well under budget). Wrap each in a
  `FakeOrchestrator` as `strong` and `weak`.
- **Act**: `dominates_at_budget(strong, weak, env=None, cfg=None,
  walltime_budget_sec=10.0)`.
- **Assert**: returns `False`.

Test code: [`../../../../tests/reward_bench/use_cases/test_dominates_at_budget.py`](../../../../tests/reward_bench/use_cases/test_dominates_at_budget.py)::`test_when_strong_and_weak_yield_equal_best_score_then_dominates_at_budget_returns_false`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — pure comparison over two FakeOrchestrators.
