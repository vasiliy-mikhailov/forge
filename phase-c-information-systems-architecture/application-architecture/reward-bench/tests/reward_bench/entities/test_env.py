"""Env entity tests."""
from __future__ import annotations


def test_when_env_constructed_then_carries_tasks_dir_and_canonical_scorer():
    """Pins the §7 `Env` bundle: tasks_dir + canonical_scorer. The two
    seams `score :: Env -> Submission -> Score` and
    `orchestrate :: Env -> BenchConfig -> [Submission]` both read."""
    # Arrange
    from pathlib import Path

    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.entities.env import Env

    tasks_dir = Path('/tmp/x')
    fake = FakeCanonicalScorer()

    # Act
    env = Env(tasks_dir=tasks_dir, canonical_scorer=fake)

    # Assert
    assert env.tasks_dir == tasks_dir
    assert env.canonical_scorer is fake


def test_when_env_constructed_with_model_client_then_field_preserved():
    """Pins the §7 Env.model_client field. Per the wrapper-encapsulation
    principle, URL strings don't belong in the bench API; Env holds a
    pre-bound ModelClient."""
    # Arrange
    from pathlib import Path

    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.entities.env import Env

    fake_mc = object()  # sentinel — testing field round-trip, not behaviour

    # Act
    env = Env(
        tasks_dir=Path('/tmp/x'),
        canonical_scorer=FakeCanonicalScorer(),
        model_client=fake_mc,
    )

    # Assert
    assert env.model_client is fake_mc
