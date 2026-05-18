"""ContextSnapshot tests."""
from __future__ import annotations


def test_when_context_snapshot_constructed_then_carries_all_fields():
    """Pins §2 ContextSnapshot field round-trip. The orchestrator builds
    one of these per iter; the SolutionGenerator's only state is the
    snapshot's fields."""
    # Arrange
    from src.reward_bench.entities.context_snapshot import ContextSnapshot
    from src.tier1.entities.submission import Submission

    best = Submission(body='class Solver: pass\n', score=42.0, walltime_sec=1.0)
    prior_a = Submission(body='', score=0.0, walltime_sec=0.5)
    prior_b = Submission(body='class S: pass\n', score=10.0, walltime_sec=0.7)

    # Act
    snap = ContextSnapshot(
        env_spec='SPEC: write a Solver\n',
        best_so_far=best,
        history_digest=(prior_a, prior_b),
        iters_remaining=5,
        time_remaining_sec=120.0,
        budget_sec_per_seed=12.0,
    )

    # Assert
    assert snap.env_spec == 'SPEC: write a Solver\n'
    assert snap.best_so_far is best
    assert snap.history_digest == (prior_a, prior_b)
    assert snap.iters_remaining == 5
    assert snap.time_remaining_sec == 120.0
    assert snap.budget_sec_per_seed == 12.0
