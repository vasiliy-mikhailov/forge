"""OpenHands-backed SolutionGenerator adapter.

Per SOLUTION-ARCHITECTURE.md §4: OpenHands IS the SolutionGenerator
runtime. Each generate() call constructs a task prompt from the
ContextSnapshot and dispatches it to an OpenHands Conversation.
The runner seam is injectable for testability; the production
binding wires in the real SDK.
"""
from __future__ import annotations

from typing import Callable


class OpenHandsSolutionGenerator:
    def __init__(self, *, _openhands_runner: Callable[[str], str] | None = None):
        if _openhands_runner is None:
            _openhands_runner = _default_openhands_runner
        self._runner = _openhands_runner

    def generate(self, snapshot) -> str:
        prompt = self._render_prompt(snapshot)
        return self._runner(prompt)

    @staticmethod
    def _render_prompt(snapshot) -> str:
        lines = [
            '# Task',
            snapshot.env_spec,
            '',
            '# Best so far',
            f'score: {snapshot.best_so_far.score}',
            f'body:\n{snapshot.best_so_far.body}',
            '',
            '# History (prior iters)',
        ]
        for i, prior in enumerate(snapshot.history_digest):
            lines.append(f'iter {i}: score={prior.score}')
        lines.extend([
            '',
            '# Budget',
            f'iters_remaining: {snapshot.iters_remaining}',
            f'time_remaining_sec: {snapshot.time_remaining_sec}',
            f'budget_sec_per_seed: {snapshot.budget_sec_per_seed}',
            '',
            '# Output',
            'Return the full Python source of a new Solver class.',
        ])
        return '\n'.join(lines)


def _default_openhands_runner(prompt: str) -> str:
    """Production binding: spawn an OpenHands Conversation, run the
    task, return the final submission body. Implemented in a later
    cycle when the SDK is wired into this lab's venv."""
    raise NotImplementedError(
        'OpenHands production binding not yet wired. '
        'Inject _openhands_runner explicitly until then.'
    )
