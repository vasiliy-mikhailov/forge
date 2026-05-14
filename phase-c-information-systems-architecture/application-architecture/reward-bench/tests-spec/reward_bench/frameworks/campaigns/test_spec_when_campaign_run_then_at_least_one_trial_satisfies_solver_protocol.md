# `test_when_campaign_run_then_at_least_one_trial_satisfies_solver_protocol`

Closes the user-identified CATS hole: previously campaign tests
passed when ALL trials produced Gym-style submissions because the
shape contract tolerated `mean=0` sentinels. This assertion makes the
test fail when the model never managed to write a submission that
satisfies the [SKILL_tier1.md protocol](../../../../tasks/2048/SKILL_tier1.md)
(class Solver + move(self, board) -> 'W'|'A'|'S'|'D').

Per-trial booleans are recorded in the artifact's
`per_trial_protocol_valid` field. The test asserts
`any(per_trial_protocol_valid)` — at least one trial must have
produced a valid submission. Zero valid = the active loop is broken
end-to-end and the test goes red.

- **Arrange**: existing campaign config (`max_iters=100`, `n_trials=3`,
  cycles 48/50/51/52/53 wiring).
- **Act**: run the campaign live; artifact is written.
- **Assert** (added):
  - `'per_trial_protocol_valid' in artifact`
  - `len(per_trial_protocol_valid) == n_trials`
  - `any(per_trial_protocol_valid)` — REGRESSION GUARD.

Test code: [`tests/reward_bench/frameworks/campaigns/test_iters100_T07_n3.py`](../../../../tests/reward_bench/frameworks/campaigns/test_iters100_T07_n3.py).
