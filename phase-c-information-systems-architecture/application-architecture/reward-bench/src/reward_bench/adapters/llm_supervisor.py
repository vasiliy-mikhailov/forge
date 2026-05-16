"""LlmSupervisor: SupervisorPort impl that delegates plateau judgment
to the bench LLM under test.

See src-spec/reward_bench/adapters/llm_supervisor/.

Per ADR 0001 (same model as bench) + ADR 0005 (LLM self-judges
plateau), the wiring layer (frameworks/main) supplies an `ask`
callable backed by the bench-model vLLM endpoint.

Flow: render sweep -> ask -> parse -> SupervisorDecision. Any
failure on the parse path degrades to a CONSERVATIVE fallback
(plateau=False, stop_recommended=False) — the agent loop never
sees an exception from the supervisor, and a flaky supervisor
never causes an accidental early stop."""
import json
import re
from typing import Callable, Tuple

from src.reward_bench.entities.supervisor_decision import SupervisorDecision
from src.ports.supervisor import Sample


_JSON_OBJECT_RE = re.compile(r'\{.*\}', re.DOTALL)


_PROMPT_TEMPLATE = """You are watching your own bench run for the 2048 task.
Below is a sweep of recent iterations — each row is
(iter_no, mean_score, max_tile, walltime_sec).

Sweep:
{sweep_block}

Question: Given this sweep, are you on a plateau (no meaningful
improvement) or still making progress? Reply with ONE JSON object
on a single line:

  {{"plateau": <bool>, "reasoning": <string>, "stop_recommended": <bool>}}

CONSERVATIVE BIAS: only set stop_recommended=true if you are
confident that further iterations would not improve the score.
"""


def _render_sweep(sweep: Tuple[Sample, ...]) -> str:
    return '\n'.join(
        f'({iter_no}, {mean_score:.1f}, {max_tile}, {walltime_sec:.2f})'
        for iter_no, mean_score, max_tile, walltime_sec in sweep
    )


def _parse_reply(reply: str) -> SupervisorDecision:
    """Locate the first JSON object in `reply` and coerce its three
    fields. Raises ValueError on any malformation — callers wrap."""
    match = _JSON_OBJECT_RE.search(reply)
    if match is None:
        raise ValueError('no JSON object in reply')
    obj = json.loads(match.group(0))
    if not isinstance(obj, dict):
        raise ValueError('JSON root is not an object')
    if 'plateau' not in obj or 'stop_recommended' not in obj:
        raise ValueError('missing plateau or stop_recommended key')
    return SupervisorDecision(
        plateau=bool(obj['plateau']),
        stop_recommended=bool(obj['stop_recommended']),
        reasoning=str(obj.get('reasoning', '')),
    )


class LlmSupervisor:
    """SupervisorPort backed by an LLM `ask` callable."""

    def __init__(self, ask: Callable[[str], str], model_id: str):
        self._ask = ask
        self.model_id = model_id

    def judge(self, sweep: Tuple[Sample, ...]) -> SupervisorDecision:
        prompt = _PROMPT_TEMPLATE.format(sweep_block=_render_sweep(sweep))
        try:
            reply = self._ask(prompt)
            return _parse_reply(reply)
        except Exception as e:
            return SupervisorDecision(
                plateau=False,
                stop_recommended=False,
                reasoning=f'supervisor parse-error: {type(e).__name__}: {e}',
            )
