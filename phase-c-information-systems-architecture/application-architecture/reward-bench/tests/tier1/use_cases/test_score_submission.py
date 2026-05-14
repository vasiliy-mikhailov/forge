"""score_submission use-case tests.

See tests-spec/tier1/use_cases/score_submission/."""
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.entities.game_result import GameResult
from src.tier1.use_cases.score_submission import score_submission


class _StubEnv:
    """Returns hand-crafted GameResult instances by seed so the test
    controls final_state and can pin the derivation of the boolean
    flags without a live game env."""

    _BY_SEED = {
        1: GameResult(seed=1, score=100, max_tile=64, moves=50,
                      final_state='stagnated', walltime_sec=0.01),
        2: GameResult(seed=2, score=200, max_tile=128, moves=80,
                      final_state='lost', walltime_sec=0.02),
    }

    def play_one_game(self, solver, seed):
        return self._BY_SEED[seed]


def test_when_score_submission_called_then_attempt_result_carries_per_game_records_and_derived_flags():
    # Arrange
    env = _StubEnv()

    # Act
    result = score_submission(
        solver_factory=lambda: object(),
        seeds=[1, 2],
        env=env,
    )

    # Assert
    assert isinstance(result, AttemptResult)
    assert len(result.games) == 2
    assert result.games[0].seed == 1
    assert result.games[1].seed == 2
    assert result.stagnated_any is True
    assert result.walltime_exceeded is False


import threading as _threading
import time as _time


class _SlowEnv:
    """Stub env that sleeps to simulate slow per-game work — the cycle-22
    real-system trigger."""
    def __init__(self, sleep_per_game):
        self.sleep = sleep_per_game
    def play_one_game(self, solver, seed):
        _time.sleep(self.sleep)
        return GameResult(seed=seed, score=100, max_tile=4, moves=10,
                          final_state='lost', walltime_sec=self.sleep)


def _run_with_timeout(fn, timeout):
    """Run fn() in a daemon thread; return (done, result_or_exc)."""
    captured = {'done': False, 'value': None, 'exc': None}
    def worker():
        try:
            captured['value'] = fn()
            captured['done'] = True
        except BaseException as e:
            captured['exc'] = e
    t = _threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    return captured


def test_when_score_submission_called_with_slow_env_then_returns_within_aggregate_walltime_budget():
    """Cycle 23 (no-silent-fix): pin the cycle-22 hang shape.

    Uncapped, score_submission runs N games proportional to per-game cost.
    The cycle-22 campaign tripped this when a slow Solver did heavy lookahead
    per move; the test substitutes a deterministic 0.6 s/game stub for
    repeatability. With hard_wall_sec=0.3 the use case must cap aggregate
    walltime; without the cap (pre-fix) the daemon thread never finishes
    within the 2 s test budget."""
    # Arrange
    env = _SlowEnv(sleep_per_game=0.6)

    # Act
    captured = _run_with_timeout(
        lambda: score_submission(
            solver_factory=lambda: object(),
            seeds=list(range(10)),
            env=env,
            hard_wall_sec=0.3,
        ),
        timeout=2.0,
    )

    # Assert
    assert captured['exc'] is None, (
        f'score_submission raised: {captured["exc"]!r}'
    )
    assert captured['done'], (
        'score_submission did not return within 2.0 s budget — '
        'hard_wall_sec cap not honoured (reproduces cycle-22 hang shape).'
    )
    result = captured['value']
    assert result.walltime_exceeded is True
    exceeded = [g for g in result.games if g.final_state == 'walltime_exceeded']
    assert len(exceeded) >= 1
    assert result.hard_wall_sec == 0.3


class _HangingEnv:
    """Stub env: play_one_game(seed=1) hangs (simulates cycle-26 bug).
    Other seeds return immediately."""
    def play_one_game(self, solver, seed):
        if seed == 1:
            _time.sleep(1000)  # would hang the test process pre-fix
        return GameResult(seed=seed, score=10, max_tile=4, moves=2,
                          final_state='lost', walltime_sec=0.001)


def test_when_score_submission_called_with_env_that_hangs_one_game_then_returns_within_aggregate_walltime_budget():
    """Cycle 27 (no-silent-fix): pin per-game preemption.

    Cycle 23s aggregate cap fires only BETWEEN games — a single hanging
    play_one_game blocks the cap. This test demands score_submission
    return within the budget even when ONE game hangs."""
    # Arrange
    env = _HangingEnv()

    # Act
    captured = _run_with_timeout(
        lambda: score_submission(
            solver_factory=lambda: object(),
            seeds=[1, 2, 3],
            env=env,
            hard_wall_sec=0.3,
        ),
        timeout=1.0,
    )

    # Assert
    assert captured['exc'] is None, f'score_submission raised: {captured["exc"]!r}'
    assert captured['done'], (
        'score_submission did not return within 1.0 s budget — '
        'per-game preemption not honoured (reproduces cycle-26 hang).'
    )
    result = captured['value']
    assert result.walltime_exceeded is True
    assert result.games[0].final_state == 'walltime_exceeded', (
        f'first game (the hung one) should be sentinel; got '
        f'{result.games[0].final_state!r}'
    )



class _NeverCalledEnv:
    """Stub env whose play_one_game should never be reached because
    solver_factory crashes first."""
    def play_one_game(self, solver, seed):
        raise AssertionError(
            'play_one_game should not be reached when solver_factory raises'
        )


def _crashing_factory():
    """Stub solver_factory: raises AttributeError on every call —
    reproduces campaign10 (Solver.__init__ crash)."""
    raise AttributeError("'start' does not exist on <Machine@stub>")


def test_when_solver_factory_raises_then_returns_game_result_with_final_state_solver_error():
    """Cycle 29 (no-silent-fix): score_submission catches solver_factory
    runtime errors and emits per-seed GameResult(final_state='solver_error')
    instead of propagating.

    Reproduces campaign10: AttributeError inside Solver.__init__() escaped
    score_submission and failed the campaign with no partial leaderboard."""
    # Arrange
    env = _NeverCalledEnv()

    # Act
    result = score_submission(
        solver_factory=_crashing_factory,
        seeds=[1, 2, 3],
        env=env,
        hard_wall_sec=1.0,
    )

    # Assert
    assert result.n_games == 3, f'expected 3 sentinels; got {result.n_games}'
    for g in result.games:
        assert g.final_state == 'solver_error', (
            f"seed {g.seed} expected 'solver_error' sentinel; "
            f"got {g.final_state!r}"
        )
        assert g.score == 0
        assert g.moves == 0
    assert result.walltime_exceeded is False, (
        'solver_factory crash is not a walltime bug'
    )
