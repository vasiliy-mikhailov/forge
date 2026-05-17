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
