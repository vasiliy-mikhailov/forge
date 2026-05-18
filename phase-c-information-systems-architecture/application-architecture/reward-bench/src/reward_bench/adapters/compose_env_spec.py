"""§4 env_spec composer — task + dev-harness + budget.

Per SOLUTION-ARCHITECTURE.md §4 binding interface: env_spec is a
self-contained prompt built once at startup. Three sections:

1. Task        — the SKILL contract text (FSM Solver, move(board)).
2. Dev harness — an inline shell command the agent runs via bash
                  to score a candidate against dev seeds.
3. Budget      — per-dev-test wallclock hint.

Pure string composition. No IO. The env_factory reads SKILL_tier1.md
once, passes its text here with the host paths for the env.py mount.
"""
from __future__ import annotations

from pathlib import Path


def compose_env_spec(
    skill_md_text: str,
    env_py_path: Path,
    *,
    tier1_image: str = 'reward-bench-tier1:0.4',
    dev_games: int = 5,
    dev_seed_base: int = 2000,
    dev_timeout_sec: int = 60,
) -> str:
    """Build the §4 self-contained env_spec prompt."""
    return (
        '# Task\n\n'
        f'{skill_md_text.rstrip()}\n\n'
        '# Dev test harness\n\n'
        'Write your candidate Solver to a scratch file (e.g. /tmp/sub.py).\n'
        f'Then run this command to score it against {dev_games} dev-seed games\n'
        f'(per-call timeout {dev_timeout_sec}s, isolated docker container):\n\n'
        f'  timeout {dev_timeout_sec} docker run --rm \\\n'
        '    --network=none --memory=2g --cpus=2 --pids-limit=256 \\\n'
        '    -v /tmp/sub.py:/workspace/submission.py:ro \\\n'
        f'    -v {env_py_path}:/env/env_2048.py:ro \\\n'
        f'    -e REWARD_BENCH_NUM_GAMES={dev_games} \\\n'
        f'    -e REWARD_BENCH_SEED_BASE={dev_seed_base} \\\n'
        '    -e REWARD_BENCH_STAGNATION_SEC=15 \\\n'
        f'    {tier1_image}\n\n'
        'It prints game scores + aggregate JSON to stdout. Iterate based on\n'
        'observed scores; the harness on canonical held-out seeds runs later.\n\n'
        '# Budget\n\n'
        f'Per dev test: ~{dev_timeout_sec} seconds. The orchestrator\'s '
        'per-iter budget appears in the # Budget section that follows.\n'
    )
