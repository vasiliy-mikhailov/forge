# `src/tier1/use_cases/score_submission.py`

`score_submission` is the application-policy orchestrator: it plays
N games via an injected `GameEnvPort`, aggregates per-game outcomes,
and returns an `AttemptResult` aligned with SPEC.md.

## Signature

    def score_submission(
        solver_factory: Callable,
        seeds: Iterable[int],
        env: GameEnvPort,
        hard_wall_sec: float = 0.0,
    ) -> AttemptResult

## Responsibilities

1. For each `seed` in `seeds`:
   - If `hard_wall_sec > 0` and aggregate elapsed time exceeds it,
     append a sentinel `GameResult(final_state='walltime_exceeded')`
     and continue to the next seed.
   - Otherwise call `env.play_one_game(solver_factory(), seed)` and
     collect the returned `GameResult`.
2. Aggregate scoring metrics (`mean_score`, `median_score`,
   `std_score`, `max_max_tile`, `aggregate_walltime_sec`).
3. Populate the SPEC.md-aligned `AttemptResult` fields:
   - `games` — the tuple of collected `GameResult`s.
   - `stagnated_any` — OR of `g.final_state == 'stagnated'`.
   - `walltime_exceeded` — OR of `g.final_state == 'walltime_exceeded'`.
   - `hard_wall_sec` — reflects the input value (0.0 by default).

## `hard_wall_sec` cap

Per [ADR 0006](../../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
layer 1. The cap is AGGREGATE — it fires between games once total
elapsed exceeds the budget; the FIRST slow game still runs to
completion before the cap kicks in. Per-game preemption is the
Docker tier-1 sandbox layer (ADR 0006 layer 2, queued).

Default `0.0` = disabled, matching the legacy behaviour. Callers
opt in (cycle-22 campaign would have set e.g. `hard_wall_sec=60`).

## Layer purity

Pure application-business-rule. Imports only entities and stdlib
(`statistics`, `time`, `typing`). No IO, no HTTP, no Docker.
