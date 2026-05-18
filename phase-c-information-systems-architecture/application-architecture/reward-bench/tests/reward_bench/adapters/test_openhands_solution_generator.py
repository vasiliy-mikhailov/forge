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

    def stub_runner(prompt: str, deadline_sec: float) -> str:
        captured['prompt'] = prompt
        captured['deadline_sec'] = deadline_sec
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


def test_when_openhands_solution_generator_generate_called_with_snapshot_time_then_runner_receives_that_deadline():
    """Per §4 binding time-budget contract: the runner closure
    receives snapshot.time_remaining_sec as its deadline argument.
    The host uses this to wrap docker in `timeout N`."""
    # Arrange
    from src.reward_bench.adapters.openhands_solution_generator import (
        OpenHandsSolutionGenerator,
    )
    from src.reward_bench.entities.context_snapshot import ContextSnapshot
    from src.tier1.entities.submission import Submission

    captured = {}

    def stub_runner(prompt: str, deadline_sec: float) -> str:
        captured['deadline_sec'] = deadline_sec
        return ''

    adapter = OpenHandsSolutionGenerator(_openhands_runner=stub_runner)
    snap = ContextSnapshot(
        env_spec='SPEC',
        best_so_far=Submission(body='', score=0.0, walltime_sec=0.0),
        history_digest=(),
        iters_remaining=0,
        time_remaining_sec=42.5,
        budget_sec_per_seed=0.0,
    )

    # Act
    adapter.generate(snap)

    # Assert
    assert captured['deadline_sec'] == 42.5


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

        def stub_runner(prompt, deadline_sec):
            captured['prompt'] = prompt
            captured['deadline_sec'] = deadline_sec
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


def test_when_openhands_solution_generator_generate_called_then_prompt_instructs_agent_to_emit_fenced_python_block():
    """Per §4 binding: the rendered prompt must instruct the agent
    to emit its final Solver code as a fenced ```python ... ```
    block in the last assistant message — that's the body
    extraction contract."""
    # Arrange
    from src.reward_bench.adapters.openhands_solution_generator import (
        OpenHandsSolutionGenerator,
    )
    from src.reward_bench.entities.context_snapshot import ContextSnapshot
    from src.tier1.entities.submission import Submission

    captured = {}

    def stub_runner(prompt: str, deadline_sec: float) -> str:
        captured['prompt'] = prompt
        return ''

    adapter = OpenHandsSolutionGenerator(_openhands_runner=stub_runner)
    snap = ContextSnapshot(
        env_spec='SPEC',
        best_so_far=Submission(body='', score=0.0, walltime_sec=0.0),
        history_digest=(),
        iters_remaining=0,
        time_remaining_sec=0.0,
        budget_sec_per_seed=0.0,
    )

    # Act
    adapter.generate(snap)

    # Assert: prompt names the fenced-block convention.
    prompt = captured['prompt']
    assert '```python' in prompt
    assert 'fenced' in prompt.lower() or 'last assistant message' in prompt
    # The prompt explicitly names the # Output convention — file
    # outputs from the agent are agent-internal scratch only; the
    # boundary contract is the fenced block, not a file path.
    assert '# Output' in prompt


import pytest


@pytest.mark.live
def test_when_openhands_solution_generator_generate_called_with_real_vllm_then_returns_python_source_with_solver_class(
        vllm_base_url, vllm_api_key):
    """§4 live: docker-wrapped OpenHands runner + real vLLM +
    simple snapshot → Python source containing a Solver class
    extracted from the agent's final fenced python block."""
    # Arrange
    from src.adapters.vllm_openai_client import VllmOpenAIClient
    from src.reward_bench.adapters.openhands_solution_generator import (
        OpenHandsSolutionGenerator,
    )
    from src.reward_bench.entities.context_snapshot import ContextSnapshot
    from src.tier1.entities.submission import Submission

    mc = VllmOpenAIClient(
        base_url=vllm_base_url,
        api_key=vllm_api_key,
        default_model_id='qwen3.6-27b-awq',
    )
    generator = OpenHandsSolutionGenerator(model_client=mc)

    snap = ContextSnapshot(
        env_spec=(
            'Write a Python class Solver with a method '
            '`move(self, board) -> str` that returns the string "W".'
        ),
        best_so_far=Submission(body='', score=0.0, walltime_sec=0.0),
        history_digest=(),
        iters_remaining=0,
        time_remaining_sec=120.0,
        budget_sec_per_seed=12.0,
    )

    # Act
    body = generator.generate(snap)

    # Assert
    assert 'class Solver' in body, (
        f'OpenHands did not produce a Solver class; '
        f'first 200 chars: {body[:200]!r}'
    )
