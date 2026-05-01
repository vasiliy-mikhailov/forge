#!/usr/bin/env python3
"""Runner for tests/phase-b-business-architecture/roles/test-developer.md

Per ADR 0013 the md is the spec; this runner is the derived
mechanism. Cases DV-01..06 are mechanical inspection of git
history, file structure, and runner JSONL logs.

Usage:
    python3 scripts/test-runners/test-developer-runner.py
    python3 scripts/test-runners/test-developer-runner.py --log-scores
    python3 scripts/test-runners/test-developer-runner.py 'DV-0[1-3]'

Exit code: 0 if no FAIL; 1 otherwise.
"""
from __future__ import annotations
import re
import subprocess
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history  # noqa: E402

FORGE = Path(__file__).resolve().parents[2]
LAB_BASE = (FORGE / 'phase-c-information-systems-architecture'
            / 'application-architecture')
LABS = ['rl-2048', 'wiki-bench', 'wiki-compiler', 'wiki-ingest']


@dataclass
class Result:
    verdict: str  # PASS | FAIL | SKIP | PASS-italian-strike
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


def _git(cmd: list[str]) -> str:
    return subprocess.run(['git', '-C', str(FORGE)] + cmd,
                          capture_output=True, text=True).stdout


def _last_lab_touching_commit() -> tuple[str, str, str, list[str]] | None:
    """Walk git log; return (sha, author, message_body, file_list) of
    the most recent commit that touched any lab path."""
    log = _git(['log', '--format=%H%x09%an%x09%B%x1e', '-50']).split('\x1e')
    for entry in log:
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split('\t', 2)
        if len(parts) < 3:
            continue
        sha, author, body = parts
        files = _git(['diff-tree', '--no-commit-id', '--name-only', '-r',
                      sha]).strip().splitlines()
        if any(f.startswith('phase-c-information-systems-architecture/'
                            'application-architecture/') for f in files):
            return sha, author, body, files
    return None


# ─────────────── DV-01: commit cites experiment id / R-NN / ADR ───────────────

DV01_PATTERNS = [
    re.compile(r'\bK\d+\b'),
    re.compile(r'\bG\d+\b'),
    re.compile(r'\bR-[A-Z]-[a-z][\w\-]*'),
    re.compile(r'\bADR\s*\d+\b', re.IGNORECASE),
]


def dv_01_commit_cites_driver() -> Result:
    info = _last_lab_touching_commit()
    if info is None:
        return Result('SKIP', 'no lab-touching commit in last 50',
                      score=0.0, score_max=2.0, threshold=2.0)
    sha, _, body, _ = info
    matches = []
    for pat in DV01_PATTERNS:
        for m in pat.finditer(body):
            matches.append(m.group(0))
    score = 1.0 if matches else 0.0
    # C2 — does the cited id resolve?
    resolved = False
    for m in matches:
        if m.upper().startswith('K') or m.upper().startswith('G'):
            # experiment id → look in phase-f
            if list((FORGE / 'phase-f-migration-planning'
                    / 'experiments').glob(f'{m.upper()}-*.md')):
                resolved = True; break
        elif m.upper().startswith('R-'):
            cat = (FORGE / 'phase-requirements-management' / 'catalog.md').read_text()
            if m in cat:
                resolved = True; break
        elif m.upper().startswith('ADR'):
            n = re.search(r'\d+', m).group(0).zfill(4)
            if list(FORGE.rglob(f'**/{n}-*.md')):
                resolved = True; break
    score += 1.0 if resolved else 0.0
    return Result(adr0015_verdict(score, 2.0, 2.0),
                  f'sha={sha[:8]}; matches={matches[:3]}; resolved={resolved}',
                  score=score, score_max=2.0, threshold=2.0)


# ─────────────── DV-02: TDD discipline (test added with code) ───────────────

def dv_02_tdd_discipline() -> Result:
    info = _last_lab_touching_commit()
    if info is None:
        return Result('SKIP', 'no lab-touching commit',
                      score=0.0, score_max=2.0, threshold=1.0)
    sha, _, body, files = info
    added_source = False
    added_test = False
    for f in files:
        if not f.startswith('phase-c-information-systems-architecture/'):
            continue
        if '/tests/' in f:
            if f.endswith('.py') or f.endswith('.md'):
                added_test = True
        elif f.endswith('.py'):
            added_source = True
    # Allow opt-out via 'closes test:' or 'tests:' in commit body
    opt_out = bool(re.search(r'(?im)^(?:closes\s+test|tests):', body))
    score = float(int(added_source)) + float(int(added_test or opt_out))
    return Result(adr0015_verdict(score, 2.0, 1.0),
                  f'sha={sha[:8]}; src={added_source}, test={added_test}, opt_out={opt_out}',
                  score=score, score_max=2.0, threshold=1.0)


# ─────────────── DV-03: Python collects ───────────────

