# `test_when_attempt_result_constructed_with_games_tuple_then_games_field_preserves_tuple`

Pins the first new field of the SPEC.md realignment: `AttemptResult`
carries a `games: tuple[GameResult, ...]` field that preserves the
per-game records nested inside an attempt. The pydantic schema in
SPEC.md declares `games: list[GameResult]`; the Python entity uses a
frozen tuple so the dataclass stays hashable.

- **Arrange**: import `AttemptResult` and `GameResult`. Build two
  `GameResult` instances with different seeds (e.g. 1000, 1001) and
  trivial other values.
- **Act**: construct `AttemptResult` with `games=(g1, g2)` and the
  other fields filled in at any sensible value.
- **Assert**: `result.games == (g1, g2)` and `len(result.games) == 2`.

This is the first additive field. Existing callers (score_submission
and the legacy scorer) keep working because the field defaults to
an empty tuple — they do not need to be touched in this cycle.

Test code: [`tests/tier1/entities/test_attempt_result.py`](../../../../tests/tier1/entities/test_attempt_result.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.

