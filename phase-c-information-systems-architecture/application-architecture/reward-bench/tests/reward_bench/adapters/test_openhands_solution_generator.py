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
