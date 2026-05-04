"""Claude's tier-1 submission for reward-bench / 2048.

Establishes the leaderboard ceiling reference. Stronger than the
hand-written `reference_fsm.py` baseline:
  - 2-ply expectimax in mid-game/endgame (was 1-ply)
  - Better evaluation: weighted snake heuristic (the canonical 2048 strategy
    from blogs/papers — assigns positional weights so values decrease
    along a snake path from the bottom-left corner)
  - Tighter state classification with explicit transitions
  - All while staying within the tier-1 contract (transitions.Machine FSM,
    no LLM calls, only allow-listed imports, no I/O, no timing-randomness).
"""

from __future__ import annotations

import math
from transitions import Machine

ACTIONS = ("S", "A", "W", "D")  # priority: down, left, up, right (corner anchor)

# Snake-pattern positional weights — canonical 2048 heuristic.
# Largest values go bottom-left, decreasing along the snake path.
# The board is read [row][col] where row=0 is top, row=3 is bottom.
SNAKE_WEIGHTS = [
    [    4,    8,   16,   32],
    [  256,  128,   64,   32],   # row 1: zig
    [  512, 1024, 2048, 4096],   # row 2: zag
    [65536,32768,16384, 8192],   # row 3: bottom — biggest
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

    def move(self, board):
        self._reclassify(board)
        if self.state == "tight":
            return self._tight_move(board)
        if self.state == "building":
            return self._building_move(board)
        if self.state == "consolidating":
            return self._consolidating_move(board, depth=1)
        return self._endgame_move(board, depth=2)

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

    # ---- env simulation ----

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
            new = new_rows
        elif action == "D":
            new_rows, gains = [], 0
            for row in board:
                nr, g, _ = cls._slide_row_left(list(reversed(row)))
                new_rows.append(list(reversed(nr)))
                gains += g
            new = new_rows
        elif action == "W":
            cols = [list(c) for c in zip(*board)]
            new_cols, gains = [], 0
            for col in cols:
                nc, g, _ = cls._slide_row_left(col)
                new_cols.append(nc)
                gains += g
            new = [list(r) for r in zip(*new_cols)]
        elif action == "S":
            cols = [list(c) for c in zip(*board)]
            new_cols, gains = [], 0
            for col in cols:
                nc, g, _ = cls._slide_row_left(list(reversed(col)))
                new_cols.append(list(reversed(nc)))
                gains += g
            new = [list(r) for r in zip(*new_cols)]
        else:
            raise ValueError(action)
        return new, gains, new != board

    # ---- evaluation ----

    @staticmethod
    def _empty_count(board):
        return sum(1 for row in board for v in row if v == 0)

    @staticmethod
    def _max_tile(board):
        return max(max(row) for row in board)

    @staticmethod
    def _snake_score(board):
        """Sum of board[i][j] × SNAKE_WEIGHTS[i][j]. Rewards keeping big
        tiles on the snake path."""
        s = 0
        for i in range(4):
            for j in range(4):
                s += board[i][j] * SNAKE_WEIGHTS[i][j]
        return s

    @staticmethod
    def _smoothness(board):
        """Penalty proportional to log2-differences between adjacent cells."""
        s = 0.0
        for i in range(4):
            for j in range(3):
                a, b = board[i][j], board[i][j + 1]
                if a and b:
                    s -= abs(math.log2(a) - math.log2(b))
                a, b = board[j][i], board[j + 1][i]
                if a and b:
                    s -= abs(math.log2(a) - math.log2(b))
        return s

    def _evaluate(self, board):
        empty = self._empty_count(board)
        snake = self._snake_score(board)
        smooth = self._smoothness(board)
        max_tile = self._max_tile(board)
        # Bonus if max tile sits on the snake's start (bottom-left corner)
        anchor_bonus = max_tile * 4 if board[3][0] == max_tile and max_tile > 0 else 0
        # Empty cells weighted by log(max_tile) so survival matters more late game
        empty_w = empty * (max(math.log2(max_tile), 1) ** 2) * 50 if max_tile > 0 else empty * 50
        return snake * 1.0 + smooth * 100.0 + empty_w + anchor_bonus

    # ---- expectimax ----

    def _expectimax(self, board, depth):
        """Player-then-chance lookahead. Returns expected score."""
        if depth == 0:
            return self._evaluate(board)
        # Player's turn — best action
        best = -float("inf")
        any_legal = False
        for a in ACTIONS:
            new_board, gain, changed = self._simulate(board, a)
            if not changed:
                continue
            any_legal = True
            v = gain + self._chance(new_board, depth - 1)
            if v > best:
                best = v
        if not any_legal:
            return self._evaluate(board) - 1e6
        return best

    def _chance(self, board, depth):
        """Random spawn — average over up to N empty positions × {2, 4}."""
        if depth == 0:
            return self._evaluate(board)
        empty = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
        if not empty:
            return self._evaluate(board)
        # Limit branching for speed: sample at most 6 empty cells
        sample = empty[: min(6, len(empty))]
        s = 0.0
        weight = 0.0
        for (i, j) in sample:
            for v, p in ((2, 0.9), (4, 0.1)):
                sim = [row.copy() for row in board]
                sim[i][j] = v
                s += p * self._expectimax(sim, depth)
                weight += p
        return s / weight if weight > 0 else self._evaluate(board)

    # ---- per-state policies ----

    def _building_move(self, board):
        # Greedy with snake bias
        best = -float("inf")
        best_action = None
        for a in ACTIONS:
            new_board, gain, changed = self._simulate(board, a)
            if not changed:
                continue
            score = self._evaluate(new_board) + gain
            if a == "S":
                score += 200
            elif a == "A":
                score += 100
            elif a == "W":
                score -= 200
            if score > best:
                best, best_action = score, a
        return best_action or self._first_legal(board)

    def _consolidating_move(self, board, depth):
        return self._search_with_bias(board, depth, down_bonus=80, left_bonus=40, up_penalty=80)

    def _endgame_move(self, board, depth):
        return self._search_with_bias(board, depth, down_bonus=40, left_bonus=20, up_penalty=100)

    def _tight_move(self, board):
        # Prefer moves that maximize empty cells; secondary: keep anchor
        best = -float("inf")
        best_action = None
        for a in ACTIONS:
            new_board, gain, changed = self._simulate(board, a)
            if not changed:
                continue
            empty = self._empty_count(new_board)
            mt = self._max_tile(new_board)
            anchor = (new_board[3][0] == mt and mt > 0)
            score = empty * 1500 + gain * 5 + (anchor * 200)
            if score > best:
                best, best_action = score, a
        return best_action or self._first_legal(board)

    def _search_with_bias(self, board, depth, *, down_bonus, left_bonus, up_penalty):
        best = -float("inf")
        best_action = None
        for a in ACTIONS:
            new_board, gain, changed = self._simulate(board, a)
            if not changed:
                continue
            v = gain + self._chance(new_board, depth)
            if a == "S":
                v += down_bonus
            elif a == "A":
                v += left_bonus
            elif a == "W":
                v -= up_penalty
            if v > best:
                best, best_action = v, a
        return best_action or self._first_legal(board)

    def _first_legal(self, board):
        for a in ACTIONS:
            _, _, ch = self._simulate(board, a)
            if ch:
                return a
        return ACTIONS[0]