def dv_03_python_collects() -> Result:
    info = _last_lab_touching_commit()
    if info is None:
        return Result('SKIP', 'no lab-touching commit',
                      score=0.0, score_max=2.0, threshold=2.0)
    sha, _, _, files = info
    py_source = []
    py_test = []
    for f in files:
        if not (f.startswith('phase-c-') and f.endswith('.py')):
            continue
        full = FORGE / f
        if not full.exists():
            continue
        if '/tests/' in f:
            py_test.append(full)
        else:
            py_source.append(full)
    src_ok = True
    for src in py_source:
        # syntax check via py_compile
        r = subprocess.run(['python3', '-m', 'py_compile', str(src)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            src_ok = False
            break
    test_ok = True
    if py_test:
        # pytest --collect-only on each
        r = subprocess.run(['python3', '-m', 'pytest', '--collect-only', '-q']
                           + [str(p) for p in py_test],
                           capture_output=True, text=True)
        if r.returncode != 0:
            test_ok = False
    score = float(int(src_ok)) + float(int(test_ok))
    return Result(adr0015_verdict(score, 2.0, 2.0),
                  f'sha={sha[:8]}; src_ok={src_ok}, test_ok={test_ok} '
                  f'({len(py_source)} src, {len(py_test)} test)',
                  score=score, score_max=2.0, threshold=2.0)


# ─────────────── DV-04: score-history row matches HEAD ───────────────

def dv_04_score_history_logged() -> Result:
    info = _last_lab_touching_commit()
    if info is None:
        return Result('SKIP', 'no lab-touching commit',
                      score=0.0, score_max=1.0, threshold=1.0)
    sha, _, _, files = info
    runner_files = [f for f in files
                    if f.startswith('scripts/test-runners/')
                    and f.endswith('-runner.py')]
    if not runner_files:
        # Vacuous PASS — no runner touched
        return Result('PASS', f'sha={sha[:8]}; no runner touched (vacuous)',
                      score=1.0, score_max=1.0, threshold=1.0)
    head_short = sha[:10]
    found_logged = False
    for rf in runner_files:
        name = Path(rf).stem
        log = (FORGE / 'scripts' / 'test-runners' / '.score-history'
               / f'{name}.jsonl')
        if not log.exists():
            continue
        if head_short in log.read_text(encoding='utf-8'):
            found_logged = True; break
    score = 1.0 if found_logged else 0.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'sha={sha[:8]}; runners touched={len(runner_files)}; '
                  f'logged={found_logged}',
                  score=score, score_max=1.0, threshold=1.0)


# ─────────────── DV-05: no silent cross-lab edits ───────────────

def dv_05_no_silent_cross_lab() -> Result:
    info = _last_lab_touching_commit()
    if info is None:
        return Result('SKIP', 'no lab-touching commit',
                      score=0.0, score_max=1.0, threshold=1.0)
    sha, _, body, files = info
    labs_touched = set()
    for f in files:
        m = re.match(r'^phase-c-information-systems-architecture/'
                     r'application-architecture/([^/]+)/', f)
        if m:
            labs_touched.add(m.group(1))
    cross_lab = len(labs_touched) > 1
    has_xlab_adr = bool(re.search(r'(?i)cross-lab:.*ADR\s*\d+', body))
    score = 1.0 if (not cross_lab or has_xlab_adr) else 0.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'sha={sha[:8]}; labs_touched={sorted(labs_touched)}; '
                  f'cross_lab={cross_lab}; xlab_adr={has_xlab_adr}',
                  score=score, score_max=1.0, threshold=1.0)


# ─────────────── DV-06: author identity ───────────────

def dv_06_author_identity() -> Result:
    info = _last_lab_touching_commit()
    if info is None:
        return Result('SKIP', 'no lab-touching commit',
                      score=0.0, score_max=1.0, threshold=1.0)
    sha, author, _, _ = info
    score = 1.0 if author == 'vasiliy-mikhailov' else 0.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'sha={sha[:8]}; author={author!r}',
                  score=score, score_max=1.0, threshold=1.0)


REGISTRY = {
    'DV-01': dv_01_commit_cites_driver,
    'DV-02': dv_02_tdd_discipline,
    'DV-03': dv_03_python_collects,
    'DV-04': dv_04_score_history_logged,
    'DV-05': dv_05_no_silent_cross_lab,
    'DV-06': dv_06_author_identity,
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
        score_str = ''
        if r.score is not None and r.score_max is not None:
            score_str = f' [{r.score}/{r.score_max}]'
        print(f'  {tid:<6} {r.verdict:<19}{score_str}  {r.detail}'.rstrip())
        rows.append((tid, r.verdict, r.score, r.score_max, r.threshold,
                     r.detail))

    print()
    print(f'  total: PASS={counts["PASS"]}  '
          f'PASS-italian-strike={counts.get("PASS-italian-strike", 0)}  '
          f'FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')
    if log_scores:
        path = _score_history.append_scores('test-developer-runner', rows)
        print(f'  logged {len(rows)} rows -> '
              f'{path.relative_to(FORGE)}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
