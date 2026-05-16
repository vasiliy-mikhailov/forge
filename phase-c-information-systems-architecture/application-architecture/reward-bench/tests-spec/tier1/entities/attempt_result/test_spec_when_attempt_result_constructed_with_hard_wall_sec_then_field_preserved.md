# `test_when_attempt_result_constructed_with_hard_wall_sec_then_field_preserved`

Pins the SPEC.md outer-runaway cap as a field on `AttemptResult`.
SPEC.md §"Per-game stagnation detector" describes `hard_wall_sec`
as the outer hard-wall cap, default `0` (disabled). The attempt
record carries the cap that applied to it.

- **Arrange**: import `AttemptResult` and `GameResult`. Build a
  trivial empty-games attempt with `hard_wall_sec=1800.0` (a
  non-default value so the test pins the actual stored number, not
  the default).
- **Act**: construct the `AttemptResult`.
- **Assert**: `result.hard_wall_sec == 1800.0`. The field defaults to
  `0.0` (SPEC.md default = disabled) when not provided, so older
  constructors continue to work.

Test code: [`tests/tier1/entities/test_attempt_result.py`](../../../../tests/tier1/entities/test_attempt_result.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

