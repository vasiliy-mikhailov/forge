"""End-to-end bench test. See tests-spec/reward_bench/frameworks/main/."""
from src.reward_bench.entities.bench_config import BenchConfig
from src.tier1.entities.attempt_result import AttemptResult


# Test-friendly small config: keeps cycle wall time bounded.
_FAST = BenchConfig(max_iters=30, n_trials=1, temperature=0.0)


def test_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(model_id='qwen3.6-27b-awq', config=_FAST)

    # Assert: shape-only contract (model quality is a separate cycle)
    assert isinstance(result, AttemptResult)
    assert result.n_games == len(result.games)
    assert result.aggregate_walltime_sec >= 0.0
    if result.n_games == 20:
        # Happy path: scored 20 canonical seeds
        assert result.mean_score >= 0.0
        assert tuple(g.seed for g in result.games) == tuple(range(1000, 1020))
    else:
        # Sentinel: submission shape error
        assert result.n_games == 0
        assert len(result.games) == 0


def test_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(model_id='qwen3.6-27b-awq', config=_FAST)

    # Assert — strict happy-path contract (model produced valid Solver)
    assert isinstance(result, AttemptResult)
    assert result.n_games == 20, (
        f'expected 20 games scored, got {result.n_games} — sentinel emitted, '
        f'model produced wrong-shape submission'
    )
    assert len(result.games) == 20
    bad = [g for g in result.games
           if g.final_state not in ('won', 'lost')]
    assert not bad, f'unexpected final_states: {[g.final_state for g in bad]}'
    assert result.mean_score >= 0.0


def test_when_main_invoked_with_max_iters_one_then_sentinel_emitted():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0),
    )

    # Assert: max_iters=1 is too few turns to produce a valid Solver,
    # so main returns the sentinel AttemptResult.
    assert isinstance(result, AttemptResult)
    assert result.n_games == 0, (
        f'expected sentinel n_games=0 with max_iters=1, got {result.n_games}'
    )
