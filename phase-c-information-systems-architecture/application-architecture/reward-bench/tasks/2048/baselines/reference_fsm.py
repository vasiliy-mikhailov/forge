"""Reference tier-1 submission — what a *competent* author would write.

Used only for harness calibration: when the eval sandbox is handed this
file, it should produce mean_score ≈ 4 400 over 30 games. If it doesn't,
the harness has a bug.

LLM submissions go through OpenHands (Stage 1: author) and produce their
own submission.py. This file is the human baseline.

Conforms to tier-1 contract (see /tasks/2048/tier-1/SKILL.md):
  - class Solver with move(board) -> {'W','A','S','D'}
  - declares states + transitions via `transitions.Machine`
  - imports only allowed: numpy, transitions, math, random, copy, etc.
  - no eval/exec/__import__/I/O/timing-randomness
"""

from __future__ import annotations
import math

from transitions import Machine

# WASD priority order: down → left → up → right (corner-anchor strategy)
ACTIONS = ("S", "A", "W", "D")


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
            return self._consolidating_move(board)
        return self._endgame_move(board)

    def _reclassify(self, board):
        empty = sum(1 for row in board for v in row if v == 0)
        max_tile = max(max(row) for row in board)
        if empty <= 2:
            self.to_tight()
        elif max_tile < 128:
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
        n = len(board)
        if action == "A":
            new_rows = []
            gains = 0
            for row in board:
                nr, g, _ = cls._slide_row_left(row)
                new_rows.append(nr)
                gains += g
            new = new_rows
        elif action == "D":
            new_rows = []
            gains = 0
            for row in board:
                nr, g, _ = cls._slide_row_left(list(reversed(row)))
                new_rows.append(list(reversed(nr)))
                gains += g
            new = new_rows
        elif action == "W":
            cols = [list(c) for c in zip(*board)]
            new_cols = []
            gains = 0
            for col in cols:
                nc, g, _ = cls._slide_row_left(col)
                new_cols.append(nc)
                gains += g
            new = [list(r) for r in zip(*new_cols)]
        elif action == "S":
            cols = [list(c) for c in zip(*board)]
            new_cols = []
            gains = 0
            for col in cols:
                nc, g, _ = cls._slide_row_left(list(reversed(col)))
                new_cols.append(list(reversed(nc)))
                gains += g
            new = [list(r) for r in zip(*new_cols)]
        else:
            raise ValueError(action)
        return new, gains, new != board

    @staticmethod
    def _evaluate(board):
        empty = sum(1 for row in board for v in row if v == 0)
        max_tile = max(max(row) for row in board)
        corners = (board[0][0], board[0][-1], board[-1][0], board[-1][-1])
        max_in_corner = max_tile > 0 and max_tile in corners

        mono = 0
        for j in range(3):
            if board[-1][j] >= board[-1][j + 1] and board[-1][j] > 0:
                mono += board[-1][j]
        for i in range(3, 0, -1):
            if board[i][0] >= board[i - 1][0] and board[i][0] > 0:
                mono += board[i][0]

        smooth = 0.0
        for i in range(4):
            for j in range(3):
                a, b = board[i][j], board[i][j + 1]
                if a and b:
                    smooth -= abs(math.log2(a) - math.log2(b))
                a, b = board[j][i], board[j + 1][i]
                if a and b:
                    smooth -= abs(math.log2(a) - math.log2(b))

        return empty * 200 + (max_tile if max_in_corner else 0) * 1.5 + mono * 4.0 + smooth * 30.0

    def _building_move(self, board):
        for a in ACTIONS:
            _, _, ch = self._simulate(board, a)
            if ch:
                return a
        return ACTIONS[0]

    def _consolidating_move(self, board):
        best_score = -float("inf")
        best_action = None
        for a in ACTIONS:
            new_board, gain, changed = self._simulate(board, a)
            if not changed:
                continue
            score = self._evaluate(new_board) + gain
            if a == "S":
                score += 50
            elif a == "A":
                score += 30
            elif a == "W":
                score -= 50
            if score > best_score:
                best_score, best_action = score, a
        return best_action or self._first_legal(board)

    def _endgame_move(self, board):
        best_score = -float("inf")
        best_action = None
        for a in ACTIONS:
            new_board, gain, changed = self._simulate(board, a)
            if not changed:
                continue
            empty_cells = [(i, j) for i in range(4) for j in range(4) if new_board[i][j] == 0]
            if not empty_cells:
                eval_score = self._evaluate(new_board)
            else:
                samples = empty_cells[: min(6, len(empty_cells))]
                eval_score = 0.0
                weight = 0.0
                for (i, j) in samples:
                    for v, p in ((2, 0.9), (4, 0.1)):
                        sim = [row.copy() for row in new_board]
                        sim[i][j] = v
                        best_resp = -float("inf")
                        for a2 in ACTIONS:
                            sim2, g2, ch2 = self._simulate(sim, a2)
                            if not ch2:
                                continue
                            cand = self._evaluate(sim2) + g2
                            if cand > best_resp:
                                best_resp = cand
                        if best_resp == -float("inf"):
                            best_resp = self._evaluate(sim) - 1e6
                        eval_score += p * best_resp
                        weight += p
                if weight > 0:
                    eval_score /= weight
            total = gain + eval_score
            if a == "S":
                total += 30
            elif a == "A":
                total += 15
            if total > best_score:
                best_score, best_action = total, a
        return best_action or self._first_legal(board)

    def _tight_move(self, board):
        best_score = -float("inf")
        best_action = None
        for a in ACTIONS:
            new_board, gain, changed = self._simulate(board, a)
            if not changed:
                continue
            empty = sum(1 for row in new_board for v in row if v == 0)
            corners = (new_board[0][0], new_board[0][-1], new_board[-1][0], new_board[-1][-1])
            mt = max(max(row) for row in new_board)
            corner = mt > 0 and mt in corners
            score = empty * 1000 + gain * 5 + (corner * 100)
            if score > best_score:
                best_score, best_action = score, a
        return best_action or self._first_legal(board)

    def _first_legal(self, board):
        for a in ACTIONS:
            _, _, ch = self._simulate(board, a)
            if ch:
                return a
        return ACTIONS[0]
