"""2048 environment for reward-bench (v2 — WASD action API, matches rl-2048).

Lifted + cleaned from `rl-2048/notebooks/2048_gpt_oss_20b.ipynb`.
Adds: type hints, pydantic GameState, deterministic seed handling,
exposes a stable public API for both the harness runner and tier-1
solvers (which import GameBoard).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional


# ---------- Pure-Python row helpers (kept identical to rl-2048 to avoid env drift) ----------

def _compress_and_merge_row_left(row):
    n = len(row)
    tiles = [x for x in row if x != 0]
    gained = 0
    merged = []
    i = 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            v = tiles[i] * 2
            gained += v
            merged.append(v)
            i += 2
        else:
            merged.append(tiles[i])
            i += 1
    merged += [0] * (n - len(merged))
    changed = merged != row
    return merged, gained, changed


def _move_left(board):
    changed_any = False
    total_gain = 0
    new_board = []
    for row in board:
        new_row, gained, changed = _compress_and_merge_row_left(row)
        new_board.append(new_row)
        total_gain += gained
        changed_any = changed_any or changed
    return new_board, total_gain, changed_any


def _move_right(board):
    changed_any = False
    total_gain = 0
    new_board = []
    for row in board:
        rev = list(reversed(row))
        new_rev, gained, changed = _compress_and_merge_row_left(rev)
        new_board.append(list(reversed(new_rev)))
        total_gain += gained
        changed_any = changed_any or changed
    return new_board, total_gain, changed_any


def _transpose(board):
    return [list(row) for row in zip(*board)]


def _move_up(board):
    t = _transpose(board)
    moved, gain, changed = _move_left(t)
    return _transpose(moved), gain, changed


def _move_down(board):
    t = _transpose(board)
    moved, gain, changed = _move_right(t)
    return _transpose(moved), gain, changed


def _empty_cells(board):
    size = len(board)
    return [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]


def _can_move(board):
    if _empty_cells(board):
        return True
    size = len(board)
    for r in range(size):
        for c in range(size - 1):
            if board[r][c] == board[r][c + 1]:
                return True
    for r in range(size - 1):
        for c in range(size):
            if board[r][c] == board[r + 1][c]:
                return True
    return False


# ---------- Public API ----------

ACTIONS = ("W", "A", "S", "D")
ACTION_NAMES = {"W": "up", "A": "left", "S": "down", "D": "right"}
_ACTION_FNS = {"W": _move_up, "A": _move_left, "S": _move_down, "D": _move_right}


@dataclass
class GameBoard:
    """Deterministic-seeded 2048 board.

    Action API is **WASD** (uppercase strings). State is "ongoing" / "won" / "lost".
    Score increases by the value of each merge.

    Args:
        size: side length (default 4).
        seed: RNG seed for reproducibility.
        target: tile value that triggers "won" state (set higher than 2048
            for arbitrarily long games; set lower for fast eval).
        probability_fours: chance a spawned tile is 4 (else 2). Standard rule = 0.10.
    """

    size: int = 4
    seed: Optional[int] = None
    target: int = 2048
    probability_fours: float = 0.10

    _rng: random.Random = field(init=False, repr=False)
    _board: list[list[int]] = field(init=False, repr=False)
    _score: int = field(default=0, init=False, repr=False)
    _state: str = field(default="ongoing", init=False, repr=False)

    def __post_init__(self):
        if self.size < 2:
            raise ValueError("Board size must be at least 2.")
        self._rng = random.Random(self.seed)
        self._board = [[0] * self.size for _ in range(self.size)]
        self._add_random_tile()
        self._add_random_tile()
        self._update_state_after_change()

    # ----- public -----

    @property
    def board(self) -> list[list[int]]:
        """Deep copy of the board (so solver can't mutate it)."""
        return [row.copy() for row in self._board]

    @property
    def score(self) -> int:
        return self._score

    @property
    def state(self) -> str:
        return self._state

    @property
    def max_tile(self) -> int:
        return max(max(row) for row in self._board)

    def is_terminal(self) -> bool:
        return self._state in ("won", "lost")

    def do_action(self, action: str) -> bool:
        """Apply a WASD action. Returns True iff the move changed the board.

        Raises ValueError if action isn't W/A/S/D, OR if the game is already terminal.
        """
        if self._state != "ongoing":
            raise ValueError(f"Game is in terminal state '{self._state}'; no further moves.")
        if action not in ACTIONS:
            raise ValueError(f"Invalid action '{action}'. Must be one of {ACTIONS}.")

        new_board, gain, changed = _ACTION_FNS[action](self._board)
        if not changed:
            return False
        self._board = new_board
        self._score += gain
        self._add_random_tile()
        self._update_state_after_change()
        return True

    def legal_actions(self) -> list[str]:
        """List of WASD actions that would change the board."""
        out = []
        for a in ACTIONS:
            _, _, changed = _ACTION_FNS[a](self._board)
            if changed:
                out.append(a)
        return out

    # ----- private -----

    def _add_random_tile(self):
        empty = _empty_cells(self._board)
        if not empty:
            return
        r, c = self._rng.choice(empty)
        self._board[r][c] = 4 if self._rng.random() < self.probability_fours else 2

    def _update_state_after_change(self):
        if self.max_tile >= self.target:
            self._state = "won"
        elif not _can_move(self._board):
            self._state = "lost"
        else:
            self._state = "ongoing"
