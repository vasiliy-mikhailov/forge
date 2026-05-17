"""best_submission tests."""
from __future__ import annotations


def test_when_best_submission_called_with_two_submissions_then_returns_higher_score():
    """Pins the §7 argmax-by-score primitive. `bench` composes this
    with an `Orchestrator` to define the top-level fitness target."""
    # Arrange
    from src.reward_bench.use_cases.best_submission import best_submission
    from src.tier1.entities.submission import Submission

    a = Submission(body='from foo import bar\n', score=10.0, walltime_sec=1.0)
    b = Submission(body='from baz import qux\n', score=20.0, walltime_sec=2.0)

    # Act
    winner = best_submission([a, b])

    # Assert
    assert winner is b
