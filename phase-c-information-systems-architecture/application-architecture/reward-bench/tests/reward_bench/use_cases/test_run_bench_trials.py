"""run_bench_trials tests.

See tests-spec/reward_bench/use_cases/run_bench_trials/."""
from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.use_cases.run_bench_trials import run_bench_trials
from src.tier1.entities.attempt_result import AttemptResult


def test_when_run_bench_trials_called_with_n_trials_three_then_returns_tuple_of_three_attempt_results():
    # Arrange
    config = BenchConfig(max_iters=1, n_trials=3, temperature=0.0)
    calls = []
    def stub_runner(model_id, config):
        calls.append({'model_id': model_id, 'config': config})
        return AttemptResult(
            mean_score=float(len(calls)),
            median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=0,
            aggregate_walltime_sec=0.0,
            games=(),
        )

    # Act
    trials = run_bench_trials(
        model_id='stub-model',
        config=config,
        runner=stub_runner,
    )

    # Assert
    assert isinstance(trials, tuple)
    assert len(trials) == 3
    assert len(calls) == 3
    for call in calls:
        assert call['model_id'] == 'stub-model'
        assert call['config'] is config
    assert [t.mean_score for t in trials] == [1.0, 2.0, 3.0]
