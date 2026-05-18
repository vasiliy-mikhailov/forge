# `test_when_in_process_canonical_scorer_score_body_called_then_score_submission_receives_solver_class`

Pins the §7.5 body-in API on the in-process canonical scorer per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7.5. Body string in, AttemptResult out. The scorer compiles the
body into a module in memory (no tempfile, no path), pulls out the
`Solver` class, and delegates to `score_submission`.

- **Arrange**: a body string defining `class Solver` with a fixed
  `move` method; a `FakeEnv` injected into the scorer; monkeypatch
  `src.tier1.use_cases.score_submission.score_submission` with a
  recording stub.
- **Act**: `scorer.score_body(body=BODY, seeds=(1,))`.
- **Assert**: the recording stub was called with a `Solver` class
  whose `__name__ == 'Solver'`.

Test code: [`../../../tests/adapters/test_in_process_canonical_scorer.py`](../../../tests/adapters/test_in_process_canonical_scorer.py)::`test_when_in_process_canonical_scorer_score_body_called_then_score_submission_receives_solver_class`.

## Model client injection point

- **Seam**: monkeypatch on `score_submission` use case.
- **Mode**: **fake** — no real games played; stub intercepts.

## Runtime scope

> **Runtime scope**: unit only — in-memory module compile + stub call.
