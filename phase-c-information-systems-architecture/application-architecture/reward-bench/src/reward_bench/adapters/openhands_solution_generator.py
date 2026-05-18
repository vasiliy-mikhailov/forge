"""§4 OpenHands-backed SolutionGenerator adapter.

Per SOLUTION-ARCHITECTURE.md §4: the OpenHands runtime runs
inside an ephemeral docker container per generate() call. The
host enforces `snapshot.time_remaining_sec` as a wallclock
deadline via `timeout N docker run ...` (kernel SIGTERM).

The prompt is piped in on stdin; the agent's last assistant
message text comes back on stdout; `extract_fenced_python` on
the host lifts the body out.

No threading.Timer / conv.pause() races, no in-process SDK
state to interrupt — the container dies, the host reads
whatever stdout got flushed.

Wiring:

- Tests inject `_openhands_runner` directly with signature
  `(prompt, deadline_sec) -> body` — fully bypasses docker.
- Production binding takes `model_client`; the default factory
  `make_default_openhands_runner(model_client)` returns a
  closure that shells to docker.
"""
from __future__ import annotations

from typing import Callable


# Default per-call wallclock when snapshot.time_remaining_sec
# is 0 (placeholder). 60s matches BenchConfig.hard_wall_sec
# defaults.
_DEFAULT_DEADLINE_SEC = 60.0

# Image tag. Built from Dockerfile.openhands-runner. Increment
# the suffix when the in-container entrypoint changes.
DEFAULT_IMAGE = 'reward-bench-openhands-runner:0.1'


class OpenHandsSolutionGenerator:
    def __init__(
        self,
        model_client=None,
        *,
        _openhands_runner: Callable[[str, float], str] | None = None,
        _make_runner: Callable[[object], Callable[[str, float], str]] | None = None,
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
        deadline = snapshot.time_remaining_sec or _DEFAULT_DEADLINE_SEC
        return self._runner(prompt, deadline)

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
            'IMPORTANT — the harness kills your container at the '
            'time_remaining_sec deadline. Use the dev test harness '
            '2-3 times to validate, then COMMIT.',
            '',
            'Emit your final Solver code as a fenced '
            '```python ... ``` block in your last assistant message. '
            'The harness extracts the last fenced block as the '
            'submission body. The fenced block IS the submission — '
            'put your best version there. Do not append more tool '
            'calls after the final block.',
        ])
        return '\n'.join(lines)


def make_default_openhands_runner(model_client, *, image: str = DEFAULT_IMAGE):
    """Production runner factory. Returned closure invokes
    `timeout N docker run ... <image>` per call, pipes prompt on
    stdin, returns extract_fenced_python(stdout).

    Wallclock is enforced by the host's `timeout` wrapper —
    kernel SIGTERM at deadline. The container dies; we keep
    whatever stdout was flushed."""

    def _runner(prompt: str, deadline_sec: float) -> str:
        import subprocess

        from src.reward_bench.adapters.extract_fenced_python import (
            extract_fenced_python,
        )

        # `timeout` exits 124 on deadline; we accept that — we
        # parse whatever stdout we got. check=False.
        cmd = [
            'timeout', str(int(deadline_sec)),
            'docker', 'run', '--rm', '-i',
            '--network=host',
            '-v', '/var/run/docker.sock:/var/run/docker.sock',
            '-e', f'OPENAI_API_KEY={model_client.api_key}',
            '-e', f'OPENAI_BASE_URL={model_client.base_url}',
            '-e', f'OPENAI_MODEL_ID={model_client.model_id}',
            image,
        ]
        proc = subprocess.run(
            cmd,
            input=prompt.encode(),
            capture_output=True,
            check=False,
        )
        return extract_fenced_python(proc.stdout.decode(errors='replace'))

    return _runner
