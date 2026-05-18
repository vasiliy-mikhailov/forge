# `test_when_fake_canonical_scorer_score_body_called_then_records_body_and_returns_scripted_result`

Pins the §7.5 body-in API on the canonical scorer test double per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7.5. `score_body(body: str, seeds, ...)` is the first step of the
file-API elimination chain: callers pass the submission text
directly instead of a path; the scorer marshals to whatever private
file/mount it needs internally.

This cycle adds `score_body` to `FakeCanonicalScorer` only. The
Port Protocol gains the method in a subsequent cycle; production
`DockerCanonicalScorer` after that; callers migrate after that;
old path-based `.score` removed last.

- **Arrange**: a scripted `AttemptResult`; build
  `FakeCanonicalScorer(script=(expected,))`.
- **Act**: `result = fake.score_body(body='class Solver: pass\n',
  seeds=(1, 2, 3))`.
- **Assert**: `result is expected`; and the call was recorded —
  `fake.calls[0]['body'] == 'class Solver: pass\n'` and
  `fake.calls[0]['seeds'] == (1, 2, 3)`.

Test code: [`../../../tests/adapters/test_fake_canonical_scorer.py`](../../../tests/adapters/test_fake_canonical_scorer.py)::`test_when_fake_canonical_scorer_score_body_called_then_records_body_and_returns_scripted_result`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default).

## Runtime scope

> **Runtime scope**: unit only — scripted in-memory adapter; no IO.
