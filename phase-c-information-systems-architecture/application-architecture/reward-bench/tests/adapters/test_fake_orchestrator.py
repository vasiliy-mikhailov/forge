"""FakeOrchestrator tests."""
from __future__ import annotations


def test_when_fake_orchestrator_orchestrate_called_then_yields_scripted_submissions():
    """Pins the FakeOrchestrator scripted-result behaviour."""
    # Arrange
    from src.adapters.fakes.fake_orchestrator import FakeOrchestrator
    from src.tier1.entities.submission import Submission

    a = Submission(body='', score=1.0, walltime_sec=1.0)
    b = Submission(body='', score=2.0, walltime_sec=2.0)
    fake = FakeOrchestrator(submissions=(a, b))

    # Act
    result = list(fake.orchestrate(env=None, cfg=None))

    # Assert
    assert result == [a, b]


def test_when_runtime_boundary_manifest_inspected_then_fake_orchestrator_module_is_referenced():
    """Pins ADR-0018 Fake registration for the §7 Orchestrator Port."""
    # Arrange
    from pathlib import Path

    manifest_file = (
        Path(__file__).resolve().parents[1]
        / 'architecture' / 'test_runtime_boundary_ports.py'
    )

    # Act
    text = manifest_file.read_text()

    # Assert
    assert 'fake_orchestrator' in text
