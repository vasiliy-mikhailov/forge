"""Tier 1 scorer tests. See src-spec/tier1/ and tests-spec/tier1/."""
from pathlib import Path

from src.tier1.harness import load_submission
from src.tier1.scorer import score_one_game


REPO = Path(__file__).resolve().parents[2]


def test_when_solver_plays_one_game_with_seed_then_score_is_non_negative():
    # Arrange
    module = load_submission(REPO / 'tasks/2048/baselines/reference_fsm.py')
    solver = module.Solver()

    # Act
    score = score_one_game(solver, seed=42)

    # Assert
    assert isinstance(score, int) and score >= 0, f'score={score!r}'
