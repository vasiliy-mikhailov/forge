#!/usr/bin/env python3
"""Runner for tests/phase-b-business-architecture/roles/test-devops.md

DO-01..06 mechanical inspection of operations.md plus a P20 + P6
re-use against it (DO-04 / DO-06 import the auditor runner's
finders).

Usage:
    python3 scripts/test-runners/test-devops-runner.py
    python3 scripts/test-runners/test-devops-runner.py --log-scores
"""
from __future__ import annotations
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history  # noqa: E402

FORGE = Path(__file__).resolve().parents[2]
OPS = (FORGE / 'phase-g-implementation-governance' / 'operations.md')


# Load auditor runner module via runpy (importlib trips dataclass
# resolution because the loaded module isn't in sys.modules until
# after exec_module returns; runpy sidesteps this).
import runpy
_AUDITOR_RUNNER = (FORGE / 'scripts' / 'test-runners'
                   / 'test-auditor-runner.py')
_aud_ns = runpy.run_path(str(_AUDITOR_RUNNER), run_name='_aud_loaded')
p6_findings = _aud_ns['p6_findings']
p20_findings = _aud_ns['p20_findings']


@dataclass
class Result:
    verdict: str
    detail: str = ''
    score: float | None = None
    score_max: float | None = None
    threshold: float | None = None


def adr0015_verdict(score, score_max, threshold):
    if score < threshold:
        return 'FAIL'
    if score >= 0.8 * score_max:
        return 'PASS'
    return 'PASS-italian-strike'


# ─────────────── DO-01: file exists, non-empty ───────────────

def do_01_ops_log_exists() -> Result:
    if not OPS.exists():
        return Result('FAIL', 'operations.md missing',
                      score=0.0, score_max=2.0, threshold=2.0)
    n = sum(1 for ln in OPS.read_text(encoding='utf-8').splitlines()
            if ln.strip())
    score = float(int(n >= 100)) + 1.0  # C1 always 1 since exists
    return Result(adr0015_verdict(score, 2.0, 2.0),
                  f'{n} non-blank lines',
                  score=score, score_max=2.0, threshold=2.0)


# ─────────────── DO-02: dated entries exist + recent ───────────────

import datetime as _dt


def _ops_log_section(text: str) -> str:
    """Return only the body of the '## Operational log' section
    (where dated entries live), or empty string if absent."""
    m = re.search(r'(?ms)^## Operational log\s*$.+?(?=\n## |\Z)', text)
    return m.group(0) if m else ''


def do_02_ops_log_dated() -> Result:
    if not OPS.exists():
        return Result('SKIP', 'no operations.md',
                      score=0.0, score_max=2.0, threshold=1.0)
    full = OPS.read_text(encoding='utf-8')
    section = _ops_log_section(full)
    if not section:
        return Result('FAIL', '## Operational log section missing',
                      score=0.0, score_max=2.0, threshold=1.0)
    dates = re.findall(r'^[*\-]\s*(\d{4}-\d{2}-\d{2})', section, flags=re.MULTILINE)
    has_dated = bool(dates)
    parsed = []
    for d in dates:
        try:
            parsed.append(_dt.date.fromisoformat(d))
        except Exception:
            pass
    if not parsed:
        return Result('FAIL', 'no parseable dates',
                      score=0.0, score_max=2.0, threshold=1.0)
    latest = max(parsed)
    age_days = (_dt.date.today() - latest).days
    recent = age_days <= 90
    score = float(int(has_dated)) + float(int(recent))
    return Result(adr0015_verdict(score, 2.0, 1.0),
                  f'{len(parsed)} dates; latest={latest} (age {age_days}d)',
                  score=score, score_max=2.0, threshold=1.0)


# ─────────────── DO-03: governing-keyword paragraphs cite ADR/R-NN ───────────────

GOVERNING_KW = re.compile(r'(?i)\b(deploy|restart|rebuild|power-cap|gpu|key|ssh)\b')
ADR_OR_RNN = re.compile(r'(?i)(?:ADR\s*\d+|R-[A-Z]-\S+)')


