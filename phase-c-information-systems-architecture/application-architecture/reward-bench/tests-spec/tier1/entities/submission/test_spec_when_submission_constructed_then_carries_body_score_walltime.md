# `test_when_submission_constructed_then_carries_body_score_walltime`

Pins the `Submission` entity per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7: `bench :: Env -> BenchConfig -> Submission`. Submission is the
unit `orchestrate` enumerates and `bench` returns the `argmax` over.
A frozen, hashable value object carrying just the three fields the
subagent-per-iter strategy returns to the main process — the rest
of the subagent's deliberation dies with its context.

- **Arrange**: import `Submission` from `src.tier1.entities.submission`.
- **Act**: construct `Submission(body='from foo import bar\n',
  score=1234.5, walltime_sec=12.7)`.
- **Assert**: the three fields round-trip
  (`s.body == 'from foo import bar\n'`, `s.score == 1234.5`,
  `s.walltime_sec == 12.7`).

Test code: [`../../../../tests/tier1/entities/test_submission.py`](../../../../tests/tier1/entities/test_submission.py)::`test_when_submission_constructed_then_carries_body_score_walltime`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.
