#!/usr/bin/env python3
"""Unit-test runner for tests/phase-b-business-architecture/roles/test-wiki-pm.md

Per ADR 0013, each test in the md file has Arrange / Act / Assert and one
of three outcomes: GREEN, RED, SKIPPED. This runner mirrors the md test
cases as Python functions, runs them, and prints one PASS / FAIL / SKIP
line per test.

Two kinds of test:
  - Inspection (I-NN) — read an artefact, assert one property.
  - Decision   (D-NN) — given a fixture quote, assert the role's
                        classification matches expectations. SKIPPED
                        until a decision-test harness exists (no
                        LLM-as-judge integration today).

Usage:
    python3 test-wiki-pm-verifier.py             # run all
    python3 test-wiki-pm-verifier.py I-01        # run one
    python3 test-wiki-pm-verifier.py I-*         # run a group

Exit code:
  0 — all RAN tests passed (SKIPPED tests do NOT count as failures
       and do NOT count as passes; they're reported separately).
  1 — at least one RAN test failed.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

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


@dataclass
class Result:
    verdict: str  # PASS | FAIL | SKIP
    detail: str = ''


# ─────────────── Inspection tests (I-NN) ───────────────

def i_01_file_exists() -> Result:
    if OUT_OBS.exists():
        return Result('PASS')
    return Result('FAIL', f'file missing: {OUT_OBS.relative_to(FORGE)}')


def i_02_file_nonempty() -> Result:
    if not OUT_OBS.exists():
        return Result('SKIP', 'I-01 not green')
    lines = [ln for ln in OUT_OBS.read_text(encoding='utf-8').splitlines() if ln.strip()]
    if len(lines) >= 30:
        return Result('PASS')
    return Result('FAIL', f'only {len(lines)} non-blank lines (<30)')


def _bucket_obs_count(section: str) -> int | None:
    if not OUT_OBS.exists():
        return None
    text = OUT_OBS.read_text(encoding='utf-8')
    body = re.search(rf'(?ms)^## {section}\s*\n(.+?)(?=\n## |\Z)', text)
    if not body:
        return None
    return len(re.findall(r'(?m)^\*\*OBS-', body.group(1)))


def i_03_substance_min_three() -> Result:
    n = _bucket_obs_count('Substance')
    if n is None:
        return Result('SKIP', 'I-01 not green')
    return Result('PASS') if n >= 3 else Result('FAIL', f'{n} obs <3')


def i_04_form_min_three() -> Result:
    n = _bucket_obs_count('Form')
    if n is None:
        return Result('SKIP', 'I-01 not green')
    return Result('PASS') if n >= 3 else Result('FAIL', f'{n} obs <3')


def i_05_air_min_three() -> Result:
    n = _bucket_obs_count('Air')
    if n is None:
        return Result('SKIP', 'I-01 not green')
    return Result('PASS') if n >= 3 else Result('FAIL', f'{n} obs <3')


def i_06_quotes_verbatim() -> Result:
    if not OUT_OBS.exists():
        return Result('SKIP', 'I-01 not green')
    text = OUT_OBS.read_text(encoding='utf-8')
    quotes = [m.group(1).strip() for m in re.finditer(r'(?m)^> (.+)$', text)
              if len(m.group(1).strip()) >= 8]
    if not quotes:
        return Result('SKIP', 'no quotes to verify')
    hay = ''
    for g in SAMPLE_GLOBS:
        for m in RAWS_ROOT.glob(g):
            d = json.load(m.open(encoding='utf-8'))
            hay += norm(' '.join(s.get('text', '').strip()
                                 for s in d.get('segments', []))) + ' '
    invented = [q[:60] for q in quotes if norm(q) not in hay]
    if not invented:
        return Result('PASS', f'{len(quotes)} quotes verified')
    return Result('FAIL', f'{len(invented)} of {len(quotes)} not in raws: {invented[:3]}')


def i_07_dimension_coverage() -> Result:
    if not OUT_OBS.exists():
        return Result('SKIP', 'I-01 not green')
    text = OUT_OBS.read_text(encoding='utf-8')
    dims_seen: set[str] = set()
    for m in re.finditer(r'\[([^\]]+)\]', text):
        for piece in re.split(r'\]\s*\[', m.group(1).strip().lower()):
            piece = piece.strip()
            if piece in CAP_ALLOWLIST:
                dims_seen.add(piece)
    if len(dims_seen) >= 6:
        return Result('PASS', f'{len(dims_seen)}/8 covered')
    return Result('FAIL', f'only {len(dims_seen)}/8: {sorted(dims_seen)}')


def i_08_no_R_NN_emitted() -> Result:
    diff = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--',
         'phase-requirements-management/catalog.md'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout.strip()
    if not diff:
        return Result('PASS')
    return Result('FAIL', f'catalog.md modified: {diff}')


def i_09_no_wiki_bench_modified() -> Result:
    diff = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--',
         'phase-c-information-systems-architecture/application-architecture/wiki-bench/'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout.strip()
    if not diff:
        return Result('PASS')
    return Result('FAIL', f'wiki-bench modified: {diff}')


# ─────────────── Decision tests (D-NN) ───────────────
# Decision tests need an LLM-as-judge harness or a stub model that
# returns the role's classification. Until that lands, all D-NN tests
# return SKIP. The fixture and expected assertions are encoded so a
# future runner can wire them up without re-deriving them from md.

DECISION_TESTS = {
    'D-01': dict(
        fixture='переживать, страдать, мучиться и так далее, и так далее, и так далее.',
        expected_bucket='Air', expected_dim='reading speed',
        rationale_keywords=['и так далее', 'filler', 'triple-trail'],
    ),
    'D-02': dict(
        fixture='то есть это эмпатические отношения, эмпатические отношения.',
        expected_bucket='Air', expected_dim='reading speed',
        rationale_keywords=['repetition', 'doubling', 'spoken'],
    ),
    'D-03': dict(
        fixture='Все ли это? Тоже далеко не все.',
        expected_bucket='Air', expected_dim='reading speed',
        rationale_keywords=['rhetorical', 'self-Q&A', 'lifts'],
    ),
    'D-04': dict(
        fixture='Стресс — это, если опираться на определение, которое дал ему автор теории Ганс Селье, естественная реакция нашей психики и организма на изменения среды.',
        expected_bucket='Substance', expected_dim='concept-graph quality',
        rationale_keywords=['attribution', 'Selye', 'verifiable'],
    ),
    'D-05': dict(
        fixture='Несколько слов скажу, поскольку я сам автор системной поведенческой психотерапии',
        expected_bucket=['Form', 'Air'],  # depends on session state
        expected_dim='voice preservation',
        rationale_keywords=['self-citation', 'СПП', 'branded'],
    ),
    'D-06': dict(
        fixture='А теперь представьте, что у вас был какой-нибудь близкий друг, с которым вы были в хороших отношениях',
        expected_bucket='Form', expected_dim='voice preservation',
        rationale_keywords=['direct address', 'thought experiment', 'scenario'],
    ),
    'D-07': dict(
        fixture='психотерапевтический контакт, установить, иногда это говорят, рапорт, или доверительные отношения с клиентом',
        expected_bucket=None,  # tag-only test
        expected_dim='voice preservation',
        rationale_keywords=['synonym chain'],
    ),
    'D-08': dict(
        fixture='и так далее, и так далее, и так далее',
        expected_bucket=None, expected_dim='reading speed',
        rationale_keywords=['filler'],
    ),
}


def make_decision_test(test_id: str):
    spec = DECISION_TESTS[test_id]
    def runner() -> Result:
        # No LLM-as-judge harness yet — return SKIP, but with the
        # exact prompt + expectation, so a future harness can pick
        # up without re-derivation.
        return Result(
            'SKIP',
            f'no decision-test harness; fixture {spec["fixture"][:40]!r}…, '
            f'expects bucket={spec["expected_bucket"]} dim={spec["expected_dim"]!r}',
        )
    return runner


# ─────────────── Registry + driver ───────────────

REGISTRY = {
    'I-01': i_01_file_exists,
    'I-02': i_02_file_nonempty,
    'I-03': i_03_substance_min_three,
    'I-04': i_04_form_min_three,
    'I-05': i_05_air_min_three,
    'I-06': i_06_quotes_verbatim,
    'I-07': i_07_dimension_coverage,
    'I-08': i_08_no_R_NN_emitted,
    'I-09': i_09_no_wiki_bench_modified,
    **{k: make_decision_test(k) for k in DECISION_TESTS},
}


def main() -> int:
    pat = sys.argv[1] if len(sys.argv) > 1 else '*'
    selected = [k for k in REGISTRY if fnmatch(k, pat)]
    if not selected:
        print(f'no tests match pattern {pat!r}')
        return 1

    counts = {'PASS': 0, 'FAIL': 0, 'SKIP': 0}
    for tid in selected:
        r = REGISTRY[tid]()
        counts[r.verdict] += 1
        line = f'  {tid:<6} {r.verdict:<4}  {r.detail}'.rstrip()
        print(line)

    print()
    print(f'  total: PASS={counts["PASS"]}  FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
