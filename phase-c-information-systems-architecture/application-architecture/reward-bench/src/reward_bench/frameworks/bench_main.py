"""§7 bench main — production binding of bench() to MODEL_REGISTRY.

Replaces the procedural main.py with a thin composition that wires
the §2 three-role chain (OrchestrateSubagentPerIter +
OpenHandsSolutionGenerator + DockerCanonicalScorer as Runner) per
SOLUTION-ARCHITECTURE.md §4 (OpenHands committed). Includes a CLI
block for direct invocation.

The default env loads the 2048 task spec (SKILL_tier1.md) once at
construction so the orchestrator can stamp it into every per-iter
snapshot without re-reading from disk.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable

from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.entities.env import Env
from src.reward_bench.entities.model_target import ModelTarget
from src.reward_bench.use_cases.bench import bench
from src.tier1.entities.submission import Submission


REPO = Path(__file__).resolve().parents[4]
TASKS_DIR = REPO / 'tasks'
TASK_SPEC_PATH = TASKS_DIR / '2048' / 'SKILL_tier1.md'


def _default_env_factory(target: ModelTarget) -> Env:
    import os

    from src.adapters.vllm_openai_client import VllmOpenAIClient
    from src.tier1.adapters.docker_canonical_scorer import (
        DockerCanonicalScorer,
    )
    from src.tier1.inference import ensure_serving_model

    base_url = ensure_serving_model(target)
    api_key = os.environ['VLLM_API_KEY']
    return Env(
        tasks_dir=TASKS_DIR,
        canonical_scorer=DockerCanonicalScorer(),
        model_client=VllmOpenAIClient(
            base_url=base_url, api_key=api_key,
            default_model_id=target.served_name,
        ),
        env_spec=TASK_SPEC_PATH.read_text(),
    )


def _default_orchestrator_factory(env: Env):
    """§2 three-role default: OrchestrateSubagentPerIter wrapping
    OpenHandsSolutionGenerator (model_client from env) and
    env.canonical_scorer as Runner."""
    from src.reward_bench.adapters.openhands_solution_generator import (
        OpenHandsSolutionGenerator,
    )
    from src.reward_bench.adapters.orchestrate_subagent_per_iter import (
        OrchestrateSubagentPerIter,
    )
    return OrchestrateSubagentPerIter(
        solution_generator=OpenHandsSolutionGenerator(
            model_client=env.model_client,
        ),
        runner=env.canonical_scorer,
    )


def bench_main(
    target: ModelTarget,
    cfg: BenchConfig,
    *,
    env_factory: Callable[[ModelTarget], Env] | None = None,
    orchestrator_factory: Callable[[Env], object] | None = None,
) -> Submission:
    env_factory = env_factory or _default_env_factory
    orchestrator_factory = orchestrator_factory or _default_orchestrator_factory

    env = env_factory(target)
    orchestrator = orchestrator_factory(env)
    return bench(orchestrator, env, cfg)


def _cli() -> int:
    from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY

    ap = argparse.ArgumentParser()
    ap.add_argument('--model-id', default='qwen3.6-27b-awq')
    ap.add_argument('--max-iters', type=int, default=100)
    ap.add_argument('--hard-wall-sec', type=float, default=60.0)
    ap.add_argument('--no-early-stop', action='store_true', default=False)
    args = ap.parse_args()

    target = next(t for t in MODEL_REGISTRY if t.id == args.model_id)
    cfg = BenchConfig(
        max_iters=args.max_iters,
        hard_wall_sec=args.hard_wall_sec,
        smoke_early_stop=not args.no_early_stop,
    )

    t0 = time.monotonic()
    sub = bench_main(target, cfg)
    elapsed = time.monotonic() - t0

    result = {
        'model_id': args.model_id,
        'wallclock_sec': round(elapsed, 2),
        'submission_score': sub.score,
        'submission_walltime_sec': sub.walltime_sec,
        'submission_body_len': len(sub.body),
        'body_has_class_solver': 'class Solver' in sub.body,
        'body_has_from_transitions': 'from transitions' in sub.body,
        'config': {
            'max_iters': cfg.max_iters,
            'hard_wall_sec': cfg.hard_wall_sec,
            'smoke_early_stop': cfg.smoke_early_stop,
        },
    }
    print(json.dumps(result, indent=2))
    print('--- submission body (first 600 chars) ---')
    print(sub.body[:600])
    if len(sub.body) > 600:
        print(f'... ({len(sub.body) - 600} more chars)')
    return 0


if __name__ == '__main__':
    sys.exit(_cli())
