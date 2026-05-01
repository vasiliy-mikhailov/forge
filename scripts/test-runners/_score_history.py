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


def aggregate_per_runner(path: Path) -> dict:
    """ADR 0015 dec 6 — per-runner aggregate score.

    Reads the JSONL, takes the LATEST row per test_id (so re-runs at
    the same case don't double-count), and rolls up:

        score_sum / score_max_sum  →  normalised aggregate (0..1)

    Cases without a Reward function (score=None) are excluded from
    the average — they're binary inspection tests, not graded
    behaviour. Returns:

        {
          'n_cases_total':   int,    # all logged cases
          'n_cases_scored':  int,    # cases with score not None
          'score_sum':       float,  # sum of scores (nullable cases excluded)
          'score_max_sum':   float,  # sum of score_max (same exclusion)
          'score_norm':      float,  # score_sum / score_max_sum, or None
          'band':            str,    # PASS | italian-strike | FAIL | n/a
          'pass_count':      int,    # cases whose latest verdict == PASS
          'italian_strike_count': int,
          'fail_count':      int,
        }

    The band uses the same ADR 0015 verdict ladder applied to the
    aggregate: PASS at score_norm >= 0.8; italian-strike at 0.5..0.8;
    FAIL below 0.5. (The aggregate threshold is itself a separate
    architect call — 0.5 is the conservative default.)
    """
    latest = latest_per_case(path)
    n_total = len(latest)
    if n_total == 0:
        return {
            'n_cases_total': 0, 'n_cases_scored': 0,
            'score_sum': 0.0, 'score_max_sum': 0.0,
            'score_norm': None, 'band': 'n/a',
            'pass_count': 0, 'italian_strike_count': 0, 'fail_count': 0,
        }
    score_sum = 0.0
    score_max_sum = 0.0
    n_scored = 0
    pass_count = italian_strike_count = fail_count = 0
    for row in latest.values():
        if row.get('score') is not None and row.get('score_max'):
            score_sum += row['score']
            score_max_sum += row['score_max']
            n_scored += 1
        v = row.get('verdict')
        if v == 'PASS':
            pass_count += 1
        elif v == 'PASS-italian-strike':
            italian_strike_count += 1
        elif v == 'FAIL':
            fail_count += 1
    if score_max_sum > 0:
        score_norm = score_sum / score_max_sum
        if score_norm >= 0.8:
            band = 'PASS'
        elif score_norm >= 0.5:
            band = 'italian-strike'
        else:
            band = 'FAIL'
    else:
        score_norm = None
        band = 'n/a'
    return {
        'n_cases_total': n_total,
        'n_cases_scored': n_scored,
        'score_sum': round(score_sum, 3),
        'score_max_sum': round(score_max_sum, 3),
        'score_norm': round(score_norm, 3) if score_norm is not None else None,
        'band': band,
        'pass_count': pass_count,
        'italian_strike_count': italian_strike_count,
        'fail_count': fail_count,
    }


def aggregate_per_lab(path: Path) -> dict[str, dict]:
    """ADR 0015 dec 6, lab-AGENTS variant: split LA-XX-NN cases by XX
    so each lab gets its own aggregate (RL/WB/WC/WI). Returns
    {lab_short_code: aggregate_dict}.
    """
    latest = latest_per_case(path)
    by_lab: dict[str, list[dict]] = {}
    for tid, row in latest.items():
        # LA-RL-01 → RL; LA-WB-04 → WB; etc.
        parts = tid.split('-')
        if len(parts) >= 3 and parts[0] == 'LA':
            by_lab.setdefault(parts[1], []).append(row)
    out: dict[str, dict] = {}
    for code, rows in by_lab.items():
        score_sum = sum(r['score'] for r in rows if r.get('score') is not None)
        score_max_sum = sum(r['score_max'] for r in rows if r.get('score_max') is not None)
        if score_max_sum > 0:
            norm = score_sum / score_max_sum
            band = 'PASS' if norm >= 0.8 else ('italian-strike' if norm >= 0.5 else 'FAIL')
        else:
            norm = None; band = 'n/a'
        verdicts = [r.get('verdict') for r in rows]
        out[code] = {
            'n_cases_total': len(rows),
            'n_cases_scored': sum(1 for r in rows if r.get('score') is not None),
            'score_sum': round(score_sum, 3),
            'score_max_sum': round(score_max_sum, 3),
            'score_norm': round(norm, 3) if norm is not None else None,
            'band': band,
            'pass_count': verdicts.count('PASS'),
            'italian_strike_count': verdicts.count('PASS-italian-strike'),
            'fail_count': verdicts.count('FAIL'),
        }
    return out


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
