# Tier 1 game runner

## Purpose

Run a Solver instance through one 2048 game with a fixed seed and
return the resulting score.

## Public function

    run_game(solver, seed: int) -> int

## Contract (current scope)

Given a solver instance whose move(board) returns one of W/A/S/D, and a
seed, run_game plays the game until terminal and returns board.score
(a non-negative integer).

The board uses tasks/2048/env.GameBoard with the given seed. The default
target (2048) and probability_fours (0.10) apply.

If the solver returns an illegal move, run_game accepts the failed-move
return value silently (no score change, board advances by a forced
fallback in a later cycle).

## Multi-game evaluation

    run_canonical_eval(solver_factory) -> dict

solver_factory is a no-arg callable producing a fresh Solver instance
per game. Plays N=20 games on canonical seeds 1000..1019, returns
a dict with at least mean_score (float).

## Out of scope (deferred)

- Move-count cap (run_game runs until terminal today)
- Stagnation detector (no-progress watchdog)
- Forced fallback for illegal moves
- Replay determinism check
- Events trace
