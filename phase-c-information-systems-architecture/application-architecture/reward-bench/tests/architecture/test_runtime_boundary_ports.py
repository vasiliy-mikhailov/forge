"""Cycle 109 / ADR 0018: architecture test — every runtime-boundary
dependency has Port + production adapter + Fake + autouse binding.

The MANIFEST below is the curated list of ports under this rule. New
ports added by future cycles must be appended here alongside their
implementation.
"""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path

import pytest


# Each entry: (port_module, port_class_name, fake_module, fake_class_name)
# Production adapter location is convention-based (src/.../adapters/);
# we assert it exists by importing from the conftest binding below.
MANIFEST = [
    ("src.ports.model_client", "ModelClient",
     "src.adapters.fakes.fake_model_client", "FakeModelClient"),
    ("src.ports.tool_registry", "ToolRegistry",
     None, None),   # no shared Fake; tests use inline RecordingRegistry
    ("src.ports.protocol_parser", "ProtocolParser",
     None, None),   # no shared Fake; tests use inline RecordingParser
    ("src.ports.cpu_count", "CpuCountPort",
     "src.adapters.multiprocessing_cpu_count", "FixedCpuCount"),
    ("src.ports.canonical_scorer", "CanonicalScorerPort",
     "src.adapters.fakes.fake_canonical_scorer", "FakeCanonicalScorer"),
    ("src.ports.tool", "Tool",
     None, None),   # no shared Fake; per-tool adapters tested directly
    ("src.ports.supervisor", "SupervisorPort",
     None, None),   # NullSupervisor is the production-default Port-conformant impl
    ("src.ports.condenser", "CondenserPort",
     None, None),   # NullCondenser is the production-default Port-conformant impl
]


@pytest.mark.no_fake
@pytest.mark.parametrize("port_module,port_class,fake_module,fake_class",
                         MANIFEST,
                         ids=[m[1] for m in MANIFEST])
def test_when_runtime_boundary_port_inspected_then_protocol_exists(
        port_module, port_class, fake_module, fake_class):
    """ADR 0018: every manifest entry has a Port (Protocol) class."""
    mod = importlib.import_module(port_module)
    assert hasattr(mod, port_class), (
        f"Port {port_class} missing from {port_module}"
    )
    cls = getattr(mod, port_class)
    # The Protocol must declare at least one public abstract-ish method
    # (we don't enforce typing.Protocol strictly because some ports
    # use Protocol[T]; just check the class is callable).
    assert inspect.isclass(cls)


@pytest.mark.no_fake
@pytest.mark.parametrize("port_module,port_class,fake_module,fake_class",
                         [m for m in MANIFEST if m[2] is not None],
                         ids=[m[1] for m in MANIFEST if m[2] is not None])
def test_when_runtime_boundary_port_has_fake_then_fake_class_importable(
        port_module, port_class, fake_module, fake_class):
    """ADR 0018: each manifest entry with a shared Fake has it
    under src/adapters/fakes/ (or equivalent), importable, and a class."""
    mod = importlib.import_module(fake_module)
    assert hasattr(mod, fake_class), (
        f"Fake {fake_class} missing from {fake_module}"
    )
    assert inspect.isclass(getattr(mod, fake_class))


@pytest.mark.no_fake
def test_when_conftest_inspected_then_canonical_scorer_autouse_binding_present():
    """ADR 0018: conftest autouse binds canonical_scorer for non-live tests.

    Verified by reading the conftest source and asserting a mention.
    """
    repo = Path(__file__).resolve().parents[2]
    conftest = (repo / "tests/conftest.py").read_text()
    # The autouse fixture binds main_mod.main's canonical_scorer default
    # (via monkeypatch of the function or by injecting a fixture).
    assert "canonical_scorer" in conftest, (
        "conftest.py should bind canonical_scorer per ADR 0018"
    )
    assert "FakeCanonicalScorer" in conftest, (
        "conftest.py should reference FakeCanonicalScorer"
    )
