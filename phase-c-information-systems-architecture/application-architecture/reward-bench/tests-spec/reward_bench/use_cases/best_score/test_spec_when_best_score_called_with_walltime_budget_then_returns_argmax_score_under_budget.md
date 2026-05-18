# `test_when_best_score_called_with_walltime_budget_then_returns_argmax_score_under_budget`

Pins the §7 fitness primitive per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md):

    best_score env cfg t =
        max { score env s
            | s in orchestrate env cfg,
              submission_walltime s <= t }

This cycle pins the pure reduction `best_score(submissions, t)`:
filter by `walltime_sec <= t`, then `max` over `score`. The dominance
test compares two orchestrators at the same `t`; this primitive is
how the comparison is computed.

- **Arrange**: three Submissions —
  `cheap_bad(score=10.0, walltime_sec=1.0)`,
  `expensive_great(score=100.0, walltime_sec=999.0)` (over budget),
  `cheap_good(score=50.0, walltime_sec=2.0)`.
- **Act**: `best_score([cheap_bad, expensive_great, cheap_good],
  walltime_budget_sec=10.0)`.
- **Assert**: `score == 50.0` (cheap_good wins;
  expensive_great is filtered out).

Test code: [`../../../../tests/reward_bench/use_cases/test_best_score.py`](../../../../tests/reward_bench/use_cases/test_best_score.py)::`test_when_best_score_called_with_walltime_budget_then_returns_argmax_score_under_budget`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — pure filter+reduce over an iterable; no runtime boundary involved.
