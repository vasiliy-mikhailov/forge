"""reward-bench composition root.

See src-spec/reward_bench/frameworks/main/src_spec_main.md.

Wires the model registry, the tier1 inference container, the agent
loop, the harness, the GameBoard adapter, and the score_submission
use case into a single end-to-end run that emits an AttemptResult.

Robust to malformed model output: when the agent loop produces a
submission without a `Solver` class (or no submission at all), main
emits a sentinel AttemptResult(n_games=0, games=(), mean_score=0.0)
instead of crashing."""
import os
import tempfile
from pathlib import Path
from typing import Iterable

from src.reward_bench.entities.model_target import ModelTarget
from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY
from src.tier1.adapters.game_board_2048 import GameBoard2048Adapter
from src.tier1.agent_loop import run_loop
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.harness import load_submission
from src.tier1.inference import ensure_serving
from src.tier1.use_cases.score_submission import score_submission


REPO = Path(__file__).resolve().parents[4]
ENV_DIR = REPO / 'tasks' / '2048'
TASKS_DIR = REPO / 'tasks'


def _pick_model(model_id: str) -> ModelTarget:
    for t in MODEL_REGISTRY:
        if t.id == model_id:
            return t
    raise KeyError(
        f'model {model_id!r} not in MODEL_REGISTRY '
        f'(known: {[t.id for t in MODEL_REGISTRY]})'
    )


def _sentinel_attempt_result(reason: str) -> AttemptResult:
    """Empty AttemptResult emitted when the submission is malformed.
    n_games=0, games=(), mean_score=0.0 mark the shape-error case."""
    print(f'[bench] submission shape error: {reason}')
    return AttemptResult(
        mean_score=0.0,
        median_score=0.0,
        std_score=0.0,
        max_max_tile=0,
        n_games=0,
        aggregate_walltime_sec=0.0,
        games=(),
    )


def main(
    model_id: str = 'qwen3.6-27b-awq',
    seeds: Iterable[int] = range(1000, 1020),
    max_iters: int = 30,
) -> AttemptResult:
    """Run the bench end-to-end and emit an AttemptResult."""
    target = _pick_model(model_id)
    base_url = ensure_serving()
    api_key = os.environ['VLLM_API_KEY']

    workspace = Path(tempfile.mkdtemp(prefix='reward-bench-main-'))
    print(f'[bench] model={target.id} workspace={workspace}')

    run_loop(
        workspace=workspace,
        env_dir=ENV_DIR,
        tasks_dir=TASKS_DIR,
        vllm_base_url=base_url,
        vllm_api_key=api_key,
        max_iters=max_iters,
    )

    submission_path = workspace / 'submission.py'
    try:
        module = load_submission(submission_path)
        SolverCls = module.Solver  # may raise AttributeError
    except FileNotFoundError:
        return _sentinel_attempt_result(f'no submission at {submission_path}')
    except AttributeError as e:
        return _sentinel_attempt_result(str(e))

    adapter = GameBoard2048Adapter()
    result = score_submission(SolverCls, seeds, adapter)

    print(f'[bench] mean_score={result.mean_score:.1f} '
          f'median={result.median_score:.1f} '
          f'max_tile={result.max_max_tile} '
          f'n_games={result.n_games} '
          f'walltime_sec={result.aggregate_walltime_sec:.1f}')
    return result
