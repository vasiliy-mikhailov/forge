"""bench_main production-binding tests."""
from __future__ import annotations


def test_when_bench_main_called_with_injected_factories_then_orchestrator_submission_is_returned():
    """Pins the §7 production-binding composition: bench_main builds
    env via env_factory(target), constructs an Orchestrator via
    orchestrator_factory(env), and returns bench(orch, env, cfg).
    orchestrator_factory receives env so it can read
    env.model_client + env.canonical_scorer."""
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
    env_sentinel = object()

    captured = {}

    def fake_env_factory(t):
        captured['target'] = t
        return env_sentinel

    def fake_orch_factory(env):
        captured['env'] = env
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
    assert captured['env'] is env_sentinel


def test_when_bench_main_default_orchestrator_factory_used_then_chain_is_subagent_per_iter_with_openhands_generator():
    """§2 + §4: the default orchestrator_factory builds
    OrchestrateSubagentPerIter wrapping OpenHandsSolutionGenerator
    (model_client from env) and env.canonical_scorer as Runner."""
    # Arrange
    from src.reward_bench.adapters.openhands_solution_generator import (
        OpenHandsSolutionGenerator,
    )
    from src.reward_bench.adapters.orchestrate_subagent_per_iter import (
        OrchestrateSubagentPerIter,
    )
    from src.reward_bench.frameworks.bench_main import (
        _default_orchestrator_factory,
    )

    class _MC:
        base_url = 'http://stub:8000'
        api_key = 'sk-stub'
        model_id = 'stub-model'

    class _Env:
        model_client = _MC()
        canonical_scorer = object()

    env = _Env()

    # Act
    orchestrator = _default_orchestrator_factory(env)

    # Assert
    assert isinstance(orchestrator, OrchestrateSubagentPerIter)
    assert isinstance(orchestrator._gen, OpenHandsSolutionGenerator)
    assert orchestrator._runner is env.canonical_scorer
