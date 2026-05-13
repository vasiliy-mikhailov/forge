# `src_spec_game_board_2048_adapter`

`src.tier1.adapters.game_board_2048.GameBoard2048Adapter` is a concrete
implementation of the `GameEnvPort` protocol declared in
`src.tier1.use_cases.score_submission`. It wraps `tasks/2048/env.GameBoard`
behind the port so use_cases stay decoupled from the 2048 env's
concrete API.

Public method:

    def play_one_game(self, solver, seed: int) -> tuple[int, int]:
        '''Returns (score, max_tile). Loops solver.move(board.board)
        -> board.do_action(action) until is_terminal(). Same logic
        as the legacy src/tier1/scorer.py _play helper, just under
        the port contract.'''

Allowed imports: `sys`, `pathlib`, `src.tier1.use_cases.score_submission`
(for type hint) and a `sys.path`-inserted import of the legacy
`tasks/2048/env.GameBoard`. The sys.path trick is local to this
adapter; nothing else in src/ needs the tasks/ directory.
