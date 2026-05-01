"""ADR 0015 dec 5 — score-history logging for agentic-behaviour runners.

Each runner (`test-auditor-runner.py`, `test-wiki-pm-runner.py`,
`test-lab-AGENTS-runner.py`) calls `append_scores(...)` at the end
of `main()` ONLY IF the user passed `--log-scores`. Default: do
not log (keeps interactive dev runs out of git history).

File layout:
    scripts/test-runners/.score-history/
        test-auditor-runner.jsonl
        test-wiki-pm-runner.jsonl
        test-lab-AGENTS-runner.jsonl

Schema (one JSON object per line):
    {
      "ts":         "2026-05-01T17:42:13Z",   # UTC, second precision
      "git_commit": "feff3d6abc",             # short HEAD at log time
      "runner":     "test-auditor-runner",
      "test_id":    "AU-05",
      "verdict":    "PASS",                   # one of PASS, FAIL,
                                              # SKIP, PASS-italian-strike
      "score":      5.0,                      # may be null if case
                                              # has no Reward function
      "score_max":  6.0,                      # null iff score null
      "threshold":  3.0,                      # null iff score null
      "detail":     "score=5.0/6.0; C1=1, …"  # human-readable line
    }

Why JSONL (not CSV): score components can be embedded as nested
objects in future without breaking older readers; one diff per
logged run; cheap to grep / jq.

Reader API:
    latest_per_case(path)   → dict[test_id] -> row (newest)
    previous_per_case(path) → dict[test_id] -> row (second-newest)
    regressions(path)       → list[(test_id, prev_row, curr_row)]
                              for cases whose latest is worse than
                              their previous (verdict regression, or
                              score drop ≥ 10% of score_max).
"""
from __future__ import annotations
import json
import subprocess
import time
from pathlib import Path

HISTORY_DIR = Path(__file__).resolve().parent / '.score-history'

# Verdict ordering: best → worst. A move toward index N from index < N
# is a regression. SKIP is excluded — a SKIP is pending data, not
# a worse outcome than PASS.
VERDICT_ORDER = ['PASS', 'PASS-italian-strike', 'FAIL']


def _git_commit() -> str:
    forge_root = Path(__file__).resolve().parents[2]
    try:
        out = subprocess.run(
            ['git', 'rev-parse', '--short=10', 'HEAD'],
            capture_output=True, text=True, check=True, cwd=forge_root,
        )
        return out.stdout.strip()
    except Exception:
        return 'unknown'


def append_scores(runner_name: str, results) -> Path:
    """Append one JSONL row per result tuple.

    `results` iterable of
        (test_id, verdict, score, score_max, threshold, detail)
    where score / score_max / threshold may be None.
    """
    HISTORY_DIR.mkdir(exist_ok=True)
    path = HISTORY_DIR / f'{runner_name}.jsonl'
    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    commit = _git_commit()
    with path.open('a', encoding='utf-8') as fh:
        for tid, verdict, score, score_max, threshold, detail in results:
            row = {
                'ts': ts,
                'git_commit': commit,
                'runner': runner_name,
                'test_id': tid,
                'verdict': verdict,
                'score': score,
                'score_max': score_max,
                'threshold': threshold,
                'detail': detail,
            }
            fh.write(json.dumps(row, ensure_ascii=False) + '\n')
    return path


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def latest_per_case(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for row in _read_rows(path):
        out[row['test_id']] = row
    return out


def previous_per_case(path: Path) -> dict[str, dict]:
    last: dict[str, dict] = {}
    prev: dict[str, dict] = {}
    for row in _read_rows(path):
        tid = row['test_id']
        if tid in last:
            prev[tid] = last[tid]
        last[tid] = row
    return prev


def regressions(path: Path,
                score_drop_threshold: float = 0.10
                ) -> list[tuple[str, dict, dict]]:
    """Return [(test_id, prev_row, curr_row), ...] for regressions.

    A case is regressing if EITHER:
      - verdict moved later in VERDICT_ORDER (e.g. PASS → FAIL,
        PASS → italian-strike, italian-strike → FAIL), OR
      - score / score_max dropped by ≥ score_drop_threshold (10% by
        default) versus the previous run's score / score_max.
    """
    last = latest_per_case(path)
    prev = previous_per_case(path)
    out: list[tuple[str, dict, dict]] = []
    for tid, curr in last.items():
        if tid not in prev:
            continue
        p = prev[tid]
        verdict_regressed = False
        try:
            verdict_regressed = (
                VERDICT_ORDER.index(curr['verdict']) >
                VERDICT_ORDER.index(p['verdict'])
            )
        except ValueError:
            pass
        score_dropped = False
        if (curr.get('score') is not None and curr.get('score_max')
                and p.get('score') is not None and p.get('score_max')):
            curr_norm = curr['score'] / curr['score_max']
            prev_norm = p['score'] / p['score_max']
            if prev_norm - curr_norm >= score_drop_threshold:
                score_dropped = True
        if verdict_regressed or score_dropped:
            out.append((tid, p, curr))
    return out
