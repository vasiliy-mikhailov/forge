#!/usr/bin/env python3
"""Unit-test runner for tests/phase-b-business-architecture/roles/test-auditor.md

Per ADR 0013 the md is the spec; this runner is the derived mechanism
(per the smoke.md → smoke.sh pattern). Outcomes: PASS, FAIL, SKIP. This runner mirrors the md
test cases as Python functions and prints PASS / FAIL / SKIP per test.

All cases live in test-auditor.md as agentic behaviour tests
(AU-NN). This runner automates each case mechanically — predicate
P6 is grep-based, so Decision cases run inline without an
LLM-as-judge harness. Outcomes: PASS, FAIL, SKIP.

Usage:
    python3 test-auditor-verifier.py            # run all
    python3 test-auditor-verifier.py I-AU-01    # run one
    python3 test-auditor-verifier.py 'D-*'      # fnmatch pattern

Exit code:
  0 — all RAN tests passed.
  1 — at least one FAIL.
"""
from __future__ import annotations
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

FORGE = Path(__file__).resolve().parents[2]
PHASE_H = FORGE / 'phase-h-architecture-change-management'


# ─────────────── P6 implementation (inline, used by D-AU tests) ───────────────

# ADR 0014 forbidden vocabulary patterns. Each pattern is paired with a
# label so a finding can name what it matched.
P6_PATTERNS = [
    # (regex, label, applies_to_relationship_verb_only)
    (r'\b(operations|capability)\s+stack\b', 'operations/capability stack', False),
    (r'\bis\s+responsible\s+for\b',          'is responsible for',           False),
    (r'\bare\s+responsible\s+for\b',         'are responsible for',          False),
    # "<noun> agent" used in subject position (org-unit-style).
    # Matches phrases like "The X agent does Y", "The Y-PM agent emits".
    (r'\bThe\s+\w[\w\-\s]*?agent\s+(?:emits|owns|drives|writes|runs|performs|decides)\b',
     'agent used as org-unit',     False),
    # "<noun> drives <noun>" / "<noun> owns <noun>" — relationship verb
    # in subject-verb-object form. Flag when both nouns look architecture-
    # relevant; cheap heuristic: the verb is followed by "the" + noun.
    (r'\b\w+\s+drives\s+the\s+\w+',
     'drives (relationship verb)', True),
    (r'\b\w+\s+owns\s+the\s+\w+',
     'owns (relationship verb)',   True),
]


def p6_findings(text: str) -> list[tuple[str, str]]:
    """Return [(label, matched_substring), …] for all P6 hits in text."""
    findings: list[tuple[str, str]] = []
    for pat, label, _ in P6_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            findings.append((label, m.group(0)))
    return findings


# ─────────────── helpers for inspection tests ───────────────

def latest_audit_path() -> Path | None:
    """Return the most recent audit-YYYY-MM-DD.md, or None."""
    candidates = sorted(
        PHASE_H.glob('audit-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].md')
    )
    return candidates[-1] if candidates else None


@dataclass
class Result:
    verdict: str  # PASS | FAIL | SKIP
    detail: str = ''


# ─────────────── Inspection tests (I-AU-NN) ───────────────

def i_au_01_audit_report_exists() -> Result:
    p = latest_audit_path()
    if p is None:
        return Result('FAIL', 'no audit-YYYY-MM-DD.md under phase-h-…')
    return Result('PASS', f'found {p.name}')


def i_au_02_audit_report_nonempty() -> Result:
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'I-AU-01 not green')
    n = sum(1 for ln in p.read_text(encoding='utf-8').splitlines() if ln.strip())
    return Result('PASS', f'{n} non-blank lines') if n >= 30 else Result('FAIL', f'{n} <30')


def i_au_03_audit_report_has_FAIL_WARN_INFO_sections() -> Result:
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'I-AU-01 not green')
    text = p.read_text(encoding='utf-8')
    missing = [v for v in ('FAIL', 'WARN', 'INFO')
               if not re.search(rf'(?im)^## Findings — verdict {v}\b', text)]
    if missing:
        return Result('FAIL', f'missing sections: {missing}')
    return Result('PASS')


def i_au_04_findings_carry_predicate_and_fix() -> Result:
    """Section-aware shape check.

    FAIL / WARN findings: must have Predicate + Symptom + Rule + (Proposed fix
        or escalation).
    INFO findings: must have Predicate + Symptom + Note (Rule and Proposed
        fix are optional per the audit-process.md format spec).
    """
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'I-AU-01 not green')
    text = p.read_text(encoding='utf-8')

    bad = []
    total = 0
    for verdict in ('FAIL', 'WARN', 'INFO'):
        section_match = re.search(
            rf'(?ms)^## Findings — verdict {verdict}\b.+?(?=\n## |\Z)', text
        )
        if not section_match:
            continue
        for blk in re.findall(r'(?ms)^### F\d+\..+?(?=\n### |\n## |\Z)',
                              section_match.group(0)):
            total += 1
            has_pred = bool(re.search(r'Predicate:\s*P\d+', blk))
            has_symptom = '**Symptom.**' in blk
            if verdict in ('FAIL', 'WARN'):
                has_rule = '**Rule.**' in blk
                has_fix = ('**Proposed fix or escalation.**' in blk
                           or '**Proposed fix.**' in blk)
                ok = has_pred and has_symptom and has_rule and has_fix
                detail = f'pred={has_pred} sym={has_symptom} rule={has_rule} fix={has_fix}'
            else:  # INFO
                has_note = '**Note.**' in blk
                ok = has_pred and has_symptom and has_note
                detail = f'pred={has_pred} sym={has_symptom} note={has_note}'
            if not ok:
                bad.append((verdict, blk[:60].splitlines()[0], detail))
    if total == 0:
        return Result('FAIL', 'no ### F<N>. blocks found in any section')
    if bad:
        return Result('FAIL', f'{len(bad)}/{total} blocks malformed: {bad[:3]}')
    return Result('PASS', f'{total} findings well-formed across FAIL/WARN/INFO')


