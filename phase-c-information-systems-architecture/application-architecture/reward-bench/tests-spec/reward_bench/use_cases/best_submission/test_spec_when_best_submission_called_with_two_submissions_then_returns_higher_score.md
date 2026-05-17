# `test_when_best_submission_called_with_two_submissions_then_returns_higher_score`

Pins the `argmax_by_score` primitive per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7:

    bench env cfg = argmaxBy (.score) (orchestrate env cfg)

`best_submission` is the pure reduction over an `Iterable[Submission]`.
The bench composes it with an `Orchestrator` to define the top-level
fitness target. Pure function — no IO, no env — because Submission
already carries its score (the orchestrator computes the score and
stores it on the Submission).

- **Arrange**: two `Submission` instances, `a` with `score=10.0` and
  `b` with `score=20.0`.
- **Act**: `best_submission([a, b])`.
- **Assert**: returns `b` (`is b` — Submission is a frozen value
  object; the function returns the same instance, not a copy).

Test code: [`../../../../tests/reward_bench/use_cases/test_best_submission.py`](../../../../tests/reward_bench/use_cases/test_best_submission.py)::`test_when_best_submission_called_with_two_submissions_then_returns_higher_score`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — pure reduction over an iterable; no runtime boundary involved.
