"""reward-bench composition root.

See src-spec/reward_bench/frameworks/main/src_spec_main.md.

Wires the model registry, the tier1 inference container, the agent
loop, the harness, the GameBoard adapter, the score_submission use
case, and the LlmCondenser into a single end-to-end run that emits
an AttemptResult.

Per ADR 0001, the condenser uses the same vLLM endpoint and model
as the bench target. Per ADR 0002, malformed submissions yield a
sentinel AttemptResult. Per ADR 0003, the default BenchConfig
applies 500 iters / T=0.7."""
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Iterable, Tuple

from src.reward_bench.adapters.llm_condenser import LlmCondenser
from src.reward_bench.adapters.llm_supervisor import LlmSupervisor
from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.entities.condenser_config import CondenserConfig
from src.reward_bench.entities.model_target import ModelTarget
from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY
from src.tier1.adapters.game_board_2048 import GameBoard2048Adapter
from src.tier1.agent_loop import run_loop
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.harness import load_submission, validate_submission_protocol
from src.tier1.inference import ensure_serving_model
from src.tier1.use_cases.score_submission import score_submission


REPO = Path(__file__).resolve().parents[4]
ENV_DIR = REPO / 'tasks' / '2048'
TASKS_DIR = REPO / 'tasks'

# Condenser trigger sized for the 128K context budget. With
# max_model_len=131072 and reserved output budget max_tokens=32768, the
# effective input budget is ~98304 tokens. We trigger at ~80% of that so
# the model has room to swing without compacting prematurely. Legacy _bak
# used 40000 (conservative for a smaller secondary GPU); our setup runs
# the same 128K model for both bench and condenser per ADR 0001 so the
# higher trigger is safe.
_CONDENSER_TRIGGER_TOKENS = 80000
_CONDENSER_KEEP_RECENT = 8


def _pick_model(model_id: str) -> ModelTarget:
    for t in MODEL_REGISTRY:
        if t.id == model_id:
            return t
    raise KeyError(
        f'model {model_id!r} not in MODEL_REGISTRY '
        f'(known: {[t.id for t in MODEL_REGISTRY]})'
    )


def _sentinel_attempt_result(reason: str, *, protocol_invalid: bool = False) -> AttemptResult:
    """Empty AttemptResult emitted when the submission is malformed (ADR 0002)."""
    print(f'[bench] submission shape error: {reason}')
    return AttemptResult(
        mean_score=0.0,
        median_score=0.0,
        std_score=0.0,
        max_max_tile=0,
        n_games=0,
        aggregate_walltime_sec=0.0,
        games=(),
        solver_protocol_valid=not protocol_invalid,
    )