def i_au_05_summary_totals_match() -> Result:
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'I-AU-01 not green')
    text = p.read_text(encoding='utf-8')
    counts: dict[str, int] = {}
    for verdict in ('FAIL', 'WARN', 'INFO'):
        section = re.search(
            rf'(?ms)^## Findings — verdict {verdict}\b.+?(?=\n## |\Z)', text
        )
        counts[verdict] = (
            len(re.findall(r'(?m)^### F\d+\.', section.group(0))) if section else 0
        )
    # Parse summary table
    summary_table = re.search(r'(?ms)^## Summary.+?(?=\n## |\Z)', text)
    if not summary_table:
        return Result('FAIL', 'no Summary section')
    declared = {}
    for v in ('FAIL', 'WARN', 'INFO'):
        m = re.search(rf'\|\s*{v}\s*\|\s*(\d+)\s*\|', summary_table.group(0))
        declared[v] = int(m.group(1)) if m else None
    mismatches = [(v, counts[v], declared[v]) for v in counts if declared[v] != counts[v]]
    if mismatches:
        return Result('FAIL', f'mismatch: {mismatches}')
    return Result('PASS', f'counts {counts}')


def i_au_06_predicates_walked_line() -> Result:
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'I-AU-01 not green')
    text = p.read_text(encoding='utf-8')
    m = re.search(r'(?im)^Predicates walked:[^\n]*', text)
    if not m:
        return Result('FAIL', 'no "Predicates walked:" line')
    ids = re.findall(r'P\d+', m.group(0))
    if not ids:
        return Result('FAIL', 'no predicate IDs in line')
    return Result('PASS', f'{len(ids)} predicates listed: {ids[:5]}...')


# ─────────────── Decision tests (D-AU-NN) ───────────────

DECISION_FIXTURES = {
    'AU-05': {
        'fixture': "The wiki line's operations stack — what wiki-* labs do per product.",
        'expect_findings': True,
        'expect_label_substr': 'operations',
    },
    'AU-06': {
        'fixture': 'The Wiki PM role is responsible for emitting requirements into the catalog.',
        'expect_findings': True,
        'expect_label_substr': 'responsible',
    },
    'AU-07': {
        'fixture': 'The Wiki PM agent emits R-NN rows into the catalog.',
        'expect_findings': True,
        'expect_label_substr': 'agent',
    },
    'AU-08': {
        'fixture': ('The Wiki PM Role is assigned to the Wiki-requirements-collection '
                    'Function. The Function realizes the Develop-wiki-product-line Capability.'),
        'expect_findings': False,
    },
    'AU-09': {
        'fixture': 'The compiler component drives the publish step. The bench owns the catalog.',
        'expect_findings': True,
        'min_findings': 2,
    },
}


def make_decision_test(test_id: str):
    spec = DECISION_FIXTURES[test_id]
    def runner() -> Result:
        findings = p6_findings(spec['fixture'])
        if spec['expect_findings']:
            min_n = spec.get('min_findings', 1)
            if len(findings) < min_n:
                return Result(
                    'FAIL',
                    f'expected ≥{min_n} findings, got {len(findings)}: {findings}',
                )
            if 'expect_label_substr' in spec:
                labels = ' '.join(label for label, _ in findings).lower()
                if spec['expect_label_substr'].lower() not in labels:
                    return Result(
                        'FAIL',
                        f'expected label containing {spec["expect_label_substr"]!r}; '
                        f'got labels: {[lbl for lbl, _ in findings]}',
                    )
            return Result('PASS', f'{len(findings)} findings: {findings[:2]}')
        else:
            if findings:
                return Result(
                    'FAIL',
                    f'expected zero findings on clean fixture, got: {findings}',
                )
            return Result('PASS', 'clean fixture; 0 findings')
    return runner


# ─────────────── Registry + driver ───────────────

REGISTRY = {
    'AU-01': i_au_01_audit_report_exists,
    'AU-01b': i_au_02_audit_report_nonempty,
    'AU-02': i_au_03_audit_report_has_FAIL_WARN_INFO_sections,
    'AU-03': i_au_04_findings_carry_predicate_and_fix,
    'AU-04': i_au_05_summary_totals_match,
    'AU-04b': i_au_06_predicates_walked_line,
    **{k: make_decision_test(k) for k in DECISION_FIXTURES},
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
        line = f'  {tid:<8} {r.verdict:<4}  {r.detail}'.rstrip()
        print(line)

    print()
    print(f'  total: PASS={counts["PASS"]}  FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
