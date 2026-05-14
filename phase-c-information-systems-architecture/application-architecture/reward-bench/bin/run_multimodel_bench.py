#!/usr/bin/env python3
"""Cycle 43: orchestrator for multi-model bench.

Iterates a curated MODEL_REGISTRY subset, calling ensure_serving_model
to swap vLLM, then `pytest -m campaign test_per_model_bak_runner.py`
to produce one artifact per model.

This is NOT a pytest test — it's a runner that drives the cycle-41
test once per model. The artifacts themselves (the leaderboard data
points) still come from the test, per cats.md.

Usage:
    python3 bin/run_multimodel_bench.py [model_id ...]

If no model_ids given, runs the default curated list. Each entry:
ensure_serving_model -> wait for container ready -> pytest the per-model
campaign test. Failures are logged but don't abort the loop.

Locally-cached HF paths (from /mnt/steam/forge/shared/models/hub):
    qwen3.6-27b-awq               cyankiwi/Qwen3.6-27B-AWQ-INT4
    qwen3.5-27b-nvfp4             kaitchup/Qwen3.5-27B-NVFP4
    devstral-small-2-24b          Firworks/Devstral-Small-2-24B-Instruct-2512-nvfp4
    gemma-4-31b-nvfp4             nvidia/Gemma-4-31B-IT-NVFP4
    llama-3.1-8b-nvfp4            nvidia/Llama-3.1-8B-Instruct-NVFP4
    nemotron-super-49b-v1.5-nvfp4 nvidia/Llama-3_3-Nemotron-Super-49B-v1_5-NVFP4
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY
from src.tier1.inference import ensure_serving_model


DEFAULT_MODELS = [
    'qwen3.6-27b-awq',          # already baselined cycle 40-41
    'qwen3.5-27b-nvfp4',
    'devstral-small-2-24b',
    'gemma-4-31b-nvfp4',
    'llama-3.1-8b-nvfp4',        # tiny — quick sanity model
    'nemotron-super-49b-v1.5-nvfp4',  # bigger, tighter VRAM
]


def main(argv):
    targets = argv or DEFAULT_MODELS
    by_id = {m.id: m for m in MODEL_REGISTRY}
    for mid in targets:
        if mid not in by_id:
            print(f'[orchestrator] skipping {mid}: not in MODEL_REGISTRY')
            continue
        target = by_id[mid]
        print(f'[orchestrator] === {mid} ===')
        try:
            url = ensure_serving_model(target)
            print(f'[orchestrator]   vLLM ready at {url}')
        except Exception as e:
            print(f'[orchestrator]   ensure_serving_model failed: {e}')
            continue

        cmd = [
            'python3', '-m', 'pytest', '-m', 'campaign',
            'tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py',
            '-v', '-s', '--tb=short',
        ]
        env = os.environ.copy()
        env['BENCH_MODEL_ID'] = mid
        env.setdefault('VLLM_API_KEY',
                       'sk-ef2926520a83b7f6efac7f4dc5b049842b4b2baebfdc18b69b76220f29fdf272')
        log_path = REPO / 'experiments' / f'2026-05-14-{mid}-orchestrator.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as logf:
            rc = subprocess.run(cmd, env=env, cwd=str(REPO),
                                stdout=logf, stderr=subprocess.STDOUT).returncode
        print(f'[orchestrator]   pytest rc={rc}, log={log_path}')


if __name__ == '__main__':
    main(sys.argv[1:])
