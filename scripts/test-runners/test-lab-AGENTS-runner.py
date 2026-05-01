#!/usr/bin/env python3
"""Shared runner for the 4 lab AGENTS.md tests (LA-RL/WB/WC/WI-NN).

Per ADR 0013 each lab AGENTS.md is runtime md and gets a test md at
the mirror path; per ADR 0015 each test case has a Reward function.
This runner consumes the 4 test md files (one per lab) and scores
each case mechanically (file-presence, header-grep, content-line
count, template-cross-link substring).

Usage:
    python3 test-lab-AGENTS-runner.py             # all 4 labs × 4 cases
    python3 test-lab-AGENTS-runner.py wiki-bench  # one lab
    python3 test-lab-AGENTS-runner.py 'LA-WC-*'   # fnmatch pattern

Exit code: 0 on all-PASS (italian-strike does NOT count as failure
per ADR 0015 dec 4); 1 if any FAIL.
"""
from __future__ import annotations
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

FORGE = Path(__file__).resolve().parents[2]

LABS = {
    'RL': 'rl-2048',
    'WB': 'wiki-bench',
    'WC': 'wiki-compiler',
    'WI': 'wiki-ingest',
}
LAB_BASE = 'phase-c-information-systems-architecture/application-architecture'

PHASE_HEADERS = [f'## Phase {ph} ' for ph in 'ABCDEFGH']


@dataclass
class Result:
    verdict: str  # PASS | FAIL | SKIP | PASS-italian-strike
    detail: str = ''
    score: float | None = None
    score_max: float | None = None


def adr0015_verdict(score: float, score_max: float, threshold: float) -> str:
    if score < threshold:
        return 'FAIL'
    if score >= 0.8 * score_max:
        return 'PASS'
    return 'PASS-italian-strike'


def lab_agents_path(lab_slug: str) -> Path:
    return FORGE / LAB_BASE / lab_slug / 'AGENTS.md'


def la_01_file_exists(lab_slug: str) -> Result:
    """LA-XX-01: file exists."""
    p = lab_agents_path(lab_slug)
    if p.exists():
        return Result(adr0015_verdict(1.0, 1.0, 1.0),
                      f'{p.relative_to(FORGE)}',
                      score=1.0, score_max=1.0)
    return Result('FAIL', f'missing: {p.relative_to(FORGE)}',
                  score=0.0, score_max=1.0)


def la_02_phase_headers(lab_slug: str) -> Result:
    """LA-XX-02: 8/8 Phase A-H headers."""
    p = lab_agents_path(lab_slug)
    if not p.exists():
        return Result('SKIP', 'LA-01 not green', score=0.0, score_max=1.0)
    text = p.read_text(encoding='utf-8')
    found = [h for h in PHASE_HEADERS if h in text]
    score = round(len(found) / 8, 3)
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'{len(found)}/8 headers',
                  score=score, score_max=1.0)


def la_03_template_link(lab_slug: str) -> Result:
    """LA-XX-03: cross-links lab-AGENTS-template.md."""
    p = lab_agents_path(lab_slug)
    if not p.exists():
        return Result('SKIP', 'LA-01 not green', score=0.0, score_max=1.0)
    text = p.read_text(encoding='utf-8')
    found = 'lab-AGENTS-template.md' in text
    score = 1.0 if found else 0.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  '' if found else 'no template cross-link',
                  score=score, score_max=1.0)


def la_04_phases_filled(lab_slug: str) -> Result:
    """LA-XX-04: every Phase header has ≥1 non-blank body line."""
    p = lab_agents_path(lab_slug)
    if not p.exists():
        return Result('SKIP', 'LA-01 not green', score=0.0, score_max=1.0)
    text = p.read_text(encoding='utf-8')
    filled = 0
    for ph in 'ABCDEFGH':
        m = re.search(rf'(?ms)^## Phase {ph} .+?(?=\n## |\Z)', text)
        if not m:
            continue
        body = m.group(0).split('\n', 1)[1] if '\n' in m.group(0) else ''
        if any(ln.strip() for ln in body.splitlines()):
            filled += 1
    score = round(filled / 8, 3)
    return Result(adr0015_verdict(score, 1.0, 0.75),
                  f'{filled}/8 phases filled',
                  score=score, score_max=1.0)


def main() -> int:
    pat = sys.argv[1] if len(sys.argv) > 1 else '*'

    cases: list[tuple[str, callable, str]] = []
    for short, slug in LABS.items():
        for n, fn in [
            (1, la_01_file_exists),
            (2, la_02_phase_headers),
            (3, la_03_template_link),
            (4, la_04_phases_filled),
        ]:
            tid = f'LA-{short}-{n:02d}'
            cases.append((tid, fn, slug))

    # Allow patterns like 'wiki-bench' (filter by slug) or 'LA-WC-*' (filter by id)
    selected = [(tid, fn, slug) for tid, fn, slug in cases
                if fnmatch(tid, pat) or pat == slug or pat == '*']
    if not selected:
        print(f'no tests match pattern {pat!r}')
        return 1

    counts = {'PASS': 0, 'FAIL': 0, 'SKIP': 0, 'PASS-italian-strike': 0}
    for tid, fn, slug in selected:
        r = fn(slug)
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
        score_str = ''
        if r.score is not None:
            score_str = f' [{r.score}/{r.score_max}]'
        print(f'  {tid:<10} {r.verdict:<19}{score_str}  {r.detail}'.rstrip())

    print()
    print(f'  total: PASS={counts["PASS"]}  '
          f'PASS-italian-strike={counts.get("PASS-italian-strike", 0)}  '
          f'FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
