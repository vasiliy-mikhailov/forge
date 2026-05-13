"""Clean Architecture wire-up test: score_submission + GameBoard2048Adapter
matches legacy scorer.run_canonical_eval. See tests-spec/clean_arch/."""
from pathlib import Path

from src.adapters.game_board_2048 import GameBoard2048Adapter
from src.tier1.harness import load_submission
from src.tier1.scorer import run_canonical_eval
from src.use_cases.score_submission import score_submission


REPO = Path(__file__).resolve().parents[2]


def test_when_score_submission_wired_with_adapter_then_returns_attempt_result_matching_legacy_scorer():
    # Arrange
    module = load_submission(REPO / 'tasks/2048/baselines/reference_fsm.py')
    seeds = range(1000, 1020)
    adapter = GameBoard2048Adapter()

    # Act
    legacy = run_canonical_eval(module.Solver)
    clean = score_submission(module.Solver, seeds, adapter)

    # Assert
    assert clean.n_games == legacy['n_games']
    assert clean.mean_score == legacy['mean_score']
    assert clean.median_score == legacy['median_score']
    assert clean.max_max_tile == legacy['max_max_tile']
    assert clean.seeds == tuple(seeds)
