"""dominates_at_budget harness tests."""
from __future__ import annotations


def test_when_strong_orchestrator_yields_higher_scoring_submissions_then_dominates_at_budget_returns_true():
    """Pins the §7 dominance harness positive case: when the strong
    orchestrator's best in-budget submission scores higher than the
    weak's, the harness returns True."""
    # Arrange
    from src.adapters.fakes.fake_orchestrator import FakeOrchestrator
    from src.reward_bench.use_cases.dominates_at_budget import (
        dominates_at_budget,
    )
    from src.tier1.entities.submission import Submission

    s100 = Submission(body='', score=100.0, walltime_sec=1.0)
    s10 = Submission(body='', score=10.0, walltime_sec=1.0)
    strong = FakeOrchestrator(submissions=(s100,))
    weak = FakeOrchestrator(submissions=(s10,))

    # Act
    dominated = dominates_at_budget(
        strong, weak,
        env=None, cfg=None, walltime_budget_sec=10.0,
    )

    # Assert
    assert dominated is True


def test_when_strong_and_weak_yield_equal_best_score_then_dominates_at_budget_returns_false():
    """Pins the §7 strict-`>` semantics: a tie at the same score does
    NOT count as domination. The planned shape must beat the current
    one, not merely match it."""
    # Arrange
    from src.adapters.fakes.fake_orchestrator import FakeOrchestrator
    from src.reward_bench.use_cases.dominates_at_budget import (
        dominates_at_budget,
    )
    from src.tier1.entities.submission import Submission

    same_score_strong = Submission(body='', score=50.0, walltime_sec=1.0)
    same_score_weak = Submission(body='', score=50.0, walltime_sec=1.0)
    strong = FakeOrchestrator(submissions=(same_score_strong,))
    weak = FakeOrchestrator(submissions=(same_score_weak,))

    # Act
    dominated = dominates_at_budget(
        strong, weak,
        env=None, cfg=None, walltime_budget_sec=10.0,
    )

    # Assert
    assert dominated is False
