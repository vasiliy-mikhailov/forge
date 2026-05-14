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
    assert cfg.hard_wall_sec == 0.0  # cycle 24: ADR 0003 disabled default
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


def test_when_bench_config_constructed_with_hard_wall_sec_override_then_field_preserved():
    """Cycle 24: hard_wall_sec override survives the constructor.

    Companion default pin lives in
    test_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply.
    """
    # Arrange (no fixtures — pure dataclass construct)

    # Act
    cfg = BenchConfig(hard_wall_sec=60.0)

    # Assert
    assert cfg.hard_wall_sec == 60.0



def test_when_bench_config_default_then_supervisor_every_k_is_zero():
    """Cycle 35: ADR 0005 cadence knob. Default 0 keeps cycle-12 behavior."""
    from src.reward_bench.entities.bench_config import BenchConfig
    assert BenchConfig().supervisor_every_k == 0
    assert BenchConfig(supervisor_every_k=10).supervisor_every_k == 10
