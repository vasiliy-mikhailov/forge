# `test_when_attempt_result_inspected_then_legacy_seeds_field_is_removed`

Pins the removal of the legacy `seeds: tuple[int, ...]` field on
`AttemptResult`. Per-seed identity is now recovered from
`tuple(g.seed for g in result.games)` — SPEC.md never declared the
flat `seeds` field; it was a pre-realignment compatibility shim.

- **Arrange**: import `AttemptResult` and `dataclasses`.
- **Act**: inspect `dataclasses.fields(AttemptResult)`.
- **Assert**:
  - `'seeds'` is NOT among the field names.
  - `'games'` IS among the field names (positive control — the
    replacement is intact).

Test code: [`tests/tier1/entities/test_attempt_result.py`](../../../../tests/tier1/entities/test_attempt_result.py).
