# `test_when_canonical_eval_played_then_result_has_full_attempt_schema`

Pins canonical-eval layer: a fresh `Solver()` per seed plays one
game per canonical seed (`1000..1019`, N=20 per SPEC.md Tier 1).
The returned dict matches the SPEC.md `AttemptResult` schema fields.

- **Arrange**: load `tasks/2048/baselines/reference_fsm.py`; obtain
  the `Solver` class.
- **Act**: `src.tier1.scorer.run_canonical_eval(Solver)` (passing
  the class, since we want a fresh instance per seed).
- **Assert**: returned dict has keys `mean_score`, `median_score`,
  `std_score`, `max_max_tile`, `n_games`, `aggregate_walltime_sec`,
  `seeds`. `n_games == 20`. `seeds == list(range(1000, 1020))`.

Test code: [`tests/tier1/test_scorer.py`](../../tests/tier1/test_scorer.py).
