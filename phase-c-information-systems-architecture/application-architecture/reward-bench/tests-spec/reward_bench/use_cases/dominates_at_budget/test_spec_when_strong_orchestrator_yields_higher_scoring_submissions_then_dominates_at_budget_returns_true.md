# `test_when_strong_orchestrator_yields_higher_scoring_submissions_then_dominates_at_budget_returns_true`

Pins the §7 dominance harness primitive per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

`dominates_at_budget(strong, weak, env, cfg, walltime_budget_sec)`
runs both `Orchestrator`s under the same `(env, cfg, t)` and returns
True iff `best_score(strong.orchestrate(...), t)` exceeds
`best_score(weak.orchestrate(...), t)`. This is the harness the
named fitness test
`test_when_orchestrators_compared_at_same_time_budget_then_subagent_per_iter_score_dominates_ralph_single_context`
calls; this cycle pins it with `FakeOrchestrator`s so the harness
shape is provable independent of any real second strategy.

- **Arrange**: `strong = FakeOrchestrator(submissions=(s100,))` and
  `weak = FakeOrchestrator(submissions=(s10,))`, where the
  submissions differ only in score (100 vs 10) and both fit the
  walltime budget.
- **Act**: `dominates_at_budget(strong, weak, env=None, cfg=None,
  walltime_budget_sec=10.0)`.
- **Assert**: returns `True`.

Test code: [`../../../../tests/reward_bench/use_cases/test_dominates_at_budget.py`](../../../../tests/reward_bench/use_cases/test_dominates_at_budget.py)::`test_when_strong_orchestrator_yields_higher_scoring_submissions_then_dominates_at_budget_returns_true`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — harness composition over two FakeOrchestrators; no runtime boundary involved.
