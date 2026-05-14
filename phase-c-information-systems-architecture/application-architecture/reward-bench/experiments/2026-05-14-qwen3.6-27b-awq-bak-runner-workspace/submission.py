"""Tier-1 2048 solver — FSM with snake-pattern heuristic and expectimax.

States: building → consolidating → endgame → tight
Transitions via transitions.Machine. Each state has its own move policy.
"""
from __future__ import annotations

import math
from transitions import Machine

ACTIONS = ("S", "A", "W", "D")

# Snake-pattern positional weights — canonical 2048 strategy.
# Largest values go bottom-left corner, decreasing along snake path.
SNAKE_WEIGHTS = [
    [    4,    8,   16,   32],
    [  256,  128,   64,   32],
    [  512, 1024, 2048, 4096],
    [65536,32768,16384, 8192],
]


class Solver:
    states = ["building", "consolidating", "endgame", "tight"]

    def __init__(self):
        self.machine = Machine(
            model=self,
            states=Solver.states,
            initial="building",
            ignore_invalid_triggers=True,
        )
        self.machine.add_transition("to_building", source="*", dest="building")
        self.machine.add_transition("to_consolidating", source="*", dest="consolidating")
        self.machine.add_transition("to_endgame", source="*", dest="endgame")
        self.machine.add_transition("to_tight", source="*", dest="tight")

    # ---- public API ----

    def move(self, board):
        self._reclassify(board)
        if self.state == "tight":
            return self._tight_move(board)
        elif self.state == "building":
            return self._building_move(board)
        elif self.state == "consolidating":
            return self._consolidating_move(board)
        else:
            return self._endgame_move(board)

    # ---- state classification ----

    def _reclassify(self, board):
        empty = sum(1 for row in board for v in row if v == 0)
        max_tile = max(max(row) for row in board)
        if empty <= 2:
            self.to_tight()
        elif max_tile < 128:
            self.to_building()
        elif max_tile < 1024:
            self.to_consolidating()
        else:
            self.to_endgame()

    # ---- env simulation helpers ----

    @staticmethod
    def _slide_row_left(row):
        tiles = [v for v in row if v != 0]
        merged = []
        gain = 0
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                v = tiles[i] * 2
                merged.append(v)
                gain += v
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (len(row) - len(merged))
        return merged, gain, merged != row

    @classmethod
    def _simulate(cls, board, action):
        if action == "A":
            new_rows, gains = [], 0
            for row in board:
                nr, g, _ = cls._slide_row_left(row)
                new_rows.append(nr)
                gains += g
            return new_rows, gains
        elif action == "D":
            new_rows, gains = [], 0
            for row in board:
                nr, g, _ = cls._slide_row_left(list(reversed(row)))
                new_rows.append(list(reversed(nr)))
                gains += g
            return new_rows, gains
        elif action == "W":
            cols = [list(c) for c in zip(*board)]
            new_cols, gains = [], 0
            for col in cols:
                nc, g, _ = cls._slide_row_left(col)
                new_cols.append(nc)
                gains += g
            return [list(r) for r in zip(*new_cols)], gains
        elif action == "S":
            cols = [list(c) for c in zip(*board)]
            new_cols, gains = [], 0
            for col in cols:
                nc, g, _ = cls._slide_row_left(list(reversed(col)))
                new_cols.append(list(reversed(nc)))
                gains += g
            return [list(r) for r in zip(*new_cols)], gains
        return board, 0

    @staticmethod
    def _empty_cells(board):
        return [(r, c) for r in range(len(board)) for c in range(len(board[0])) if board[r][c] == 0]

    # ---- evaluation ----

    @staticmethod
    def _evaluate(board):
        """Evaluate board using snake pattern weights + empty cells."""
        score = 0.0
        for r in range(4):
            for c in range(4):
                v = board[r][c]
                if v > 0:
                    score += SNAKE_WEIGHTS[r][c] * math.log2(v)
        # Bonus for empty cells (space is valuable)
        empty = sum(1 for row in board for v in row if v == 0)
        score += empty * 50.0
        return score

    # ---- expectimax search ----

    @classmethod
    def _expectimax(cls, board, depth, maximizing):
        if depth == 0:
            return cls._evaluate(board)

        if maximizing:
            best = -float('inf')
            for action in ACTIONS:
                new_board, gain = cls._simulate(board, action)
                if new_board != board:
                    val = cls._expectimax(new_board, depth - 1, False)
                    if val > best:
                        best = val
            return best
        else:
            # Nature's turn: spawn a tile (90% chance of 2, 10% chance of 4)
            cells = cls._empty_cells(board)
            if not cells:
                return cls._evaluate(board)
            total = 0.0
            for r, c in cells:
                board_2 = [row[:] for row in board]
                board_2[r][c] = 2
                val_2 = cls._expectimax(board_2, depth - 1, True)
                board_4 = [row[:] for row in board]
                board_4[r][c] = 4
                val_4 = cls._expectimax(board_4, depth - 1, True)
                total += 0.9 * val_2 + 0.1 * val_4
            return total / len(cells)

    # ---- per-state move policies ----

    @classmethod
    def _building_move(cls, board):
        """Early game: greedy evaluation with preference for S and A."""
        best_action = "S"
        best_val = -float('inf')

        for action in ACTIONS:
            new_board, gain = cls._simulate(board, action)
            if new_board != board:
                val = cls._evaluate(new_board)
                if val > best_val:
                    best_val = val
                    best_action = action
        return best_action

    @classmethod
    def _consolidating_move(cls, board):
        """Mid game: 1-ply expectimax."""
        best_action = "S"
        best_val = -float('inf')

        for action in ACTIONS:
            new_board, gain = cls._simulate(board, action)
            if new_board != board:
                val = cls._expectimax(new_board, 1, False)
                if val > best_val:
                    best_val = val
                    best_action = action
        return best_action

    @classmethod
    def _endgame_move(cls, board):
        """Late game: 1-ply expectimax."""
        best_action = "S"
        best_val = -float('inf')

        for action in ACTIONS:
            new_board, gain = cls._simulate(board, action)
            if new_board != board:
                val = cls._expectimax(new_board, 1, False)
                if val > best_val:
                    best_val = val
                    best_action = action
        return best_action

    @classmethod
    def _tight_move(cls, board):
        """Very tight board: greedy with merge priority."""
        best_action = "S"
        best_val = -float('inf')

        for action in ACTIONS:
            new_board, gain = cls._simulate(board, action)
            if new_board != board:
                val = cls._evaluate(new_board) + gain * 100
                if val > best_val:
                    best_val = val
                    best_action = action
        return best_action