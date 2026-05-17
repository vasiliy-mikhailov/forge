# `src_spec_when_canonical_eval_played_then_result_has_full_attempt_schema`
`src.tier1.scorer.run_canonical_eval(solver_factory) -> dict`:
- `CANONICAL_SEEDS = list(range(1000, 1020))` (20 seeds per SPEC.md
 Tier 1).
- For each seed: instantiate `solver_factory()` (so each game has a
 fresh stateful solver), call `score_one_game(solver, seed)`.
- Track max_tile per game via `GameBoard.max_tile`.
- Time the whole run via `time.monotonic()`.
Returns a dict with the SPEC.md `AttemptResult` fields:
 mean_score (float)
 median_score (float)
 std_score (float, population stdev)
 max_max_tile (int)
 n_games (int, == 20)
 aggregate_walltime_sec (float)
 seeds (list[int])
(Pydantic `AttemptResult` validation comes in a later cycle when we
land result.json IO; for now the dict shape is what's asserted.)
