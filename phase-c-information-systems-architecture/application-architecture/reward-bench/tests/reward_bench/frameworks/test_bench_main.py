"""bench_main production-binding tests."""
from __future__ import annotations


def test_when_bench_main_called_with_injected_factories_then_orchestrator_submission_is_returned():
    """Pins the §7 production-binding composition: bench_main builds
    env via env_factory(target), constructs an Orchestrator via
    orchestrator_factory(), and returns bench(orch, env, cfg)."""
    # Arrange
    from src.adapters.fakes.fake_orchestrator import FakeOrchestrator
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.model_target import ModelTarget
    from src.reward_bench.frameworks.bench_main import bench_main
    from src.tier1.entities.submission import Submission

    target = ModelTarget(
        id='m1',
        hf_path='/fake/m1',
        served_name='m1-served',
        max_model_len=4096,
        tool_call_parser='hermes',
    )
    expected = Submission(body='', score=42.0, walltime_sec=1.0)

    captured = {}

    def fake_env_factory(t):
        captured['target'] = t
        return object()  # FakeOrchestrator ignores env

    def fake_orch_factory():
        return FakeOrchestrator(submissions=(expected,))

    # Act
    result = bench_main(
        target,
        BenchConfig(),
        env_factory=fake_env_factory,
        orchestrator_factory=fake_orch_factory,
    )

    # Assert
    assert result is expected
    assert captured['target'] is target
