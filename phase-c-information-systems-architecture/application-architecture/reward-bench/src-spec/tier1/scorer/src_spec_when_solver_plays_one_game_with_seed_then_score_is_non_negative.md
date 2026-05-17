# `src_spec_when_solver_plays_one_game_with_seed_then_score_is_non_negative`
`src.tier1.scorer.score_one_game(solver, seed: int) -> int`:
- Instantiates `tasks/2048/env.GameBoard(seed=seed)`.
- Loops until `board.is_terminal()`:
 - `action = solver.move(board.board)` (deep-copied board; solver cannot
 mutate harness state).
 - `board.do_action(action)`.
- Returns `board.score`.
Per SPEC.md Tier 1 the score is the cumulative merge value across the
game. Non-negative by env contract.
Forced-fallback for illegal/no-change actions (SPEC.md: "If your
move() returns an action that wouldn't change the board, the harness
substitutes the first legal action") is deferred to its own cycle
when a real submission triggers it.
