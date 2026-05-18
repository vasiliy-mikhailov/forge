"""OpenHands-backed SolutionGenerator adapter.

Per SOLUTION-ARCHITECTURE.md §4. OpenHands IS the SolutionGenerator
runtime. The adapter renders a ContextSnapshot into a prompt,
hands it to a runner closure that wraps an OpenHands Conversation,
returns the body.

Wiring:

- Tests inject `_openhands_runner` directly — fully bypasses the
  SDK.
- Production binding takes `model_client`; the default factory
  `make_default_openhands_runner(model_client)` returns a closure
  that lazily imports `openhands.sdk` on call.
"""
from __future__ import annotations

from typing import Callable


class OpenHandsSolutionGenerator:
    def __init__(
        self,
        model_client=None,
        *,
        _openhands_runner: Callable[[str], str] | None = None,
        _make_runner: Callable[[object], Callable[[str], str]] | None = None,
    ):
        if _openhands_runner is None:
            factory = _make_runner or make_default_openhands_runner
            if model_client is None:
                raise ValueError(
                    'OpenHandsSolutionGenerator: pass either model_client '
                    '(for the default OpenHands runner) or _openhands_runner '
                    '(for tests)'
                )
            _openhands_runner = factory(model_client)
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


def make_default_openhands_runner(model_client):
    """Production runner factory. Returns a closure that constructs
    an OpenHands Conversation per call and returns the resulting
    submission body. SDK imports are lazy — the closure raises
    ImportError if openhands.sdk is not installed."""
    def _runner(prompt: str) -> str:
        from openhands.sdk import LLM, Agent, Conversation, Tool

        llm = LLM(
            model=f'openai/{model_client.model_id}',
            api_key=model_client.api_key,
            base_url=model_client.base_url,
            usage_id='reward-bench-solution-generator',
        )
        agent = Agent(llm=llm, tools=[Tool(name='task_tool_set')])
        # Workspace tempdir owned by this closure: OpenHands writes
        # submission.py here, we read it back as the body. The
        # tempdir lives only for this call.
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            conv = Conversation(agent=agent, workspace=str(td))
            conv.send_message(prompt)
            conv.run()
            sp = Path(td) / 'submission.py'
            return sp.read_text() if sp.exists() else ''
    return _runner
