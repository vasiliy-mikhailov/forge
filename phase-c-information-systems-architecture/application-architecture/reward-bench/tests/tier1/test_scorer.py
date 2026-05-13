"""Tier 1 scorer tests. See src-spec/tier1/ and tests-spec/tier1/."""
from pathlib import Path

from src.tier1.harness import load_submission
from src.tier1.scorer import score_one_game, run_canonical_eval


REPO = Path(__file__).resolve().parents[2]


def test_when_solver_plays_one_game_with_seed_then_score_is_non_negative():
    # Arrange
    module = load_submission(REPO / 'tasks/2048/baselines/reference_fsm.py')
    solver = module.Solver()

    # Act
    score = score_one_game(solver, seed=42)

    # Assert
    assert isinstance(score, int) and score >= 0, f'score={score!r}'


def test_when_canonical_eval_played_then_result_has_full_attempt_schema():
    # Arrange
    module = load_submission(REPO / 'tasks/2048/baselines/reference_fsm.py')

    # Act
    result = run_canonical_eval(module.Solver)

    # Assert
    for key in ('mean_score', 'median_score', 'std_score',
                'max_max_tile', 'n_games', 'aggregate_walltime_sec', 'seeds'):
        assert key in result, f'missing key: {key}; result keys = {list(result)}'
    assert result['n_games'] == 20, f'n_games={result["n_games"]}'
    assert result['seeds'] == list(range(1000, 1020)), f'seeds={result["seeds"]}'
    assert result['max_max_tile'] >= 2, f'max_max_tile={result["max_max_tile"]}'
    assert result['aggregate_walltime_sec'] > 0, f'walltime={result["aggregate_walltime_sec"]}'


def test_when_canonical_eval_replayed_then_mean_score_matches_exactly():
    # Arrange
    module_a = load_submission(REPO / 'tasks/2048/baselines/reference_fsm.py')
    module_b = load_submission(REPO / 'tasks/2048/baselines/reference_fsm.py')

    # Act
    run_a = run_canonical_eval(module_a.Solver)
    run_b = run_canonical_eval(module_b.Solver)

    # Assert
    assert run_a['mean_score'] == run_b['mean_score'], (
        f'mean drift: {run_a["mean_score"]} vs {run_b["mean_score"]}'
    )
    assert run_a['median_score'] == run_b['median_score']
    assert run_a['max_max_tile'] == run_b['max_max_tile']
