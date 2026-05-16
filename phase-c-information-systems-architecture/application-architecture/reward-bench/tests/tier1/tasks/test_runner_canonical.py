"""Cycle 105 sub-A backfill: pin the worker function in runner_canonical.py.

The runner runs INSIDE the Docker sandbox normally — its `sys.path`
includes `/env`. To unit-test the worker without Docker we inject a
fake `env_2048` module into sys.modules before importing the runner.
"""
from __future__ import annotations

import importlib
import sys
import textwrap
import time
import types
from pathlib import Path

import pytest


# --- Fake env_2048 module that the runner imports as `from env_2048 import GameBoard` ---

class _FakeBoard:
    """Minimal stand-in for tasks/2048/env.py's GameBoard, enough to
    exercise the runner_canonical worker logic in unit tests."""

    def __init__(self, seed: int = 0, target: int = 2048,
                 max_moves_terminal: int = 5,
                 score_per_move: int = 4,
                 always_terminal: bool = False):
        self.seed = seed
        self.target = target
        self.score = 0
        self.max_tile = 2
        self.state = "in_progress"
        self.board = [[0]*4 for _ in range(4)]
        self._moves = 0
        self._max_moves_terminal = max_moves_terminal
        self._score_per_move = score_per_move
        self._always_terminal = always_terminal

    def is_terminal(self) -> bool:
        if self._always_terminal:
            return True
        if self._moves >= self._max_moves_terminal:
            self.state = "lost"
            return True
        return False

    def step(self, action: str) -> None:
        self._moves += 1
        self.score += self._score_per_move
        self.max_tile = max(self.max_tile, 4)


def _install_fake_env_2048():
    """Inject a fake `env_2048` module into sys.modules so the runner
    can `from env_2048 import GameBoard` outside Docker."""
    mod = types.ModuleType("env_2048")
    mod.GameBoard = _FakeBoard
    sys.modules["env_2048"] = mod


@pytest.fixture(autouse=True)
def _runner_module(monkeypatch):
    """Importable runner module with a fake env_2048."""
    _install_fake_env_2048()
    # Force re-import so the runner picks up our fake env_2048.
    sys.modules.pop("runner_canonical", None)
    runner_path = Path(__file__).resolve().parents[3] / "tasks/2048/runner_canonical.py"
    spec = importlib.util.spec_from_file_location("runner_canonical", runner_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["runner_canonical"] = mod
    spec.loader.exec_module(mod)
    yield mod
    sys.modules.pop("runner_canonical", None)


def _solver(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "submission.py"
    p.write_text(textwrap.dedent(body).lstrip())
    return p


# ---------------------------------------------------------------
# happy-path
# ---------------------------------------------------------------

@pytest.mark.no_fake
def test_when_solver_valid_then_game_result_returned(_runner_module, tmp_path):
    """Cycle 105 sub-A worker: valid Solver -> game played, dict returned."""
    sub = _solver(tmp_path, """
        from transitions import Machine
        class Solver:
            def __init__(self):
                self.m = Machine(states=["idle"], initial="idle")
            def move(self, board):
                return "W"
    """)
    game, events = _runner_module._play_one_collect_events(
        (str(sub), 1, 2048, 100, 60.0, None)
    )
    assert game["seed"] == 1
    assert game["score"] >= 0
    assert game["moves"] > 0
    assert game["final_state"] in ("won", "lost", "max_moves")
    assert isinstance(events, list)


# ---------------------------------------------------------------
# solver_error variants
# ---------------------------------------------------------------

@pytest.mark.no_fake
def test_when_solver_init_raises_then_solver_error_final_state(_runner_module, tmp_path):
    sub = _solver(tmp_path, """
        from transitions import Machine
        class Solver:
            def __init__(self):
                raise RuntimeError("synthetic init error")
            def move(self, board):
                return "W"
    """)
    game, _ = _runner_module._play_one_collect_events(
        (str(sub), 1, 2048, 100, 60.0, None)
    )
    assert game["final_state"] == "solver_error"
    assert "RuntimeError" in game.get("error", "")


@pytest.mark.no_fake
def test_when_solver_move_raises_then_solver_error_with_event(_runner_module, tmp_path):
    sub = _solver(tmp_path, """
        from transitions import Machine
        class Solver:
            def __init__(self):
                self.m = Machine(states=["idle"], initial="idle")
                self._n = 0
            def move(self, board):
                self._n += 1
                if self._n >= 2:
                    raise ValueError("synthetic move error")
                return "W"
    """)
    game, events = _runner_module._play_one_collect_events(
        (str(sub), 1, 2048, 100, 60.0, None)
    )
    assert game["final_state"] == "solver_error"
    assert any(e.get("event") == "solver_raised" for e in events)


@pytest.mark.no_fake
def test_when_solver_returns_invalid_action_then_invalid_action_final_state(_runner_module, tmp_path):
    sub = _solver(tmp_path, """
        from transitions import Machine
        class Solver:
            def __init__(self):
                self.m = Machine(states=["idle"], initial="idle")
            def move(self, board):
                return "Q"   # not WASD
    """)
    game, events = _runner_module._play_one_collect_events(
        (str(sub), 1, 2048, 100, 60.0, None)
    )
    assert game["final_state"] == "invalid_action"
    assert any(e.get("event") == "invalid_action" for e in events)


# ---------------------------------------------------------------
# hard deadline
# ---------------------------------------------------------------

@pytest.mark.no_fake
def test_when_hard_deadline_passed_then_walltime_exceeded(_runner_module, tmp_path):
    """Deadline already passed at call time -> first iter of the
    game loop checks the wall clock and emits walltime_exceeded."""
    sub = _solver(tmp_path, """
        from transitions import Machine
        class Solver:
            def __init__(self):
                self.m = Machine(states=["idle"], initial="idle")
            def move(self, board):
                return "W"
    """)
    already_past = time.time() - 1.0
    game, _ = _runner_module._play_one_collect_events(
        (str(sub), 1, 2048, 100, 60.0, already_past)
    )
    assert game["final_state"] == "walltime_exceeded"
