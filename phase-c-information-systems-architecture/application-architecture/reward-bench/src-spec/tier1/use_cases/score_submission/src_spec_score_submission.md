# `src/tier1/use_cases/score_submission.py`

`score_submission` is the application-policy orchestrator: it plays
N games via an injected `GameEnvPort`, aggregates per-game outcomes,
and returns an `AttemptResult` aligned with SPEC.md.

## Signature

    def score_submission(
        solver_factory: Callable,
        seeds: Iterable[int],
        env: GameEnvPort,
    ) -> AttemptResult

## Responsibilities (per cycle)

1. For each `seed` in `seeds`, call `env.play_one_game(solver_factory(),
   seed)` and collect the returned `GameResult`.
2. Aggregate scoring metrics (`mean_score`, `median_score`,
   `std_score`, `max_max_tile`, `aggregate_walltime_sec`).
3. Populate the SPEC.md-aligned `AttemptResult` fields:
   - `games` is the tuple of collected `GameResult` records.
   - `stagnated_any` is the OR of `g.final_state == 'stagnated'`
     across games.
   - `walltime_exceeded` is the OR of
     `g.final_state == 'walltime_exceeded'` across games.

## Layer purity

Pure application-business-rule code. Imports only entities and the
`GameEnvPort` Protocol it declares. No IO, no HTTP, no Docker, no
filesystem.

## Legacy field

`AttemptResult.seeds` is still populated as `tuple(seeds_iterable)`
to keep callers that read `result.seeds` working. A later cycle
drops the field once no caller depends on it.
