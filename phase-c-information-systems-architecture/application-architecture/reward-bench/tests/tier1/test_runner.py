"""Tier 1 single-game runner tests. See spec/tier1/runner.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bench.tier1.harness import load_submission
from bench.tier1.runner import run_game


def test_when_reference_fsm_plays_one_game_with_seed_then_score_is_non_negative():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    Solver = load_submission(repo / 'tasks/2048/baselines/reference_fsm.py')
    solver = Solver()

    # Act
    score = run_game(solver, seed=42)

    # Assert
    assert score >= 0


def test_when_reference_fsm_plays_20_canonical_games_then_mean_score_above_zero():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    Solver = load_submission(repo / 'tasks/2048/baselines/reference_fsm.py')

    # Act
    from bench.tier1.runner import run_canonical_eval
    result = run_canonical_eval(Solver)

    # Assert
    assert result['mean_score'] > 0


def test_when_reference_fsm_plays_20_canonical_games_then_mean_score_at_least_4400():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    Solver = load_submission(repo / 'tasks/2048/baselines/reference_fsm.py')

    # Act
    from bench.tier1.runner import run_canonical_eval
    result = run_canonical_eval(Solver)

    # Assert
    assert result['mean_score'] >= 4400, (
        f'reference_fsm dropped below calibration floor: {result["mean_score"]:.1f}'
    )


def test_when_reference_fsm_plays_same_seed_twice_then_scores_match_exactly():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    Solver = load_submission(repo / 'tasks/2048/baselines/reference_fsm.py')
    seed = 1000

    # Act — same solver class, two fresh instances, same seed
    score_a = run_game(Solver(), seed=seed)
    score_b = run_game(Solver(), seed=seed)

    # Assert
    assert score_a == score_b, f'replay mismatch: {score_a} != {score_b}'


def test_when_run_canonical_eval_completes_then_result_has_mean_median_std_max_tile_n_games_walltime():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    Solver = load_submission(repo / 'tasks/2048/baselines/reference_fsm.py')

    # Act
    from bench.tier1.runner import run_canonical_eval
    result = run_canonical_eval(Solver)

    # Assert
    for key in ('mean_score', 'median_score', 'std_score',
                'max_max_tile', 'n_games', 'aggregate_walltime_sec'):
        assert key in result, f'missing key: {key}'
    assert result['n_games'] == 20
    assert result['max_max_tile'] >= 2
    assert result['aggregate_walltime_sec'] > 0
