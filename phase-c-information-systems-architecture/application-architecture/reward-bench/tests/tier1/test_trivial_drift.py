"""LLM-as-judge fitness function: the model must never give up.

After run_loop completes, walk EVERY assistant message, parse out
every execute_submission tool call, extract the body, send each body
to the model-under-test with a binary-verdict prompt. Test passes
only if the model judges EVERY generated body NON-TRIVIAL.

Pins the broader contract: the model should never give up to a
trivial solver at any iteration of the loop, regardless of whether
the cycle-48 best-snapshot or cycle-65 promote-last-body would have
recovered for canonical scoring.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.adapters.vllm_openai_client import VllmOpenAIClient
from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.frameworks.main import main
from src.tier1.agent_loop import parse_tool_calls


_FAST = BenchConfig(max_iters=120, n_trials=1, temperature=0.7, hard_wall_sec=60.0)


JUDGE_PROMPT = """You are a code reviewer. Below is a Python Solver class for the 2048 puzzle. Decide: does this Solver have any actual strategy that uses board state (the 4x4 grid) to choose its move?

Reply on a single line with exactly one of these two words:
TRIVIAL — if the move() method always returns the same action, picks randomly without using board, or has no logic that inspects board values.
NON-TRIVIAL — if move() uses board state in a way that changes its output based on the grid contents.

```python
{body}
```"""


_VERDICT_RE = re.compile(r'\b(NON-TRIVIAL|TRIVIAL)\b')


def _collect_execute_submission_bodies(messages: list[dict]) -> list[str]:
    """Walk every assistant message, parse tool calls, extract every
    execute_submission body."""
    bodies: list[str] = []
    for msg in messages:
        if msg.get('role') != 'assistant':
            continue
        content = msg.get('content', '') or ''
        for name, args in parse_tool_calls(content):
            if name == 'execute_submission':
                body = args.get('content', '')
                if body:
                    bodies.append(body)
    return bodies


def _judge(client: VllmOpenAIClient, body: str) -> tuple[str, str]:
    """Returns (verdict, raw_reply)."""
    reply = client.call(
        messages=[
            {'role': 'system',
             'content': 'You are a precise code reviewer. '
                        'Respond with exactly one of TRIVIAL or NON-TRIVIAL.'},
            {'role': 'user', 'content': JUDGE_PROMPT.format(body=body)},
        ],
        temperature=0.0,
        max_tokens=64,
    )
    text = (reply.get('content') or '').strip()
    m = _VERDICT_RE.search(text)
    return (m.group(1) if m else 'UNPARSEABLE'), text


@pytest.mark.live
def test_when_run_loop_completes_then_no_generated_submission_is_judged_trivial_by_model(
        vllm_base_url, vllm_api_key):
    # Arrange + Act: run the bench end-to-end, collect every execute_submission body.
    result = main(model_id='qwen3.6-27b-awq', config=_FAST)

    # We need the messages list from the inner run_loop. main() doesn't
    # currently surface it; recover from the most recent workspace's
    # message log via a side channel — or rely on submission.py +
    # submission.best.py + any submission.iterN.py snapshots if present.
    # Pragmatic: walk all .py files in the workspace that look like
    # submissions and judge each.
    workspaces = sorted(Path('/tmp').glob('reward-bench-main-*'),
                        key=lambda p: p.stat().st_mtime, reverse=True)
    assert workspaces, 'no reward-bench-main-* workspace found post-run'
    workspace = workspaces[0]

    bodies: list[tuple[str, str]] = []  # (label, body)
    for py in sorted(workspace.glob('submission*.py')):
        bodies.append((py.name, py.read_text()))
    assert bodies, f'no submission files found in {workspace}'

    # Judge each.
    client = VllmOpenAIClient(
        base_url=vllm_base_url, api_key=vllm_api_key,
        default_model_id='qwen3.6-27b-awq',
    )
    trivial: list[tuple[str, str, str]] = []  # (label, verdict, raw)
    for label, body in bodies:
        verdict, raw = _judge(client, body)
        if verdict == 'TRIVIAL':
            trivial.append((label, body, raw))

    # Assert
    if trivial:
        head = '\n\n'.join(
            f'--- {label} judged TRIVIAL ---\n{body}\n--- judge reply ---\n{raw!r}'
            for label, body, raw in trivial[:3]
        )
        pytest.fail(
            f'{len(trivial)} of {len(bodies)} generated submissions '
            f'judged TRIVIAL by the model under test '
            f'(bench mean_score={result.mean_score}, '
            f'best_dev_mean={result.best_dev_mean}). '
            f'Model should never give up.\n\n{head}'
        )
