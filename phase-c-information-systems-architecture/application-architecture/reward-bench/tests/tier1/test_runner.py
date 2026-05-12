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
