# `test_when_attempt_result_constructed_with_walltime_exceeded_then_field_preserved`

Pins the SPEC.md observation flag: did any game in this attempt end
because the outer `hard_wall_sec` cap fired? The attempt record
carries the flag so a leaderboard can surface walltime_exceeded
attempts without re-walking the per-game records.

- **Arrange**: import `AttemptResult` and `GameResult`. Build a
  trivial empty-games attempt with `walltime_exceeded=True`.
- **Act**: construct the `AttemptResult`.
- **Assert**: `result.walltime_exceeded is True`. Defaults to `False`
  when not provided.

Test code: [`tests/tier1/entities/test_attempt_result.py`](../../../../tests/tier1/entities/test_attempt_result.py).
