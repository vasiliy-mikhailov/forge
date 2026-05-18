"""best_score walltime-bounded fitness tests."""
from __future__ import annotations


def test_when_best_score_called_with_walltime_budget_then_returns_argmax_score_under_budget():
    """Pins §7 best_score = max { s.score | s in submissions,
    s.walltime_sec <= t }. An over-budget high-scoring Submission is
    filtered out; the under-budget argmax wins."""
    # Arrange
    from src.reward_bench.use_cases.best_score import best_score
    from src.tier1.entities.submission import Submission

    cheap_bad = Submission(body='', score=10.0, walltime_sec=1.0)
    expensive_great = Submission(body='', score=100.0, walltime_sec=999.0)
    cheap_good = Submission(body='', score=50.0, walltime_sec=2.0)

    # Act
    score = best_score(
        [cheap_bad, expensive_great, cheap_good],
        walltime_budget_sec=10.0,
    )

    # Assert
    assert score == 50.0
