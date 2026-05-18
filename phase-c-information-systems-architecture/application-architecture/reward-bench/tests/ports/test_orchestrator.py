"""Orchestrator Port tests."""
from __future__ import annotations


def test_when_orchestrator_port_inspected_then_orchestrate_takes_env_and_cfg():
    """Pins the §7 `Orchestrator` Port. `orchestrate(self, env, cfg)` is
    the named seam both strategies implement; the parameter names ARE
    the contract because the bench composes against them."""
    # Arrange
    import inspect

    from src.ports.orchestrator import Orchestrator

    # Act
    params = list(inspect.signature(Orchestrator.orchestrate).parameters)

    # Assert
    assert params == ['self', 'env', 'cfg']


def test_when_runtime_boundary_manifest_inspected_then_orchestrator_is_listed():
    """Pins §7 Orchestrator Port registration in the runtime-boundary
    architecture manifest."""
    # Arrange
    from pathlib import Path

    manifest_file = (
        Path(__file__).resolve().parents[1]
        / 'architecture' / 'test_runtime_boundary_ports.py'
    )

    # Act
    text = manifest_file.read_text()

    # Assert
    assert '"Orchestrator"' in text
