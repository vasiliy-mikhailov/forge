"""BenchConfig tests. See tests-spec/reward_bench/entities/bench_config/."""
import dataclasses

import pytest

from src.reward_bench.entities.bench_config import BenchConfig


def test_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply():
    # Arrange (no fixtures — pure dataclass)

    # Act
    cfg = BenchConfig()

    # Assert: ADR 0003 defaults
    assert cfg.max_iters == 500
    assert cfg.n_trials == 10
    assert cfg.temperature == 0.7
    assert cfg.max_no_improve == 999999
    assert cfg.finish_floor == 0.0
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.max_iters = 0  # type: ignore[misc]


def test_when_bench_config_constructed_with_overrides_then_overrides_apply():
    # Arrange (override every field)

    # Act
    cfg = BenchConfig(
        max_iters=30,
        n_trials=1,
        temperature=0.0,
        max_no_improve=5,
        finish_floor=1000.0,
    )

    # Assert
    assert cfg.max_iters == 30
    assert cfg.n_trials == 1
    assert cfg.temperature == 0.0
    assert cfg.max_no_improve == 5
    assert cfg.finish_floor == 1000.0