def do_03_ops_cites_adr() -> Result:
    if not OPS.exists():
        return Result('SKIP', 'no operations.md',
                      score=0.0, score_max=2.0, threshold=1.0)
    full = OPS.read_text(encoding='utf-8')
    section = _ops_log_section(full)
    if not section:
        return Result('FAIL', '## Operational log section missing',
                      score=0.0, score_max=2.0, threshold=1.0)
    paragraphs = re.split(r'\n\s*\n', section)
    governing = [p for p in paragraphs if GOVERNING_KW.search(p)]
    if not governing:
        return Result('PASS', 'no governing-keyword paragraphs (vacuous)',
                      score=2.0, score_max=2.0, threshold=1.0)
    cited = [p for p in governing if ADR_OR_RNN.search(p)]
    rate = len(cited) / len(governing)
    has_adr_paragraph = any(re.search(r'(?i)ADR\s*\d+', p) for p in cited)
    score = float(int(rate >= 0.8)) + float(int(has_adr_paragraph))
    return Result(adr0015_verdict(score, 2.0, 1.0),
                  f'{len(cited)}/{len(governing)} paragraphs cite '
                  f'(rate={rate:.2f}); has_adr={has_adr_paragraph}',
                  score=score, score_max=2.0, threshold=1.0)


# ─────────────── DO-04: ArchiMate vocabulary discipline ───────────────

def do_04_archimate_clean() -> Result:
    if not OPS.exists():
        return Result('SKIP', 'no operations.md',
                      score=0.0, score_max=1.0, threshold=1.0)
    findings = p6_findings(OPS.read_text(encoding='utf-8'))
    score = 0.0 if findings else 1.0
    detail = ('clean' if not findings
              else f'P6 hits: {[(l, m) for l, m in findings[:3]]}')
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  detail, score=score, score_max=1.0, threshold=1.0)


# ─────────────── DO-05: separation of duties ───────────────

def do_05_separation_of_duties() -> Result:
    log = subprocess.run(
        ['git', '-C', str(FORGE), 'log', '--format=%H%x09%B%x1e', '-100'],
        capture_output=True, text=True).stdout.split('\x1e')
    devops_commits = []
    for entry in log:
        entry = entry.strip()
        if not entry:
            continue
        sha, body = entry.split('\t', 1)
        if re.search(r'(?im)^(devops|ops):', body):
            devops_commits.append(sha)
    if not devops_commits:
        return Result('PASS', 'no devops:-prefixed commits (vacuous)',
                      score=1.0, score_max=1.0, threshold=1.0)
    bad = []
    for sha in devops_commits:
        files = subprocess.run(
            ['git', '-C', str(FORGE), 'diff-tree', '--no-commit-id',
             '--name-only', '-r', sha], capture_output=True, text=True).stdout
        for f in files.splitlines():
            if (f.startswith('phase-c-information-systems-architecture/'
                             'application-architecture/')
                    and f.endswith('.py')):
                bad.append((sha[:8], f))
    score = 0.0 if bad else 1.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'{len(devops_commits)} devops commits; bad={bad[:3]}',
                  score=score, score_max=1.0, threshold=1.0)


# ─────────────── DO-06: P20 token-density ───────────────

def do_06_p20_token_density() -> Result:
    if not OPS.exists():
        return Result('SKIP', 'no operations.md',
                      score=0.0, score_max=2.0, threshold=1.0)
    findings = p20_findings(OPS.read_text(encoding='utf-8'))
    n = len(findings)
    score = float(int(n <= 2)) + float(int(n == 0))
    return Result(adr0015_verdict(score, 2.0, 1.0),
                  f'{n} P20 hits',
                  score=score, score_max=2.0, threshold=1.0)


REGISTRY = {
    'DO-01': do_01_ops_log_exists,
    'DO-02': do_02_ops_log_dated,
    'DO-03': do_03_ops_cites_adr,
    'DO-04': do_04_archimate_clean,
    'DO-05': do_05_separation_of_duties,
    'DO-06': do_06_p20_token_density,
}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    log_scores = '--log-scores' in sys.argv[1:]
    pat = args[0] if args else '*'
    selected = [k for k in REGISTRY if fnmatch(k, pat)]
    if not selected:
        print(f'no tests match pattern {pat!r}')
        return 1

    counts = {'PASS': 0, 'FAIL': 0, 'SKIP': 0, 'PASS-italian-strike': 0}
    rows = []
    for tid in selected:
        r = REGISTRY[tid]()
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
        score_str = (f' [{r.score}/{r.score_max}]'
                     if r.score is not None else '')
        print(f'  {tid:<6} {r.verdict:<19}{score_str}  {r.detail}'.rstrip())
        rows.append((tid, r.verdict, r.score, r.score_max, r.threshold,
                     r.detail))

    print()
    print(f'  total: PASS={counts["PASS"]}  '
          f'PASS-italian-strike={counts.get("PASS-italian-strike", 0)}  '
          f'FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')
    if log_scores:
        path = _score_history.append_scores('test-devops-runner', rows)
        print(f'  logged {len(rows)} rows -> {path.relative_to(FORGE)}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
