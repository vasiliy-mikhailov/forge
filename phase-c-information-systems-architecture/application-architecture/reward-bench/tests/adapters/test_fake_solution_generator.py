"""FakeSolutionGenerator tests."""
from __future__ import annotations


def test_when_fake_solution_generator_generate_called_then_returns_scripted_body():
    """Pins the FakeSolutionGenerator scripted-body return."""
    # Arrange
    from src.adapters.fakes.fake_solution_generator import (
        FakeSolutionGenerator,
    )
    from src.reward_bench.entities.context_snapshot import ContextSnapshot
    from src.tier1.entities.submission import Submission

    body = 'class Solver: pass\n'
    fake = FakeSolutionGenerator(body=body)

    snap = ContextSnapshot(
        env_spec='',
        best_so_far=Submission(body='', score=0.0, walltime_sec=0.0),
        history_digest=(),
        iters_remaining=0,
        time_remaining_sec=0.0,
        budget_sec_per_seed=0.0,
    )

    # Act
    result = fake.generate(snap)

    # Assert
    assert result == body
