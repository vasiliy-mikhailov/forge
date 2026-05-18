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


def test_when_orchestrate_subagent_per_iter_runs_three_iters_then_each_snapshot_carries_prior_best_and_history(
        tmp_path):
    """§2 cumulative-state plumbing: snapshot.best_so_far is the
    highest-scored prior submission; snapshot.history_digest is the
    tuple of prior submissions in iter order."""
    # Arrange
    from src.reward_bench.adapters.orchestrate_subagent_per_iter import (
        OrchestrateSubagentPerIter,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env
    from src.tier1.entities.attempt_result import AttemptResult

    scripted_scores = [10.0, 5.0, 20.0]
    captured = []

    class RecordingGen:
        def __init__(self):
            self._i = 0

        def generate(self, snapshot):
            captured.append(snapshot)
            self._i += 1
            return f'body-{self._i}'

    class ScriptedRunner:
        def __init__(self, scores):
            self._scores = list(scores)

        def score_body(self, body, seeds, *, hard_wall_sec):
            return AttemptResult(
                mean_score=self._scores.pop(0),
                median_score=0.0, std_score=0.0,
                max_max_tile=0, n_games=1, aggregate_walltime_sec=1.0,
                games=(), hard_wall_sec=hard_wall_sec,
                stagnated_any=False, walltime_exceeded=False,
            )

    runner = ScriptedRunner(scripted_scores)
    adapter = OrchestrateSubagentPerIter(
        solution_generator=RecordingGen(),
        runner=runner,
    )
    env = Env(tasks_dir=tmp_path, canonical_scorer=runner)
    cfg = BenchConfig(max_iters=3)

    # Act
    list(adapter.orchestrate(env, cfg))

    # Assert — iter 1: clean snapshot
    assert captured[0].best_so_far.score == 0.0
    assert captured[0].history_digest == ()

    # iter 2: iter 1 in history; iter 1 is best (10.0)
    assert captured[1].best_so_far.score == 10.0
    assert captured[1].best_so_far.body == 'body-1'
    assert len(captured[1].history_digest) == 1
    assert captured[1].history_digest[0].score == 10.0
    assert captured[1].history_digest[0].body == 'body-1'

    # iter 3: iter 1+2 in history; iter 1 still best (10 > 5)
    assert captured[2].best_so_far.score == 10.0
    assert captured[2].best_so_far.body == 'body-1'
    assert len(captured[2].history_digest) == 2
    assert captured[2].history_digest[0].score == 10.0
    assert captured[2].history_digest[1].score == 5.0
    assert captured[2].history_digest[1].body == 'body-2'
