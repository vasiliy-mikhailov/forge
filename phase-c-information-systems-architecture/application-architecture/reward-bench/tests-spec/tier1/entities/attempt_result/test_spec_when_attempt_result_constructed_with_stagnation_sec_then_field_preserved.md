# `test_when_attempt_result_constructed_with_stagnation_sec_then_field_preserved`

Pins the SPEC.md per-game progress-watchdog threshold as a field on
`AttemptResult`. SPEC.md §"Per-game stagnation detector" says: each
game runs until score or max_tile has not changed for
`REWARD_BENCH_STAGNATION_SEC` seconds (default 60). The attempt
record carries the threshold that applied to it so post-hoc analysis
can compare attempts with different settings.

- **Arrange**: import `AttemptResult` and `GameResult`. Build a
  trivial empty-games attempt with `stagnation_sec=60.0`.
- **Act**: construct the `AttemptResult`.
- **Assert**: `result.stagnation_sec == 60.0`. The field defaults to
  `60.0` (SPEC.md default) when not provided, so older constructors
  continue to work.

Test code: [`tests/tier1/entities/test_attempt_result.py`](../../../../tests/tier1/entities/test_attempt_result.py).
