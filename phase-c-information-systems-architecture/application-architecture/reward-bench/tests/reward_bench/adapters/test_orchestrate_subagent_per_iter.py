"""OrchestrateSubagentPerIter adapter tests."""
from __future__ import annotations


def test_when_orchestrate_subagent_per_iter_called_with_max_iters_one_then_yields_submission_with_generator_body_and_runner_score(
        tmp_path):
    """Pins §2 three-role composition at minimum: one iter, the
    SolutionGenerator's body and the Runner's score flow into the
    yielded Submission."""
    # Arrange
    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.adapters.fakes.fake_solution_generator import (
        FakeSolutionGenerator,
    )
    from src.reward_bench.adapters.orchestrate_subagent_per_iter import (
        OrchestrateSubagentPerIter,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env
    from src.tier1.entities.attempt_result import AttemptResult

    BODY = 'class Solver: pass\n'

    fake_gen = FakeSolutionGenerator(body=BODY)
    fake_scorer = FakeCanonicalScorer(
        default_result=AttemptResult(
            mean_score=99.0, median_score=99.0, std_score=0.0,
            max_max_tile=128, n_games=5, aggregate_walltime_sec=3.0,
            games=(), hard_wall_sec=0.0,
            stagnated_any=False, walltime_exceeded=False,
        ),
    )

    adapter = OrchestrateSubagentPerIter(
        solution_generator=fake_gen,
        runner=fake_scorer,
    )
    env = Env(tasks_dir=tmp_path, canonical_scorer=fake_scorer)
    cfg = BenchConfig(max_iters=1)

    # Act
    subs = list(adapter.orchestrate(env, cfg))

    # Assert
    assert len(subs) == 1
    assert subs[0].body == BODY
    assert subs[0].score == 99.0
