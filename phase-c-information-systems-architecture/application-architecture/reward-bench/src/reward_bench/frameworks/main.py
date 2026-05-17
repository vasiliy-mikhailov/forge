"""reward-bench composition root.

Wires the model registry, the tier1 inference container, the agent
loop, the harness, the GameBoard adapter, the score_submission use
case, and the LlmCondenser into a single end-to-end run that emits
an AttemptResult."""
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


REPO = Path(__file__).resolve().parents[3]
ENV_DIR = REPO / 'tasks' / '2048'
TASKS_DIR = REPO / 'tasks'

# Condenser trigger sized for the 128K context budget: ~80% of the
# effective input budget (max_model_len 131072 minus reserved output 32768).
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
    """Empty AttemptResult emitted when the submission is malformed."""
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
    """Callable that posts older turns to the bench vLLM endpoint and
    returns the resulting summary string."""
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
    """Construct an LlmCondenser for the bench target — same model
    serves both bench-target inference and condensing."""
    summarise = _build_summarise(base_url, api_key, target.served_name)
    return LlmCondenser(summarise=summarise, model_id=target.id)


def _build_ask(base_url: str, api_key: str, served_name: str):
    """Bind a one-shot LLM completion against the bench endpoint for
    the supervisor's plateau judgement."""
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
    """Same-model supervisor."""
    ask = _build_ask(base_url, api_key, target.served_name)
    return LlmSupervisor(ask=ask, model_id=target.id)



def _default_canonical_scorer():
    """Module-level factory for the default canonical scorer.
    Production returns DockerCanonicalScorer; tests monkeypatch this
    to return FakeCanonicalScorer."""
    from src.tier1.adapters.docker_canonical_scorer import DockerCanonicalScorer
    return DockerCanonicalScorer(env_path=ENV_DIR / 'env.py')


def main(
    model_id: str = 'qwen3.6-27b-awq',
    seeds: Iterable[int] = range(1000, 1020),
    config: BenchConfig = BenchConfig(),
    canonical_scorer=None,
) -> AttemptResult:
    """Run the bench end-to-end and emit an AttemptResult."""
    target = _pick_model(model_id)
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
    # Align dev's per-seed share with canonical's.
    _seeds = tuple(seeds)
    if config.hard_wall_sec > 0 and len(_seeds) > 0:
        _dev_hard_wall_sec = (
            config.hard_wall_sec * 5 / len(_seeds)
        )
    else:
        _dev_hard_wall_sec = None
    _run_loop_result = run_loop(
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
        finish_floor=config.finish_floor,
        model_id=target.served_name,
        smoke_early_stop=config.smoke_early_stop,
        dev_hard_wall_sec=_dev_hard_wall_sec,
    )

    submission_path = workspace / 'submission.py'
    try:
        module = load_submission(submission_path)
    except FileNotFoundError:
        return _sentinel_attempt_result(f'no submission at {submission_path}')
    except SyntaxError as e:
        return _sentinel_attempt_result(f'submission has SyntaxError: {e}')
    try:
        _source = submission_path.read_text()
    except Exception:
        _source = None
    violations = validate_submission_protocol(module, source=_source)
    if violations:
        return _sentinel_attempt_result(
            f'submission protocol violation: {violations[0]}',
            protocol_invalid=True,
        )
    SolverCls = module.Solver

    # Smoke-mode canonical-skip: when smoke_early_stop fired with
    # positive dev_mean, canonical scoring is pure overhead.
    _best_dev_mean = (_run_loop_result or {}).get('best_dev_mean')
    if config.smoke_early_stop and _best_dev_mean is not None and _best_dev_mean > 0:
        print(f'[bench] smoke-mode canonical-skip: best_dev_mean='
              f'{_best_dev_mean}')
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=0, aggregate_walltime_sec=0.0,
            best_dev_mean=_best_dev_mean,
        )

    if canonical_scorer is None:
        canonical_scorer = _default_canonical_scorer()
    reports_dir = workspace / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)
    result = canonical_scorer.score(
        submission_path, seeds,
        hard_wall_sec=config.hard_wall_sec,
        reports_root=reports_dir,
    )
    import dataclasses as _dc
    result = _dc.replace(result, best_dev_mean=(_run_loop_result or {}).get('best_dev_mean'))

    print(f'[bench] mean_score={result.mean_score:.1f} '
          f'median={result.median_score:.1f} '
          f'max_tile={result.max_max_tile} '
          f'n_games={result.n_games} '
          f'walltime_sec={result.aggregate_walltime_sec:.1f}')
    return result
