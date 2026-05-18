"""CanonicalScorerPort tests."""
from __future__ import annotations


def test_when_canonical_scorer_port_inspected_then_score_body_takes_body_and_seeds():
    """Pins §7.5 body-in API on the Port: score_body(self, body, seeds, ...)."""
    # Arrange
    import inspect

    from src.ports.canonical_scorer import CanonicalScorerPort

    # Act
    params = list(inspect.signature(CanonicalScorerPort.score_body).parameters)

    # Assert
    assert params[0] == 'self'
    assert params[1] == 'body'
    assert params[2] == 'seeds'
