"""§4 OpenHands-backed SolutionGenerator adapter.

Per SOLUTION-ARCHITECTURE.md §4: OpenHands IS the SolutionGenerator
runtime. The adapter renders a ContextSnapshot into a prompt
(task + budget + fenced-output instruction), hands it to a runner
closure that wraps an OpenHands Conversation, and returns the
fenced python block from the agent's last assistant message.

No file IO across the binding — the body lives in the message,
not in a tempdir.

Wiring:

- Tests inject `_openhands_runner` directly — fully bypasses the
  SDK.
- Production binding takes `model_client`; the default factory
  `make_default_openhands_runner(model_client)` returns a closure
  that lazily imports `openhands.sdk` on call.
"""
from __future__ import annotations

from typing import Callable


# Inner-loop cap. Each iteration = one LLM response (may include
# tool calls). Default SDK value is 500 — way too high for a
# 60s-ish wallclock budget. Eight iterations is enough for ~3-5
# dev-test cycles plus a final-answer emission.
_DEFAULT_MAX_ITER = 8


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
        """Per §4 binding interface: task + budget + output."""
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
            'IMPORTANT — converge fast. You have ~5 minutes total and only '
            f'~{_DEFAULT_MAX_ITER} inner iterations before the harness '
            'force-stops you. Use the dev test harness 2-3 times to '
            'validate, then COMMIT.',
            '',
            'When ready, emit your final Solver code as a fenced '
            '```python ... ``` block in your last assistant message. '
            'The harness extracts the last fenced block as the '
            'submission body. The fenced block IS the submission — '
            'put your best version there. Do not append more tool calls '
            'after the final block.',
        ])
        return '\n'.join(lines)


def make_default_openhands_runner(model_client):
    """Production runner factory. Returns a closure that constructs
    an OpenHands Conversation per call and returns the fenced
    python block extracted from the agent's last assistant message.
    SDK imports are lazy — the closure raises ImportError if
    openhands.sdk is not installed."""
    def _runner(prompt: str) -> str:
        from openhands.sdk import LLM, Agent, Conversation
        from openhands.tools.preset.default import (
            get_default_tools, register_default_tools,
        )

        from src.reward_bench.adapters.extract_fenced_python import (
            extract_fenced_python,
        )

        # FileEditor + Terminal + TaskTracker; no browser.
        register_default_tools(enable_browser=False)
        tools = get_default_tools(enable_browser=False)

        base_url = model_client.base_url.rstrip('/')
        if not base_url.endswith('/v1'):
            base_url = base_url + '/v1'
        llm = LLM(
            model=f'openai/{model_client.model_id}',
            api_key=model_client.api_key,
            base_url=base_url,
            usage_id='reward-bench-solution-generator',
        )
        agent = Agent(llm=llm, tools=tools)

        # OpenHands SDK requires a workspace dir; agent uses it as
        # scratch. We do NOT read submission.py back — the body
        # comes from the last agent message.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            conv = Conversation(
                agent=agent,
                workspace=str(td),
                max_iteration_per_run=_DEFAULT_MAX_ITER,
            )
            conv.send_message(prompt)
            conv.run()

            final_text = _last_agent_message_text(conv)
            return extract_fenced_python(final_text)

    return _runner


def _last_agent_message_text(conv) -> str:
    """Scan conv.state.events in reverse for the last
    MessageEvent with source == 'agent'; concat its text content."""
    from openhands.sdk.event import MessageEvent

    for event in reversed(list(conv.state.events)):
        if not isinstance(event, MessageEvent):
            continue
        if getattr(event, 'source', None) != 'agent':
            continue
        msg = event.llm_message
        parts = []
        for c in getattr(msg, 'content', []) or []:
            text = getattr(c, 'text', None)
            if text:
                parts.append(text)
        return '\n'.join(parts)
    return ''
