#!/usr/bin/env python3
"""Verifier for tests/phase-b-business-architecture/roles/test-wiki-pm.md

Mechanical predicates for the three scenarios T-WP-01 / T-WP-02 / T-WP-03.
The MD file is the spec; this script is the runner that derives from it,
exactly the way smoke.sh derives from smoke.md (per ADR 0013).

Usage:
    python3 tests/phase-b-business-architecture/roles/test-wiki-pm-verifier.py [01|02|03|all]

Exit code: 0 on GREEN, 1 on RED. RED prints the failed predicates with
specific diagnostics so the operator (architect or agent) knows what
to fix.

Dependencies: stdlib only. No PyPI. Reads raw.json from the sibling
kurpatov-wiki-raw repo.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# Resolve forge root from this file's location (this file lives at
# forge/tests/phase-b-business-architecture/roles/).
FORGE = Path(__file__).resolve().parents[3]

OUT_OBS = FORGE / 'phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md'
RAWS_ROOT = FORGE.parent / 'kurpatov-wiki-raw' / 'data' / 'Психолог-консультант'

CAP_ALLOWLIST = {
    "voice preservation", "reading speed", "dedup correctness",
    "fact-check coverage", "concept-graph quality", "reproducibility",
    "transcription accuracy", "requirement traceability",
}

SAMPLE_GLOBS = [
    '000 Путеводитель по программе/000 Знакомство*/raw.json',
    '000 Путеводитель по программе/002 Вводная*/raw.json',
    '005 *внутренних конфликтов*/000 Вводная*/raw.json',
    '005 *внутренних конфликтов*/001 №1*/raw.json',
    '001 *Глубинная*/000 № 1. Вводная*/raw.json',
]


def norm(s: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', s)).strip()


def load_haystack() -> dict[str, str]:
    hay: dict[str, str] = {}
    for g in SAMPLE_GLOBS:
        for m in RAWS_ROOT.glob(g):
            d = json.load(m.open(encoding='utf-8'))
            text = ' '.join(s.get('text', '').strip() for s in d.get('segments', []))
            hay[m.parent.name[:30]] = norm(text)
    return hay


def t_wp_01() -> tuple[bool, list[str]]:
    failures: list[str] = []

    if not OUT_OBS.exists():
        return False, ['#1 corpus-observations.md missing']

    text = OUT_OBS.read_text(encoding='utf-8')
    lines = text.splitlines()

    if len(lines) < 30:
        failures.append(f'#1 file lines {len(lines)} < 30')

    need = ['## Substance', '## Form', '## Air']
    have = [h for h in need if re.search(rf'(?m)^{re.escape(h)}\b', text)]
    if len(have) != 3:
        failures.append(f'#2 missing buckets: {set(need) - set(have)}')

    hay = load_haystack()
    quotes = [m.group(1).strip() for m in re.finditer(r'(?m)^> (.+)$', text)
              if len(m.group(1).strip()) >= 8]
    invented = [q[:80] for q in quotes if not any(norm(q) in h for h in hay.values())]
    if invented:
        failures.append(f'#3/#4 {len(invented)} unverified quotes:')
        for q in invented:
            failures.append(f'    MISSING: {q!r}')

    dims_seen: set[str] = set()
    for m in re.finditer(r'\[([^\]]+)\]', text):
        for piece in re.split(r'\]\s*\[', m.group(1).strip().lower()):
            piece = piece.strip()
            if piece in CAP_ALLOWLIST:
                dims_seen.add(piece)
    if len(dims_seen) < 6:
        failures.append(f'#5 only {len(dims_seen)}/8 dimensions covered: {sorted(dims_seen)}')

    for sec in ['Substance', 'Form', 'Air']:
        body = re.search(rf'(?ms)^## {sec}\s*\n(.+?)(?=\n## |\Z)', text)
        obs_count = len(re.findall(r'(?m)^\*\*OBS-', body.group(1))) if body else 0
        if obs_count < 3:
            failures.append(f'#6 {sec} only {obs_count} observations (<3)')

    cat_diff = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--',
         'phase-requirements-management/catalog.md'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout.strip()
    if cat_diff:
        failures.append('#7 catalog.md modified — S7 is out of T-WP-01 scope')

    bench_diff = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--',
         'phase-c-information-systems-architecture/application-architecture/wiki-bench/'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout.strip()
    if bench_diff:
        failures.append('#8 wiki-bench modified — Wiki PM does not touch labs')

    return not failures, failures


def t_wp_02() -> tuple[bool, list[str]]:
    """T-WP-02 — no orphan R-NN rows. Skipped if no new rows in catalog diff."""
    failures: list[str] = []
    diff = subprocess.run(
        ['git', 'diff', 'HEAD', '--', 'phase-requirements-management/catalog.md'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout

    new_rows = [ln[1:] for ln in diff.splitlines()
                if ln.startswith('+') and ln[1:].lstrip().startswith('| R-B-')]
    if not new_rows:
        print('  T-WP-02: SKIPPED (no new R-B-* rows in catalog diff)')
        return True, []

    obs_text = OUT_OBS.read_text(encoding='utf-8') if OUT_OBS.exists() else ''
    obs_text_norm = norm(obs_text)

    for row in new_rows:
        cells = [c.strip() for c in row.split('|')[1:-1]]
        if len(cells) < 7:
            failures.append(f'  row malformed (cells={len(cells)}): {row[:80]}')
            continue
        rid, source, qdim, l1, l2, _attempt, status = cells[:7]

        if not re.match(r'^R-B-[a-z0-9-]+$', rid):
            failures.append(f'  {rid} fails ID regex')

        qdim_prefix = qdim.split('/')[0].strip().lower()
        if qdim_prefix not in CAP_ALLOWLIST:
            failures.append(f'  {rid} quality-dim "{qdim_prefix}" not in allow-list')

        if not l1 or not l2:
            failures.append(f'  {rid} empty Level1/Level2 cells')

        if status.strip().upper() != 'OPEN':
            failures.append(f'  {rid} status not OPEN (got {status!r})')

        if 'OBS-' not in source and 'corpus-observations' not in source.lower():
            quotes_in_src = re.findall(r'"([^"]+)"', source) + re.findall(r'`([^`]+)`', source)
            if not any(norm(q) in obs_text_norm for q in quotes_in_src if len(q) >= 6):
                failures.append(f'  {rid} no provenance citation to corpus-observations.md')

    return not failures, failures


def t_wp_03() -> tuple[bool, list[str]]:
    """T-WP-03 — no-touch list enforcement."""
    failures: list[str] = []
    status = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout

    no_touch_prefixes = (
        'phase-c-information-systems-architecture/application-architecture/wiki-bench/',
        'phase-c-information-systems-architecture/application-architecture/wiki-compiler/',
        'phase-c-information-systems-architecture/application-architecture/wiki-ingest/',
        'phase-d-technology-architecture/',
        'phase-preliminary/',
        'phase-a-architecture-vision/goals.md',
    )
    for line in status.splitlines():
        path = line[3:].strip()
        if any(path.startswith(p) for p in no_touch_prefixes):
            failures.append(f'  no-touch path modified: {path}')
        # Also catch role-file edits other than wiki-pm.md itself + wiki-pm-tests
        if path.startswith('phase-b-business-architecture/roles/') \
                and not path.endswith('wiki-pm.md') \
                and 'wiki-pm-tests/' not in path \
                and 'README.md' not in path:
            failures.append(f'  other role file modified: {path}')

    return not failures, failures


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    suites = {
        '01': ('T-WP-01', t_wp_01),
        '02': ('T-WP-02', t_wp_02),
        '03': ('T-WP-03', t_wp_03),
    }
    targets = suites if which == 'all' else {which: suites[which]}

    overall_ok = True
    for _key, (name, fn) in targets.items():
        ok, fails = fn()
        status = 'GREEN' if ok else 'RED'
        print(f'{name}: {status}')
        for f in fails:
            print(f'  {f}')
        overall_ok &= ok
    return 0 if overall_ok else 1


if __name__ == '__main__':
    sys.exit(main())
