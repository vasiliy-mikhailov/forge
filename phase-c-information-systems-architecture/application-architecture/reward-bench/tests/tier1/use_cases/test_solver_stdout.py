"""Cycle 103 (CATS): pin stdout suppression around env.play_one_game."""
from __future__ import annotations

import sys

import pytest

from src.tier1.entities.game_result import GameResult
from src.tier1.use_cases.score_submission import _play_with_timeout


class _PrintingEnv:
    """Stub env whose play_one_game prints before returning."""

    def __init__(self, marker: str = 'solver-stdout-marker',
                 to_stderr: bool = False, raises: BaseException | None = None):
        self._marker = marker
        self._to_stderr = to_stderr
        self._raises = raises

    def play_one_game(self, solver, seed):
        if self._to_stderr:
            print(self._marker, file=sys.stderr)
        else:
            print(self._marker)
        if self._raises is not None:
            raise self._raises
        return GameResult(seed=seed, score=42, max_tile=4, moves=1,
                          final_state='won', walltime_sec=0.0)


@pytest.mark.no_fake
def test_when_play_one_game_prints_then_stdout_not_captured(capsys):
    """Cycle 103: Solver print() inside move() must not leak to the
    bench's stdout."""
    env = _PrintingEnv(marker='solver-stdout-marker')
    result = _play_with_timeout(env, solver=None, seed=0, timeout=5)
    assert result is not None
    assert result.score == 42
    out = capsys.readouterr().out
    assert 'solver-stdout-marker' not in out, (
        f'stdout leaked: {out!r}'
    )


@pytest.mark.no_fake
def test_when_play_one_game_prints_to_stderr_then_stderr_not_captured(capsys):
    """Cycle 103: stderr too — same channel for tracebacks and noisy
    code."""
    env = _PrintingEnv(marker='solver-stderr-marker', to_stderr=True)
    _play_with_timeout(env, solver=None, seed=0, timeout=5)
    err = capsys.readouterr().err
    assert 'solver-stderr-marker' not in err, f'stderr leaked: {err!r}'


@pytest.mark.no_fake
def test_when_play_one_game_completes_then_stdout_restored(capsys):
    """Cycle 103: bench prints after the call ARE visible."""
    env = _PrintingEnv(marker='ignored')
    _play_with_timeout(env, solver=None, seed=0, timeout=5)
    print('after-play')
    out = capsys.readouterr().out
    assert 'after-play' in out, f'stdout not restored: {out!r}'


@pytest.mark.no_fake
def test_when_play_one_game_raises_then_stdout_restored(capsys):
    """Cycle 103 defensive: exception in the worker must not leave
    stdout permanently redirected."""
    env = _PrintingEnv(marker='ignored', raises=RuntimeError('boom'))
    with pytest.raises(RuntimeError):
        _play_with_timeout(env, solver=None, seed=0, timeout=5)
    print('after-raise')
    out = capsys.readouterr().out
    assert 'after-raise' in out, f'stdout not restored after raise: {out!r}'
