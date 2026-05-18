# `test_when_canonical_scorer_port_inspected_then_score_body_takes_body_and_seeds`

Pins the §7.5 body-in API on the `CanonicalScorerPort` Protocol per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7.5. Adds `score_body(body: str, seeds, ...) -> AttemptResult`
alongside the existing path-based `.score`. Callers migrate to
`score_body` in subsequent cycles; `.score(submission_path, ...)`
is removed last.

- **Arrange**: import `CanonicalScorerPort`; `inspect.signature(
  CanonicalScorerPort.score_body)`.
- **Act**: read the parameter names.
- **Assert**: first three params (after `self`) include `body` and
  `seeds`.

Test code: [`../../../tests/ports/test_canonical_scorer_port.py`](../../../tests/ports/test_canonical_scorer_port.py)::`test_when_canonical_scorer_port_inspected_then_score_body_takes_body_and_seeds`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default).

## Runtime scope

> **Runtime scope**: unit only — Protocol method-signature contract; no runtime boundary involved.
