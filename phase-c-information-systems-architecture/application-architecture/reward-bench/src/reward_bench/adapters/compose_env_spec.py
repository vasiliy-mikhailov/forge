"""§4 env_spec composer — task + dev-harness + budget.

Per SOLUTION-ARCHITECTURE.md §4 binding interface: env_spec is a
self-contained prompt built once at startup. Three sections:

1. Task        — the SKILL contract text (FSM Solver, move(board)).
2. Dev harness — an inline shell command the agent runs via bash
                  to score a candidate against dev seeds. The
                  Solver source flows via heredoc → docker stdin →
                  cat > /workspace/submission.py *inside* the
                  container (ephemeral). No host filesystem writes
                  per §5.
3. Budget      — per-dev-test wallclock hint.

Pure string composition. No IO. The env_factory reads
SKILL_tier1.md once, passes its text here with the host path of
the env.py read-only mount.
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
        f'Run this to score a candidate Solver against {dev_games} dev-seed\n'
        f'games (per-call timeout {dev_timeout_sec}s, isolated docker\n'
        'container). The Solver source goes inline as a heredoc — no host\n'
        'files involved:\n\n'
        f'  timeout {dev_timeout_sec} docker run --rm -i \\\n'
        '    --network=none --memory=2g --cpus=2 --pids-limit=256 \\\n'
        f'    -v {env_py_path}:/env/env_2048.py:ro \\\n'
        f'    -e REWARD_BENCH_NUM_GAMES={dev_games} \\\n'
        f'    -e REWARD_BENCH_SEED_BASE={dev_seed_base} \\\n'
        '    -e REWARD_BENCH_STAGNATION_SEC=15 \\\n'
        f'    --entrypoint bash {tier1_image} \\\n'
        "    -c 'cat > /workspace/submission.py && "
        "exec python3 /env/runner_canonical.py' "
        "<<'SOLVER_END'\n"
        '  # your Solver code here, inline\n'
        '  SOLVER_END\n\n'
        'It writes the heredoc body to /workspace/submission.py *inside* the\n'
        'container (ephemeral; nothing crosses to the host), runs the\n'
        'canonical evaluator, prints aggregate JSON to stdout. Iterate based\n'
        'on observed scores; the canonical harness on held-out seeds runs\n'
        'separately on the final submission.\n\n'
        '# Budget\n\n'
        f'Per dev test: ~{dev_timeout_sec} seconds. The orchestrator\'s '
        'per-iter budget appears in the # Budget section that follows.\n'
    )
