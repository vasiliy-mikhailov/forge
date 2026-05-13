# `test_when_score_submission_wired_with_adapter_then_returns_attempt_result_matching_legacy_scorer`

Pins the Clean Architecture wire-up: `score_submission` (use case) +
`GameBoard2048Adapter` (adapter) produces an `AttemptResult` whose
aggregate values match the legacy `src.tier1.scorer.run_canonical_eval`
dict for the same submission. This is the proof that the layered
re-implementation preserves behavior.

- **Arrange**: load `tasks/2048/baselines/reference_fsm.py`;
  instantiate `GameBoard2048Adapter`; choose `seeds = range(1000, 1020)`.
- **Act**: `score_submission(module.Solver, seeds, adapter)`.
- **Assert**: the returned `AttemptResult.mean_score`,
  `median_score`, `max_max_tile`, `n_games` match the legacy
  `run_canonical_eval(module.Solver)` outputs exactly.

Test code: [`tests/clean_arch/test_score_submission_wired.py`](../../tests/clean_arch/test_score_submission_wired.py).
