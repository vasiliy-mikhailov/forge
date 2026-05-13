# `test_when_attempt_result_constructed_with_stagnated_any_then_field_preserved`

Pins the SPEC.md observation flag: did any game in this attempt end
with `final_state='stagnated'`? The attempt record carries the flag
so a leaderboard can highlight "stagnated_any=True" attempts without
re-walking the per-game records.

- **Arrange**: import `AttemptResult` and `GameResult`. Build a
  trivial empty-games attempt with `stagnated_any=True`.
- **Act**: construct the `AttemptResult`.
- **Assert**: `result.stagnated_any is True`. Defaults to `False`
  when not provided (older constructors continue to work).

Test code: [`tests/tier1/entities/test_attempt_result.py`](../../../../tests/tier1/entities/test_attempt_result.py).
