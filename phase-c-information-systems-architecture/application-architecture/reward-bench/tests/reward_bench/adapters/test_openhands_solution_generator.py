"""OpenHandsSolutionGenerator adapter tests."""
from __future__ import annotations


def test_when_openhands_solution_generator_generate_called_then_runner_receives_prompt_containing_env_spec():
    """Pins §4 OpenHands adapter prompt seam: the injected runner
    receives a prompt that includes snapshot.env_spec, and its return
    becomes the SolverBody."""
    # Arrange
    from src.reward_bench.adapters.openhands_solution_generator import (
        OpenHandsSolutionGenerator,
    )
    from src.reward_bench.entities.context_snapshot import ContextSnapshot
    from src.tier1.entities.submission import Submission

    captured = {}

    def stub_runner(prompt: str) -> str:
        captured['prompt'] = prompt
        return 'class Solver: pass\n'

    adapter = OpenHandsSolutionGenerator(_openhands_runner=stub_runner)

    snap = ContextSnapshot(
        env_spec='SPEC: write a Solver',
        best_so_far=Submission(body='', score=0.0, walltime_sec=0.0),
        history_digest=(),
        iters_remaining=0,
        time_remaining_sec=0.0,
        budget_sec_per_seed=0.0,
    )

    # Act
    body = adapter.generate(snap)

    # Assert
    assert 'SPEC: write a Solver' in captured['prompt']
    assert body == 'class Solver: pass\n'


def test_when_openhands_solution_generator_constructed_with_model_client_then_default_runner_uses_clients_url_and_key():
    """Pins §4 OpenHands wiring entry point: model_client at
    construction; default runner factory receives it."""
    # Arrange
    from src.reward_bench.adapters.openhands_solution_generator import (
        OpenHandsSolutionGenerator,
    )
    from src.reward_bench.entities.context_snapshot import ContextSnapshot
    from src.tier1.entities.submission import Submission

    class FakeMC:
        base_url = 'http://x'
        api_key = 'k'
        model_id = 'm'

    fake_mc = FakeMC()
    captured = {}

    def fake_factory(model_client):
        captured['model_client'] = model_client

        def stub_runner(prompt):
            captured['prompt'] = prompt
            return 'class Solver: pass\n'

        return stub_runner

    adapter = OpenHandsSolutionGenerator(
        model_client=fake_mc,
        _make_runner=fake_factory,
    )

    snap = ContextSnapshot(
        env_spec='SPEC: write a Solver',
        best_so_far=Submission(body='', score=0.0, walltime_sec=0.0),
        history_digest=(),
        iters_remaining=0,
        time_remaining_sec=0.0,
        budget_sec_per_seed=0.0,
    )

    # Act
    body = adapter.generate(snap)

    # Assert
    assert captured['model_client'] is fake_mc
    assert 'SPEC: write a Solver' in captured['prompt']
    assert body == 'class Solver: pass\n'
