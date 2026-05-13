# `src_spec_score_submission_use_case`

`src.tier1.use_cases.score_submission.score_submission(solver_factory, seeds, env)
-> AttemptResult` is the application-policy orchestrator for Tier 1
canonical evaluation. It plays N games (one per seed) using a fresh
`solver_factory()` each time, gathers per-game scores and max_tile via
the injected `env` port, and aggregates into an `AttemptResult` entity.

Same file declares `GameEnvPort` — a `typing.Protocol` describing the
adapter contract:

    def play_one_game(self, solver, seed: int) -> tuple[int, int]:
        '''Returns (score, max_tile).'''

The use case has no knowledge of the 2048 env implementation, no HTTP,
no Docker, no file system. The concrete adapter (which wraps
`tasks/2048/env.GameBoard`) lives under `src/adapters/` in a later
cycle.

Allowed imports: `statistics`, `time`, `typing`, `src.tier1.entities.attempt_result`.