def _build_summarise(base_url: str, api_key: str, served_name: str):
    """Construct a callable that posts older turns to the bench vLLM endpoint
    and returns the resulting summary string. Per ADR 0001, served_name is
    the same as the bench target."""
    def summarise(older_turns: Tuple[dict, ...]) -> str:
        prompt = [
            {'role': 'system',
             'content': 'Summarise the following agent-loop turns concisely. '
                        'Preserve key facts about the task, the current '
                        'submission state, dev_runner results, and any errors. '
                        'Be terse — bullet points are fine.'},
            {'role': 'user',
             'content': json.dumps(list(older_turns), ensure_ascii=False)},
        ]
        payload = json.dumps({
            'model': served_name,
            'messages': prompt,
            'max_tokens': 4096,
            'temperature': 0.0,
        }).encode()
        req = urllib.request.Request(
            f'{base_url}/v1/chat/completions',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return data['choices'][0]['message']['content']

    return summarise


def _build_condenser(target: ModelTarget, base_url: str, api_key: str) -> LlmCondenser:
    """Construct an LlmCondenser for the bench target per ADR 0001 — same
    model serves both bench-target inference and condensing."""
    summarise = _build_summarise(base_url, api_key, target.served_name)
    return LlmCondenser(summarise=summarise, model_id=target.id)


def _build_ask(base_url: str, api_key: str, served_name: str):
    """Cycle 35: bind a one-shot LLM completion against the bench endpoint.

    The supervisor uses this to ask the bench model (per ADR 0001) to
    judge plateau from sweep data."""
    def ask(prompt: str) -> str:
        body = json.dumps({
            'model': served_name,
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.0,
            'max_tokens': 512,
        }).encode()
        req = urllib.request.Request(
            f'{base_url}/v1/chat/completions',
            data=body, method='POST',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return data['choices'][0]['message']['content']
    return ask


def _build_supervisor(target: ModelTarget, base_url: str, api_key: str) -> LlmSupervisor:
    """Cycle 35: same-model supervisor per ADR 0001 + ADR 0005."""
    ask = _build_ask(base_url, api_key, target.served_name)
    return LlmSupervisor(ask=ask, model_id=target.id)


def main(
    model_id: str = 'qwen3.6-27b-awq',
    seeds: Iterable[int] = range(1000, 1020),
    config: BenchConfig = BenchConfig(),
) -> AttemptResult:
    """Run the bench end-to-end and emit an AttemptResult.

    `config` defaults to ADR 0003 (500 iters, T=0.7); tests pass a
    smaller config to keep wall time bounded."""
    target = _pick_model(model_id)
    # Cycle 73: pass the picked ModelTarget through so the lab vLLM
    # container is (re)provisioned for THIS model. Before cycle 73,
    # this was the bare cycle-11 ensure_serving() which hardcoded AWQ
    # and silently overrode any earlier ensure_serving_model(target)
    # call — uncovered live during cycle 72's multi-model smoke.
    base_url = ensure_serving_model(target)
    api_key = os.environ['VLLM_API_KEY']

    workspace = Path(tempfile.mkdtemp(prefix='reward-bench-main-'))
    print(f'[bench] model={target.id} workspace={workspace} '
          f'max_iters={config.max_iters} temperature={config.temperature}')

    condenser = _build_condenser(target, base_url, api_key)
    condenser_config = CondenserConfig(
        trigger_tokens=_CONDENSER_TRIGGER_TOKENS,
        keep_recent=_CONDENSER_KEEP_RECENT,
        model_id=target.id,
    )
    def condense(messages):
        return condenser.condense(messages, condenser_config)

    supervisor = _build_supervisor(target, base_url, api_key)
    run_loop(
        workspace=workspace,
        env_dir=ENV_DIR,
        tasks_dir=TASKS_DIR,
        vllm_base_url=base_url,
        vllm_api_key=api_key,
        max_iters=config.max_iters,
        condense=condense,
        temperature=config.temperature,
        supervisor=supervisor,
        supervisor_every_k=config.supervisor_every_k,
        finish_floor=config.finish_floor,  # cycle 50 / hypothesis #2
        model_id=target.served_name,       # cycle 74: don't ask vLLM for AWQ
                                           # when the container serves something
                                           # else; otherwise HTTP 404.
        smoke_early_stop=config.smoke_early_stop,  # cycle 76 / ADR 0009 v2
    )

    submission_path = workspace / 'submission.py'
    try:
        module = load_submission(submission_path)
    except FileNotFoundError:
        return _sentinel_attempt_result(f'no submission at {submission_path}')
    except SyntaxError as e:
        # Model wrote non-Python content (e.g. HTML, pseudocode). Per ADR
        # 0002 sentinel-on-malformed pattern, extended to cover SyntaxError
        # discovered live with temperature=0.7 cycle-22 campaign run.
        return _sentinel_attempt_result(f'submission has SyntaxError: {e}')
    # Cycle 53: explicit submission-protocol validation per
    # tasks/2048/SKILL_tier1.md (class Solver + move(self, board)->W/A/S/D).
    # Replaces the ad-hoc AttributeError sentinel from cycles 28/29 with a
    # named contract check; the violation strings are surfaced into the
    # artifact via the sentinel reason so observability distinguishes
    # protocol violations from runtime crashes.
    violations = validate_submission_protocol(module)
    if violations:
        return _sentinel_attempt_result(
            f'submission protocol violation: {violations[0]}',
            protocol_invalid=True,
        )
    SolverCls = module.Solver

    adapter = GameBoard2048Adapter()
    result = score_submission(SolverCls, seeds, adapter, hard_wall_sec=config.hard_wall_sec)

    print(f'[bench] mean_score={result.mean_score:.1f} '
          f'median={result.median_score:.1f} '
          f'max_tile={result.max_max_tile} '
          f'n_games={result.n_games} '
          f'walltime_sec={result.aggregate_walltime_sec:.1f}')
    return result
