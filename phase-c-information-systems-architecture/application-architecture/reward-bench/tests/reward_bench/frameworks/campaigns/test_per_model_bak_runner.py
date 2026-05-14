"""Per-model bench data point. See ADR 0007 for the blessed-runner choice.

See tests-spec/reward_bench/frameworks/campaigns/test_spec_when_per_model_bench_run_then_canonical_artifact_emitted.md.

Run: BENCH_MODEL_ID=qwen3.6-27b-awq pytest -m campaign tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py -v -s

Caller is responsible for swapping vLLM to serve the requested model
BEFORE invoking pytest. We just verify it's served at the expected
served_name."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY


REPO = Path(__file__).resolve().parents[4]
BAK_AGENT = REPO / '_bak' / 'bin' / 'agent_loop.py'
CANONICAL_SEEDS = list(range(1000, 1020))


def _lookup_model(model_id):
    for m in MODEL_REGISTRY:
        if m.id == model_id:
            return m
    raise LookupError(f'model_id {model_id!r} not in MODEL_REGISTRY')


def _vllm_url():
    base = os.environ.get('BENCH_VLLM_URL')
    if base:
        return base
    out = subprocess.run(
        ['docker', 'inspect', 'reward-bench-vllm',
         '--format', '{{(index .NetworkSettings.Networks "proxy-net").IPAddress}}'],
        capture_output=True, text=True,
    )
    ip = out.stdout.strip()
    assert ip, 'reward-bench-vllm container not running or has no proxy-net IP'
    return f'http://{ip}:8000/v1'


def _load_solver(submission_path):
    spec = importlib.util.spec_from_file_location('per_model_bak_sub',
                                                  str(submission_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Solver


def _score_canonical(submission_path):
    """Score the submission on canonical seeds 1000-1019."""
    tasks_2048 = REPO / 'tasks' / '2048'
    sys.path.insert(0, str(tasks_2048))
    try:
        from env import GameBoard
    finally:
        sys.path.pop(0)
    Solver = _load_solver(submission_path)
    scores = []
    max_tiles = []
    for seed in CANONICAL_SEEDS:
        s = Solver()
        b = GameBoard(seed=seed)
        moves = 0
        while not b.is_terminal() and moves < 3000:
            try:
                a = s.move(b.board)
                b.do_action(a)
            except Exception:
                break
            moves += 1
        scores.append(int(b.score))
        max_tiles.append(int(b.max_tile))
    return scores, max_tiles


@pytest.mark.campaign
def test_when_per_model_bench_run_with_bak_runner_then_canonical_artifact_emitted():
    """Run _bak/bin/agent_loop.py for one model, score canonical seeds, emit artifact."""
    model_id = os.environ.get('BENCH_MODEL_ID')
    if not model_id:
        pytest.skip('Set BENCH_MODEL_ID env var to run this test (e.g. qwen3.6-27b-awq)')

    model = _lookup_model(model_id)
    base_url = _vllm_url()
    api_key = os.environ.get('VLLM_API_KEY', 'fixture')

    # Workspace + artifact paths
    ws = REPO / 'experiments' / f'2026-05-14-{model_id}-bak-runner-workspace'
    if ws.exists():
        import shutil
        shutil.rmtree(ws)
    ws.mkdir(parents=True, exist_ok=True)
    trace = ws / 'events.jsonl'
    agent_log = ws / 'agent.log'

    seed = int(os.environ.get('BENCH_SEED', '1'))
    max_iters = int(os.environ.get('BENCH_MAX_ITERS', '200'))
    temperature = float(os.environ.get('BENCH_TEMPERATURE', '0.7'))

    cmd = [
        'python3', '-u', str(BAK_AGENT),
        '--shim', base_url,
        '--api-key', api_key,
        '--model', model.served_name,
        '--workspace', str(ws),
        '--tasks-dir', str(REPO / 'tasks'),
        '--env-dir', str(REPO / 'tasks' / '2048'),
        '--max-iters', str(max_iters),
        '--max-no-improve', '999999',
        '--finish-floor', '0',
        '--max-wall-sec', '7200',
        '--seed', str(seed),
        '--temperature', str(temperature),
        '--context-budget-tokens', '100000',
        '--trace', str(trace),
    ]
    with open(agent_log, 'w') as logf:
        rc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT).returncode

    submission = ws / 'submission.py'
    assert submission.exists(), f'_bak runner did not write a submission (rc={rc}); see {agent_log}'

    scores, max_tiles = _score_canonical(submission)

    payload = {
        'model_id': model.id,
        'served_name': model.served_name,
        'runner': '_bak/bin/agent_loop.py',
        'seed': seed,
        'temperature': temperature,
        'max_iters': max_iters,
        'n_canonical_games': len(CANONICAL_SEEDS),
        'scores': scores,
        'mean': sum(scores) / len(scores),
        'median': sorted(scores)[len(scores) // 2],
        'max': max(scores),
        'min': min(scores),
        'max_max_tile': max(max_tiles),
        'max_tiles': max_tiles,
    }
    artifact = REPO / 'experiments' / f'2026-05-14-{model_id}-bak-runner.json'
    artifact.write_text(json.dumps(payload, indent=2))

    # Shape assertions
    on_disk = json.loads(artifact.read_text())
    for key in ('model_id', 'served_name', 'runner', 'seed', 'temperature',
                'max_iters', 'n_canonical_games', 'scores',
                'mean', 'median', 'max', 'min', 'max_max_tile'):
        assert key in on_disk, f'missing key {key}'
    assert on_disk['runner'] == '_bak/bin/agent_loop.py'
    assert on_disk['n_canonical_games'] == 20
    assert len(on_disk['scores']) == 20
    for k in ('mean', 'median', 'max', 'min', 'max_max_tile'):
        v = on_disk[k]
        assert v == v  # not NaN
        assert v >= 0
