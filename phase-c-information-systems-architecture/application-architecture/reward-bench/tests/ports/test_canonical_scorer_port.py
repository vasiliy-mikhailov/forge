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


def test_when_canonical_scorer_port_inspected_then_path_based_score_is_absent():
    """Pins §7.5 completion: no path-based .score across the canonical
    scorer surface. Only .score_body remains as the body-in entry
    point. DockerCanonicalScorer's path-based work is renamed to
    ._score_path (private)."""
    # Arrange
    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.adapters.in_process_canonical_scorer import (
        InProcessCanonicalScorer,
    )
    from src.ports.canonical_scorer import CanonicalScorerPort
    from src.tier1.adapters.docker_canonical_scorer import (
        DockerCanonicalScorer,
    )

    # Assert
    assert not hasattr(CanonicalScorerPort, 'score'), (
        'CanonicalScorerPort.score must be removed (use score_body)')
    assert not hasattr(FakeCanonicalScorer, 'score'), (
        'FakeCanonicalScorer.score must be removed')
    assert not hasattr(InProcessCanonicalScorer, 'score'), (
        'InProcessCanonicalScorer.score must be removed')
    # DockerCanonicalScorer's internal path-based body is private:
    assert not hasattr(DockerCanonicalScorer, 'score'), (
        'DockerCanonicalScorer.score must be renamed to ._score_path')
    assert hasattr(DockerCanonicalScorer, '_score_path')
    # All adapters keep .score_body as the body-in API:
    assert hasattr(CanonicalScorerPort, 'score_body')
    assert hasattr(FakeCanonicalScorer, 'score_body')
    assert hasattr(InProcessCanonicalScorer, 'score_body')
    assert hasattr(DockerCanonicalScorer, 'score_body')
