#!/usr/bin/env python3
"""Unit-test runner for tests/phase-b-business-architecture/roles/test-wiki-pm.md

Per ADR 0013 the md is the spec; this runner is the derived mechanism
(per the smoke.md → smoke.sh pattern). Outcomes: PASS, FAIL, SKIP. This runner mirrors the md test
cases as Python functions, runs them, and prints one PASS / FAIL / SKIP
line per test.

All cases live in test-wiki-pm.md as agentic behaviour tests
(WP-NN). This runner automates the executable subset (artefact
inspection over corpus-observations.md). Cases requiring agent
judgement (WP-07..WP-14) return SKIP — they need an
LLM-as-judge harness or architect eye-read.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history  # noqa: E402

FORGE = Path(__file__).resolve().parents[2]
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
    verdict: str  # PASS | FAIL | SKIP | PASS-italian-strike
    detail: str = ''
    score: float | None = None
    score_max: float | None = None
    threshold: float | None = None  # ADR 0015 dec 5 (score-history)


def adr0015_verdict(score: float, score_max: float, threshold: float) -> str:
    """Per ADR 0015: PASS ≥ 0.8*max; PASS-italian-strike ≥ threshold; FAIL < threshold."""
    if score < threshold:
        return 'FAIL'
    if score >= 0.8 * score_max:
        return 'PASS'
    return 'PASS-italian-strike'


# ─────────────── Inspection tests (I-NN) ───────────────

def i_01_file_exists() -> Result:
    """WP-01 component-1 spec: 1 pt, binary."""
    if OUT_OBS.exists():
        return Result('PASS', score=1.0, score_max=1.0)
    return Result('FAIL', f'file missing: {OUT_OBS.relative_to(FORGE)}',
                  score=0.0, score_max=1.0)


def i_02_file_nonempty() -> Result:
    """WP-01 component-2: ≥30 non-blank lines, 1 pt, binary."""
    if not OUT_OBS.exists():
        return Result('SKIP', 'WP-01 component-1 not green')
    lines = [ln for ln in OUT_OBS.read_text(encoding='utf-8').splitlines() if ln.strip()]
    score = 1.0 if len(lines) >= 30 else 0.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'{len(lines)} non-blank lines',
                  score=score, score_max=1.0)


def _bucket_obs_count(section: str) -> int | None:
    if not OUT_OBS.exists():
        return None
    text = OUT_OBS.read_text(encoding='utf-8')
    body = re.search(rf'(?ms)^## {section}\s*\n(.+?)(?=\n## |\Z)', text)
    if not body:
        return None
    return len(re.findall(r'(?m)^\*\*OBS-', body.group(1)))


def _bucket_score(n: int | None) -> float:
    """WP-02 ladder: 0 if <3, 0.5 if 3-9, 1.0 if ≥10. None → 0."""
    if n is None or n < 3:
        return 0.0
    if n < 10:
        return 0.5
    return 1.0


def i_03_substance_min_three() -> Result:
    """WP-02 component-Substance: ladder 0/0.5/1, italian-strike 0.5."""
    n = _bucket_obs_count('Substance')
    if n is None:
        return Result('SKIP', 'WP-01 not green', score=0.0, score_max=1.0)
    score = _bucket_score(n)
    # Threshold 0.5 (≥3 obs); italian-strike at 0.5 (just-above-floor); PASS at 1.0.
    return Result(adr0015_verdict(score, 1.0, 0.5),
                  f'{n} obs', score=score, score_max=1.0)


def i_04_form_min_three() -> Result:
    """WP-02 component-Form."""
    n = _bucket_obs_count('Form')
    if n is None:
        return Result('SKIP', 'WP-01 not green', score=0.0, score_max=1.0)
    score = _bucket_score(n)
    return Result(adr0015_verdict(score, 1.0, 0.5),
                  f'{n} obs', score=score, score_max=1.0)


def i_05_air_min_three() -> Result:
    """WP-02 component-Air."""
    n = _bucket_obs_count('Air')
    if n is None:
        return Result('SKIP', 'WP-01 not green', score=0.0, score_max=1.0)
    score = _bucket_score(n)
    return Result(adr0015_verdict(score, 1.0, 0.5),
                  f'{n} obs', score=score, score_max=1.0)


def i_06_quotes_verbatim() -> Result:
    """WP-03 spec: fraction = verified/total, 0..1, threshold 1.0 (any
    fabrication is FAIL — no partial credit). italian-strike: n/a.
    """
    if not OUT_OBS.exists():
        return Result('SKIP', 'WP-01 not green', score=0.0, score_max=1.0)
    text = OUT_OBS.read_text(encoding='utf-8')
    quotes = [m.group(1).strip() for m in re.finditer(r'(?m)^> (.+)$', text)
              if len(m.group(1).strip()) >= 8]
    if not quotes:
        return Result('SKIP', 'no quotes to verify', score=0.0, score_max=1.0)
    hay = ''
    for g in SAMPLE_GLOBS:
        for m in RAWS_ROOT.glob(g):
            d = json.load(m.open(encoding='utf-8'))
            hay += norm(' '.join(s.get('text', '').strip()
                                 for s in d.get('segments', []))) + ' '
    invented = [q[:60] for q in quotes if norm(q) not in hay]
    score = round((len(quotes) - len(invented)) / len(quotes), 3)
    return Result(
        adr0015_verdict(score, 1.0, 1.0),
        (f'{len(quotes)} quotes verified' if not invented
         else f'{len(invented)} of {len(quotes)} not in raws: {invented[:3]}'),
        score=score, score_max=1.0,
    )


def i_07_dimension_coverage() -> Result:
    """WP-04 spec: fraction = distinct/8, 0..1, threshold 0.75,
    italian-strike 0.75 ≤ score < 0.8 (just-above-threshold; 6/8
    exactly = 0.75, fits the italian-strike band).
    """
    if not OUT_OBS.exists():
        return Result('SKIP', 'WP-01 not green', score=0.0, score_max=1.0)
    text = OUT_OBS.read_text(encoding='utf-8')
    dims_seen: set[str] = set()
    for m in re.finditer(r'\[([^\]]+)\]', text):
        for piece in re.split(r'\]\s*\[', m.group(1).strip().lower()):
            piece = piece.strip()
            if piece in CAP_ALLOWLIST:
                dims_seen.add(piece)
    score = round(len(dims_seen) / 8, 3)
    return Result(
        adr0015_verdict(score, 1.0, 0.75),
        f'{len(dims_seen)}/8 covered: {sorted(dims_seen)[:4]}...',
        score=score, score_max=1.0,
    )


def i_08_no_R_NN_emitted() -> Result:
    """WP-05 spec: 1 pt, binary."""
    diff = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--',
         'phase-requirements-management/catalog.md'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout.strip()
    score = 0.0 if diff else 1.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'catalog.md modified: {diff}' if diff else '',
                  score=score, score_max=1.0)


def i_09_no_wiki_bench_modified() -> Result:
    """WP-06 spec: 1 pt, binary."""
    diff = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD', '--',
         'phase-c-information-systems-architecture/application-architecture/wiki-bench/'],
        capture_output=True, text=True, cwd=FORGE,
    ).stdout.strip()
    score = 0.0 if diff else 1.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'wiki-bench modified: {diff}' if diff else '',
                  score=score, score_max=1.0)


# ─────────────── Decision tests (D-NN) ───────────────
# Decision tests need an LLM-as-judge harness or a stub model that
# returns the role's classification. Until that lands, all D-NN tests
# return SKIP. The fixture and expected assertions are encoded so a
# future runner can wire them up without re-deriving them from md.

DECISION_TESTS = {
    'WP-07': dict(
        fixture='переживать, страдать, мучиться и так далее, и так далее, и так далее.',
        expected_bucket='Air', expected_dim='reading speed',
        rationale_keywords=['и так далее', 'filler', 'triple-trail'],
    ),
    'WP-08': dict(
        fixture='то есть это эмпатические отношения, эмпатические отношения.',
        expected_bucket='Air', expected_dim='reading speed',
        rationale_keywords=['repetition', 'doubling', 'spoken', 'word-doubling'],
    ),
    'WP-09': dict(
        fixture='Все ли это? Тоже далеко не все.',
        expected_bucket='Air', expected_dim='reading speed',
        rationale_keywords=['rhetorical', 'self-q&a', 'lifts', 'self-q', 'self-question'],
    ),
    'WP-10': dict(
        fixture='Стресс — это, если опираться на определение, которое дал ему автор теории Ганс Селье, естественная реакция нашей психики и организма на изменения среды.',
        expected_bucket='Substance', expected_dim='concept-graph quality',
        rationale_keywords=['attribution', 'selye', 'verifiable', 'Селье'],
    ),
    'WP-11': dict(
        fixture='Несколько слов скажу, поскольку я сам автор системной поведенческой психотерапии',
        expected_bucket=['Form', 'Air'],
        expected_dim='voice preservation',
        rationale_keywords=['self-citation', 'СПП', 'branded'],
    ),
    'WP-12': dict(
        fixture='А теперь представьте, что у вас был какой-нибудь близкий друг, с которым вы были в хороших отношениях',
        expected_bucket='Form', expected_dim='voice preservation',
        rationale_keywords=['direct address', 'thought experiment', 'scenario', 'direct-address'],
    ),
    'WP-13': dict(
        fixture='психотерапевтический контакт, установить, иногда это говорят, рапорт, или доверительные отношения с клиентом',
        expected_bucket=None,
        expected_dim='voice preservation',
        rationale_keywords=['synonym chain', 'synonym-chain', 'synonym'],
    ),
    'WP-14': dict(
        fixture='и так далее, и так далее, и так далее',
        expected_bucket=None, expected_dim='reading speed',
        rationale_keywords=['filler', 'triple-trail', 'и так далее'],
    ),
}


# ─────────── Answer ledger (ADR 0015 LLM-as-judge harness) ───────────

ANSWER_LEDGER_PATH = (Path(__file__).resolve().parent.parent.parent
                      / 'tests/phase-b-business-architecture/roles/wiki-pm-answers.json')


def load_answer_ledger() -> dict:
    """Read the Wiki PM's classification ledger.

    Per ADR 0015 dec 3, the agent's response per fixture is captured as
    a categorical / textual answer; the runner does mechanical scoring
    (substring match) over the answer.
    """
    if not ANSWER_LEDGER_PATH.exists():
        return {}
    return json.loads(ANSWER_LEDGER_PATH.read_text(encoding='utf-8'))


def score_wp_decision(case_id: str, spec: dict, answer: dict | None,
                       ) -> tuple[float, float, list[str]]:
    """Reward for WP-07..WP-14 per ADR 0015.

    Components (each 1 pt):
      C1. answer.bucket matches expected_bucket
          (or is in the list, when expected is a list;
           or is non-empty, when expected is None / tag-only).
      C2. expected_dim substring appears in answer.dimensions[*].
      C3. any rationale_keyword appears in answer.rationale.

    Aggregate: sum. Range 0..3. PASS threshold 2.
    Italian-strike band: 2 ≤ score < 2.4.
    """
    notes: list[str] = []
    if answer is None:
        return 0.0, 3.0, ['no ledger entry']
    score = 0.0

    expected_bucket = spec['expected_bucket']
    answer_bucket = (answer.get('bucket') or '').strip()
    if expected_bucket is None:
        if answer_bucket:
            score += 1; notes.append(f'C1=1 (bucket={answer_bucket}; tag-only)')
        else:
            notes.append('C1=0 (no bucket)')
    elif isinstance(expected_bucket, list):
        if answer_bucket in expected_bucket:
            score += 1; notes.append(f'C1=1 (bucket={answer_bucket} ∈ {expected_bucket})')
        else:
            notes.append(f'C1=0 (bucket={answer_bucket} ∉ {expected_bucket})')
    else:
        if answer_bucket == expected_bucket:
            score += 1; notes.append(f'C1=1 (bucket={answer_bucket})')
        else:
            notes.append(f'C1=0 (bucket={answer_bucket} ≠ {expected_bucket})')

    expected_dim = (spec.get('expected_dim') or '').lower()
    answer_dims = ' '.join(answer.get('dimensions', [])).lower()
    if expected_dim and expected_dim in answer_dims:
        score += 1; notes.append(f'C2=1 (dim has "{expected_dim}")')
    else:
        notes.append(f'C2=0 (dim="{answer_dims}" lacks "{expected_dim}")')

    answer_rationale = (answer.get('rationale') or '').lower()
    matched_kw = [kw for kw in spec.get('rationale_keywords', [])
                  if kw.lower() in answer_rationale]
    if matched_kw:
        score += 1; notes.append(f'C3=1 (matched: {matched_kw[:3]})')
    else:
        notes.append('C3=0 (no rationale keyword matched)')

    return score, 3.0, notes


def make_decision_test(test_id: str):
    spec = DECISION_TESTS[test_id]

    def runner() -> Result:
        ledger = load_answer_ledger()
        answer = ledger.get(test_id)
        if answer is None:
            return Result(
                'SKIP',
                f'no ledger entry for {test_id} in wiki-pm-answers.json',
                score=0.0, score_max=3.0,
            )
        score, score_max, notes = score_wp_decision(test_id, spec, answer)
        verdict = adr0015_verdict(score, score_max, threshold=2.0)
        return Result(
            verdict,
            f'score={score}/{score_max}; {", ".join(notes)}',
            score=score, score_max=score_max,
        )

    return runner


# ─────────────── Registry + driver ───────────────

REGISTRY = {
    'WP-01': i_01_file_exists,
    'WP-01b': i_02_file_nonempty,
    'WP-02a': i_03_substance_min_three,
    'WP-02b': i_04_form_min_three,
    'WP-02c': i_05_air_min_three,
    'WP-03': i_06_quotes_verbatim,
    'WP-04': i_07_dimension_coverage,
    'WP-05': i_08_no_R_NN_emitted,
    'WP-06': i_09_no_wiki_bench_modified,
    **{k: make_decision_test(k) for k in DECISION_TESTS},
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
        line = f'  {tid:<6} {r.verdict:<19}{score_str}  {r.detail}'.rstrip()
        print(line)
        rows.append((tid, r.verdict, r.score, r.score_max, r.threshold, r.detail))

    print()
    print(f'  total: PASS={counts["PASS"]}  '
          f'PASS-italian-strike={counts.get("PASS-italian-strike", 0)}  '
          f'FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')
    if log_scores:
        path = _score_history.append_scores('test-wiki-pm-runner', rows)
        print(f'  logged {len(rows)} rows -> {path.relative_to(Path(__file__).resolve().parents[2])}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
