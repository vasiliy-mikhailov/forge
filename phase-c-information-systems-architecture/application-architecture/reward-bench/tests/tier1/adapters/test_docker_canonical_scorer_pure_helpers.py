"""Pure helpers extracted from DockerCanonicalScorer.

Pins the contracts of build_docker_cmd / parse_result_payload /
aggregate_attempt. Pure functions — no Docker, no subprocess, no
filesystem.
"""
from pathlib import Path

import pytest

from src.tier1.adapters.docker_canonical_scorer import (
    build_docker_cmd,
    parse_result_payload,
    aggregate_attempt,
)
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.entities.game_result import GameResult


def test_when_build_docker_cmd_called_with_options_then_returns_canonical_arg_tuple():
    # Arrange
    cmd = build_docker_cmd(
        image='reward-bench-tier1:0.4',
        submission_path=Path('/tmp/sub.py'),
        env_path=Path('/tmp/env.py'),
        reports_dir=Path('/tmp/reports'),
        cpus=4.0,
        memory='2g',
        pids_limit=256,
        stagnation_sec=60,
        hard_wall_sec=300.0,
        seed_base=1000,
        n_games=20,
    )

    # Assert: immutable tuple of strings (Haskell stance — no mutable lists)
    assert isinstance(cmd, tuple), f'cmd must be tuple; got {type(cmd).__name__}'
    assert all(isinstance(s, str) for s in cmd)

    expected = (
        'docker', 'run', '--rm',
        '--network=none',
        '--memory=2g',
        '--pids-limit=256',
        '--cpus=4.0',
        '-v', '/tmp/sub.py:/workspace/submission.py:ro',
        '-v', '/tmp/env.py:/env/env_2048.py:ro',
        '-v', '/tmp/reports:/reports',
        '-e', 'REWARD_BENCH_NUM_GAMES=20',
        '-e', 'REWARD_BENCH_SEED_BASE=1000',
        '-e', 'REWARD_BENCH_STAGNATION_SEC=60',
        '-e', 'REWARD_BENCH_HARD_WALL_SEC=300.0',
        'reward-bench-tier1:0.4',
    )
    assert cmd == expected, f'cmd shape drift:\n  got:      {cmd}\n  expected: {expected}'


def test_when_build_docker_cmd_called_with_env_path_none_then_env_mount_omitted():
    # Arrange + Act
    cmd = build_docker_cmd(
        image='reward-bench-tier1:0.4',
        submission_path=Path('/tmp/sub.py'),
        env_path=None,
        reports_dir=Path('/tmp/reports'),
        cpus=4.0,
        memory='2g',
        pids_limit=256,
        stagnation_sec=60,
        hard_wall_sec=300.0,
        seed_base=1000,
        n_games=20,
    )

    # Assert: no /env mount
    assert '/env/env_2048.py:ro' not in ''.join(cmd)
    # but submission mount still present
    assert '/tmp/sub.py:/workspace/submission.py:ro' in cmd


def test_when_build_docker_cmd_called_twice_with_same_inputs_then_equal_tuples():
    """Pure function: deterministic."""
    kw = dict(
        image='img', submission_path=Path('/a'), env_path=None,
        reports_dir=Path('/b'), cpus=2.0, memory='1g', pids_limit=128,
        stagnation_sec=60, hard_wall_sec=0.0, seed_base=0, n_games=5,
    )
    assert build_docker_cmd(**kw) == build_docker_cmd(**kw)


def test_when_parse_result_payload_called_with_runner_json_then_returns_game_result_tuple():
    # Arrange
    payload = {
        'games': [
            {'seed': 1000, 'score': 1500, 'max_tile': 128, 'moves': 200,
             'final_state': 'lost', 'walltime_sec': 1.5},
            {'seed': 1001, 'score': 0, 'max_tile': 2, 'moves': 0,
             'final_state': 'solver_error', 'walltime_sec': 0.0},
        ]
    }
    seeds = (1000, 1001, 1002)

    # Act
    games = parse_result_payload(payload, seeds)

    # Assert
    assert isinstance(games, tuple)
    assert len(games) == 3
    # seed 1000: round-trip
    assert games[0] == GameResult(
        seed=1000, score=1500, max_tile=128, moves=200,
        final_state='lost', walltime_sec=1.5,
    )
    # seed 1001: round-trip
    assert games[1] == GameResult(
        seed=1001, score=0, max_tile=2, moves=0,
        final_state='solver_error', walltime_sec=0.0,
    )
    # seed 1002: missing from payload → walltime_exceeded sentinel
    assert games[2] == GameResult(
        seed=1002, score=0, max_tile=2, moves=0,
        final_state='walltime_exceeded', walltime_sec=0.0,
    )


def test_when_parse_result_payload_called_with_empty_games_then_all_sentinels():
    # Arrange
    payload = {'games': []}
    seeds = (1000, 1001)

    # Act
    games = parse_result_payload(payload, seeds)

    # Assert
    assert len(games) == 2
    assert all(g.final_state == 'walltime_exceeded' for g in games)
    assert tuple(g.seed for g in games) == seeds


def test_when_aggregate_attempt_called_with_games_then_returns_attempt_result_with_correct_aggregates():
    # Arrange
    games = (
        GameResult(seed=1000, score=1000, max_tile=128, moves=10,
                   final_state='lost', walltime_sec=1.0),
        GameResult(seed=1001, score=2000, max_tile=256, moves=20,
                   final_state='stagnated', walltime_sec=2.0),
        GameResult(seed=1002, score=3000, max_tile=512, moves=30,
                   final_state='won', walltime_sec=3.0),
    )

    # Act
    result = aggregate_attempt(games, elapsed_sec=42.0, hard_wall_sec=300.0)

    # Assert
    assert isinstance(result, AttemptResult)
    assert result.mean_score == 2000.0
    assert result.median_score == 2000
    assert result.max_max_tile == 512
    assert result.n_games == 3
    assert result.aggregate_walltime_sec == 42.0
    assert result.hard_wall_sec == 300.0
    assert result.stagnated_any is True
    assert result.walltime_exceeded is False
    assert result.games is games   # no copy — pure pass-through


def test_when_aggregate_attempt_called_with_empty_tuple_then_zero_filled_result():
    # Act
    result = aggregate_attempt((), elapsed_sec=0.0, hard_wall_sec=0.0)

    # Assert
    assert result.n_games == 0
    assert result.mean_score == 0.0
    assert result.max_max_tile == 0
    assert result.games == ()
