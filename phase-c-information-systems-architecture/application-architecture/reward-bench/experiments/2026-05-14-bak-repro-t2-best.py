"""Tier-1 2048 FSM solver using transitions library."""
from __future__ import annotations
import math
from transitions import Machine


class Solver:
    """FSM-based 2048 solver with corner-anchor strategy (bottom-left)."""

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

    def move(self, board: list[list[int]]) -> str:
        self._reclassify(board)
        if self.state == "tight":
            return self._tight_move(board)
        elif self.state == "building":
            return self._building_move(board)
        elif self.state == "consolidating":
            return self._consolidating_move(board)
        else:
            return self._endgame_move(board)

    def _reclassify(self, board: list[list[int]]) -> None:
        empty = sum(1 for row in board for v in row if v == 0)
        max_tile = max(max(row) for row in board)
        if empty <= 1:
            self.to_tight()
        elif max_tile < 64:
            self.to_building()
        elif max_tile < 512:
            self.to_consolidating()
        else:
            self.to_endgame()

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
            new_rows, gains, changed = [], 0, False
            for row in board:
                nr, g, c = cls._slide_row_left(row)
                new_rows.append(nr)
                gains += g
                changed = changed or c
            return new_rows, gains, changed
        elif action == "D":
            new_rows, gains, changed = [], 0, False
            for row in board:
                nr, g, c = cls._slide_row_left(list(reversed(row)))
                new_rows.append(list(reversed(nr)))
                gains += g
                changed = changed or c
            return new_rows, gains, changed
        elif action == "W":
            cols = [list(c) for c in zip(*board)]
            new_cols, gains, changed = [], 0, False
            for col in cols:
                nc, g, c = cls._slide_row_left(col)
                new_cols.append(nc)
                gains += g
                changed = changed or c
            return [list(r) for r in zip(*new_cols)], gains, changed
        elif action == "S":
            cols = [list(c) for c in zip(*board)]
            new_cols, gains, changed = [], 0, False
            for col in cols:
                nc, g, c = cls._slide_row_left(list(reversed(col)))
                new_cols.append(list(reversed(nc)))
                gains += g
                changed = changed or c
            return [list(r) for r in zip(*new_cols)], gains, changed
        return board, 0, False

    @staticmethod
    def _empty_count(board):
        return sum(1 for row in board for v in row if v == 0)

    def _evaluate_board(self, board):
        """Evaluate board for corner strategy (bottom-left anchor)."""
        score = 0.0
        n = len(board)

        # Empty cells are very valuable
        score += self._empty_count(board) * 350

        # Snake pattern positional weights from bottom-left
        for r in range(n):
            for c in range(n):
                val = board[r][c]
                if val > 0:
                    ri = n - 1 - r
                    if ri % 2 == 0:
                        ci = c
                    else:
                        ci = n - 1 - c
                    dist = ri * n + ci
                    score += val * (0.92 ** dist)

        # Row monotonicity: left-to-right decreasing
        for row in board:
            for i in range(n - 1):
                if row[i] > 0 and row[i + 1] > 0:
                    if row[i] >= row[i + 1]:
                        score += 4.0
                    else:
                        score -= 4.0

        # Column monotonicity: top-to-bottom increasing
        for c in range(n):
            for r in range(n - 1):
                if board[r][c] > 0 and board[r + 1][c] > 0:
                    if board[r + 1][c] >= board[r][c]:
                        score += 4.0
                    else:
                        score -= 4.0

        # Merge potential: count adjacent pairs of same value
        for r in range(n):
            for c in range(n):
                if board[r][c] > 0:
                    if c + 1 < n and board[r][c + 1] == board[r][c]:
                        score += board[r][c] * 0.05
                    if r + 1 < n and board[r + 1][c] == board[r][c]:
                        score += board[r][c] * 0.05

        return score

    def _pick_best_move(self, board, actions):
        best_action = actions[0]
        best_score = float("-inf")
        for action in actions:
            new_board, gain, changed = self._simulate(board, action)
            if not changed:
                continue
            score = self._evaluate_board(new_board) + gain
            if score > best_score:
                best_score = score
                best_action = action
        return best_action

    def _building_move(self, board):
        actions = ["A", "W", "D", "S"]
        return self._pick_best_move(board, actions)

    def _consolidating_move(self, board):
        actions = ["A", "S", "W", "D"]
        return self._pick_best_move(board, actions)

    def _endgame_move(self, board):
        actions = ["A", "S", "W", "D"]
        return self._pick_best_move(board, actions)

    def _tight_move(self, board):
        actions = ["A", "S", "W", "D"]
        best_action = actions[0]
        best_score = float("-inf")
        for action in actions:
            new_board, gain, changed = self._simulate(board, action)
            if not changed:
                continue
            score = gain * 10 + self._empty_count(new_board) * 350 + self._evaluate_board(new_board)
            if score > best_score:
                best_score = score
                best_action = action
        return best_action