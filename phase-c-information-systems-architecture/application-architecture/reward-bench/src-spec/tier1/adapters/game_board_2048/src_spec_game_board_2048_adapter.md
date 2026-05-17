# `src_spec_game_board_2048_adapter`
`src.tier1.adapters.game_board_2048.GameBoard2048Adapter` is a concrete
implementation of the `GameEnvPort` protocol declared in
`src.tier1.use_cases.score_submission`. It wraps `tasks/2048/env.GameBoard`
behind the port so use_cases stay decoupled from the 2048 env's
concrete API.
Public method:
 def play_one_game(self, solver, seed: int) -> GameResult:
 '''Returns a fully-populated GameResult: seed, score,
 max_tile, moves (counted by the adapter), walltime_sec
 (measured), final_state (mapped from board.state — 'won'
 or 'lost'). Loops solver.move(board.board) ->
 board.do_action(action) until is_terminal().'''
The richer return is what lets `score_submission` populate
`AttemptResult.games` per SPEC.md without itself reaching into env
internals.
Allowed imports: `sys`, `pathlib`, `src.tier1.use_cases.score_submission`
(for type hint) and a `sys.path`-inserted import of the legacy
`tasks/2048/env.GameBoard`. The sys.path trick is local to this
adapter; nothing else in src/ needs the tasks/ directory.
