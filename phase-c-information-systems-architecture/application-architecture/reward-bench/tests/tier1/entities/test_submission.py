"""Submission entity tests."""
from __future__ import annotations


def test_when_submission_constructed_then_carries_body_score_walltime():
    """Pins the §7 `Submission` entity. The frozen dataclass carries
    (body, score, walltime_sec) — what the per-iter orchestrator returns
    to the main process."""
    # Arrange
    from src.tier1.entities.submission import Submission

    # Act
    s = Submission(body='from foo import bar\n', score=1234.5, walltime_sec=12.7)

    # Assert
    assert s.body == 'from foo import bar\n'
    assert s.score == 1234.5
    assert s.walltime_sec == 12.7
