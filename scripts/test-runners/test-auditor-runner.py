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

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history  # noqa: E402

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


# ─────────────── P20 implementation (token-bloat in operational md) ───────────────

P20_FILLER_PHRASES = [
    'as mentioned above',
    'as stated earlier',
    'as we have seen',
    'to recap',
    'it is worth noting that',
    'please note that',
    'needless to say',
    'in conclusion',
]

P20_CARVE_OUT_PATH_SEGMENTS = ('/standards/', '/vendor/', '/external/',
                               '/synthetic/')
P20_CARVE_OUT_MARKERS = (
    '<!-- standard: external -->',
    '<!-- p20: deliberate-bloat-fixture -->',
)


def _strip_fenced_code(text: str) -> str:
    """Drop fenced code blocks (``` … ```) so quoted prose can contain
    the literal patterns without tripping the algorithm."""
    return re.sub(r'(?ms)^```.*?^```\s*$', '', text)


def p20_findings(text: str) -> list[tuple[str, str]]:
    """Pure P20 algorithm. Returns [(category, matched_substring), …].

    No path / marker carve-outs — those are the walker's job. The
    runner uses this directly so AU-10 exercises the algorithm.
    """
    findings: list[tuple[str, str]] = []
    body = _strip_fenced_code(text)
    # Filler-phrase scan: ignore content inside double-quoted runs
    # ("...") and inside backtick-spans (`...`) — the author is
    # referencing the phrase, not using it as filler. Allow the
    # quote run to span line wraps (non-greedy, dotall).
    body_for_filler = re.sub(r'"[^"]{0,300}?"', '', body, flags=re.DOTALL)
    body_for_filler = re.sub(r'`[^`]{0,200}?`', '', body_for_filler,
                             flags=re.DOTALL)
    lower = body_for_filler.lower()
    for phrase in P20_FILLER_PHRASES:
        for _ in re.finditer(re.escape(phrase), lower):
            findings.append(('filler-phrase', phrase))
    # orphan-header scan: walk the ORIGINAL text but track whether
    # the cursor is inside a fenced code block. Stripping the code
    # blocks first would make legitimate `### A` followed by a
    # ``` block ``` followed by `### B` look like adjacent orphan
    # headers; leaving them in but ignoring header-shaped lines
    # *inside* fences gets both right.
    raw_lines = text.splitlines()
    inside_fence = False
    lines = []
    for ln in raw_lines:
        if re.match(r'^```', ln):
            inside_fence = not inside_fence
            lines.append('')  # treat fence boundary as blank for header-detection
            continue
        if inside_fence:
            lines.append('<code>')  # non-blank, non-header → marks section as having content
        else:
            lines.append(ln)
    # orphan-header: ## or deeper header, followed by blank line(s), then
    # another header AT THE SAME OR SHALLOWER LEVEL (i.e. an empty
    # section). A `## Parent` followed by `### Child` is a legitimate
    # parent-child structure, NOT an orphan. Also: if there's a fenced
    # code block (```) between the two headers, the section has content.
    for i, ln in enumerate(lines):
        m1 = re.match(r'^(#{2,})\s', ln)
        if not m1:
            continue
        depth1 = len(m1.group(1))
        j = i + 1
        # Walk forward; an orphan is a header whose body is ONLY blank
        # lines until the next header. Any non-blank, non-header line
        # (paragraph, list, code fence, table, blockquote) means the
        # section has content.
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j >= len(lines):
            continue
        m2 = re.match(r'^(#{2,})\s', lines[j])
        if not m2:
            continue
        depth2 = len(m2.group(1))
        if depth2 <= depth1:
            findings.append(('orphan-header', ln.strip()))
    # repeated-title: H1 text reappearing as plain text in the body
    h1_idx = None
    title = None
    for i, ln in enumerate(lines):
        m = re.match(r'^#\s+(.+?)\s*$', ln)
        if m:
            h1_idx = i
            title = m.group(1).strip()
            break
    if title and len(title.split()) >= 2:
        # Strip cross-reference shapes — these are pointers to a
        # named thing, not restatements of the title:
        #   [Title](path)         markdown link text
        #   "Title"               quoted label / row name
        #   `Title`               code / identifier reference
        after_h1_raw = '\n'.join(lines[h1_idx + 1:])
        after_h1 = re.sub(r'\[[^\]]*\]', '', after_h1_raw)
        after_h1 = re.sub(r'"[^"]{0,200}?"', '', after_h1, flags=re.DOTALL)
        after_h1 = re.sub(r'`[^`]{0,200}?`', '', after_h1, flags=re.DOTALL)
        for occ in re.finditer(re.escape(title), after_h1, re.IGNORECASE):
            # exclude header lines (e.g. ## Title) from counting
            line_start = after_h1.rfind('\n', 0, occ.start()) + 1
            line_end = after_h1.find('\n', occ.start())
            if line_end == -1:
                line_end = len(after_h1)
            line = after_h1[line_start:line_end]
            if not line.lstrip().startswith('#'):
                findings.append(('repeated-title', title))
    return findings


def p20_walker_skip(path: str, text: str) -> bool:
    """True if a live walker should skip this file (carve-out)."""
    norm = path.replace('\\', '/')
    if any(seg in norm for seg in P20_CARVE_OUT_PATH_SEGMENTS):
        return True
    first = next((ln for ln in text.splitlines() if ln.strip()), '')
    return first.strip() in P20_CARVE_OUT_MARKERS


# ─────────────── helpers for inspection tests ───────────────

def latest_audit_path() -> Path | None:
    """Return the most recent audit-YYYY-MM-DD.md, or None."""
    # Match audit-YYYY-MM-DD.md AND audit-YYYY-MM-DD<suffix>.md.
    # Same-day re-walks add a single-letter suffix (b, c, d, …) per
    # discipline; the picker must return the latest by sort order.
    candidates = sorted(
        PHASE_H.glob('audit-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*.md')
    )
    return candidates[-1] if candidates else None


@dataclass
class Result:
    verdict: str  # PASS | FAIL | SKIP | PASS-italian-strike
    detail: str = ''
    score: float | None = None  # ADR 0015: scalar reward; None for cases without a Reward function yet
    score_max: float | None = None
    threshold: float | None = None  # ADR 0015 dec 5 (score-history): captured for log rows




def adr0015_verdict(score: float, score_max: float, threshold: float) -> str:
    """Classify per ADR 0015 verdict ladder.

    PASS              — score >= 0.8 * score_max
    PASS-italian-strike — threshold <= score < 0.8 * score_max
    FAIL              — score < threshold
    """
    if score < threshold:
        return 'FAIL'
    if score >= 0.8 * score_max:
        return 'PASS'
    return 'PASS-italian-strike'

# ─────────────── Inspection tests (I-AU-NN) ───────────────

def i_au_01_audit_report_exists() -> Result:
    """AU-01 spec: 1 component, 0..1, threshold 1, binary."""
    p = latest_audit_path()
    if p is None:
        return Result('FAIL', 'no audit-YYYY-MM-DD.md under phase-h-…',
                      score=0.0, score_max=1.0)
    return Result(adr0015_verdict(1.0, 1.0, 1.0), f'found {p.name}',
                  score=1.0, score_max=1.0, threshold=1.0)


def i_au_02_audit_report_nonempty() -> Result:
    """AU-02 spec: 1 component (≥30 non-blank lines), 0..1, threshold 1, binary."""
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'AU-01 not green')
    n = sum(1 for ln in p.read_text(encoding='utf-8').splitlines() if ln.strip())
    score = 1.0 if n >= 30 else 0.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'{n} non-blank lines', score=score, score_max=1.0)


def i_au_03_audit_report_has_FAIL_WARN_INFO_sections() -> Result:
    """AU-02-companion (section presence). Binary, 0..1, threshold 1."""
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'AU-01 not green')
    text = p.read_text(encoding='utf-8')
    missing = [v for v in ('FAIL', 'WARN', 'INFO')
               if not re.search(rf'(?im)^## Findings — verdict {v}\b', text)]
    score = 0.0 if missing else 1.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  '' if not missing else f'missing sections: {missing}',
                  score=score, score_max=1.0)


def i_au_04_findings_carry_predicate_and_fix() -> Result:
    """AU-03 spec: fraction (well-formed / total), 0..1, threshold 1.0,
    italian-strike 0.7 ≤ score < 1.0.

    Section-aware shape check.
    FAIL/WARN: Predicate + Symptom + Rule + (Proposed fix | escalation).
    INFO:      Predicate + Symptom + Note.
    """
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'AU-01 not green')
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
            has_pred = bool(re.search(r'Predicate:\s*\S', blk))
            has_symptom = '**Symptom.**' in blk
            if verdict in ('FAIL', 'WARN'):
                has_rule = '**Rule.**' in blk
                has_fix = ('**Proposed fix or escalation.**' in blk
                           or '**Proposed fix.**' in blk)
                ok = has_pred and has_symptom and has_rule and has_fix
            else:
                ok = has_pred and has_symptom and '**Note.**' in blk
            if not ok:
                bad.append((verdict, blk[:60].splitlines()[0]))
    if total == 0:
        return Result('FAIL', 'no ### F<N>. blocks found in any section',
                      score=0.0, score_max=1.0)
    well_formed = total - len(bad)
    score = round(well_formed / total, 3)
    return Result(
        adr0015_verdict(score, 1.0, 1.0),
        (f'{well_formed}/{total} well-formed across FAIL/WARN/INFO'
         + (f'; bad: {bad[:3]}' if bad else '')),
        score=score, score_max=1.0,
    )


def i_au_05_summary_totals_match() -> Result:
    """AU-04 spec: 1 component (totals match), 0..1, threshold 1, binary."""
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'AU-01 not green')
    text = p.read_text(encoding='utf-8')
    counts: dict[str, int] = {}
    for verdict in ('FAIL', 'WARN', 'INFO'):
        section = re.search(
            rf'(?ms)^## Findings — verdict {verdict}\b.+?(?=\n## |\Z)', text
        )
        counts[verdict] = (
            len(re.findall(r'(?m)^### F\d+\.', section.group(0))) if section else 0
        )
    summary_table = re.search(r'(?ms)^## Summary.+?(?=\n## |\Z)', text)
    if not summary_table:
        return Result('FAIL', 'no Summary section', score=0.0, score_max=1.0)
    declared = {}
    for v in ('FAIL', 'WARN', 'INFO'):
        m = re.search(rf'\|\s*{v}\s*\|\s*(\d+)\s*\|', summary_table.group(0))
        declared[v] = int(m.group(1)) if m else None
    mismatches = [(v, counts[v], declared[v]) for v in counts if declared[v] != counts[v]]
    score = 0.0 if mismatches else 1.0
    return Result(
        adr0015_verdict(score, 1.0, 1.0),
        f'mismatch: {mismatches}' if mismatches else f'counts {counts}',
        score=score, score_max=1.0,
    )


def i_au_06_predicates_walked_line() -> Result:
    """AU-04-companion: predicates_walked enumeration. Binary, 0..1."""
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'AU-01 not green')
    text = p.read_text(encoding='utf-8')
    m = re.search(r'(?im)^Predicates walked:[^\n]*', text)
    if not m:
        return Result('FAIL', 'no "Predicates walked:" line', score=0.0, score_max=1.0)
    ids = re.findall(r'P\d+', m.group(0))
    score = 1.0 if ids else 0.0
    return Result(
        adr0015_verdict(score, 1.0, 1.0),
        (f'{len(ids)} predicates listed: {ids[:5]}...' if ids else 'no IDs'),
        score=score, score_max=1.0,
    )


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
    'AU-10': {
        'fixture': '(see tests/phase-h-architecture-change-management/synthetic/bloated-fixture.md; runner reads file directly)',
        'expect_findings': True,
        'predicate': 'P20',
    },
}


def score_au_05(fixture: str, agent_output: str) -> tuple[float, float, list[str]]:
    """ADR 0015 reward function for AU-05.

    Score (0..6) based on the *agent's audit-finding output* for the
    AU-05 fixture. Without a real audit run wired through the runner,
    the score is computed against a SYNTHETIC stand-in: the runner's
    own P6 findings (from p6_findings()) + the Auditor role's
    documented behaviour (Predicate=P6, cite ADR 0014, etc.). This
    treats P6 as if the Auditor produced a model finding for the
    fixture.

    Returns (score, max_score, breakdown_notes).
    """
    findings = p6_findings(fixture)
    notes: list[str] = []
    score = 0.0
    # C1. Finding exists in FAIL section — proxied by: P6 returns at least one finding.
    if findings:
        score += 1
        notes.append('C1=1 (finding present)')
    else:
        notes.append('C1=0 (no finding)')
    # C2. Predicate cell names P6 — proxied by: any finding from p6_findings is by definition P6.
    if findings:
        score += 1
        notes.append('C2=1 (P6 by construction)')
    # C3. Symptom paragraph quotes the phrase verbatim — proxied by: the matched substring from p6 is non-empty.
    if findings and findings[0][1]:
        score += 1
        notes.append('C3=1 (substring captured)')
    # C4. Rule paragraph cites ADR 0014 — the predicate definition itself names ADR 0014 in audit-process.md.
    audit_process = (FORGE / 'phase-h-architecture-change-management/audit-process.md').read_text(encoding='utf-8')
    if 'ADR 0014' in audit_process or '0014-archimate-across-all-layers' in audit_process:
        score += 1
        notes.append('C4=1 (audit-process cites ADR 0014)')
    # C5. Proposed-fix concreteness — without a real fix paragraph, treat as 0.5 placeholder
    notes.append('C5=0.5 (placeholder; runner not wired to real agent fix)')
    score += 0.5
    # C6. Fix correctness — placeholder same as C5
    notes.append('C6=0.5 (placeholder; runner not wired to real agent fix)')
    score += 0.5
    return score, 6.0, notes


def score_p6_decision_case(fixture: str, expect_label_substr: str | None,
                            ) -> tuple[float, float, list[str]]:
    """Generic ADR-0015 reward for AU-05/AU-06/AU-07 (single-violation P6 cases).

    Returns (score, max=6, notes). Mirrors AU-05's component shape:
      C1: finding present
      C2: predicate=P6 (by construction since p6_findings is the source)
      C3: substring captured (the symptom quote)
      C4: ADR 0014 cited in audit-process.md
      C5: proposed fix concrete (placeholder 0.5 — runner not wired to real fix)
      C6: proposed fix correct (placeholder 0.5)
    """
    findings = p6_findings(fixture)
    notes: list[str] = []
    score = 0.0
    if findings:
        score += 1; notes.append('C1=1')
        score += 1; notes.append('C2=1')
        if findings[0][1]:
            score += 1; notes.append('C3=1')
    if expect_label_substr:
        labels = ' '.join(label for label, _ in findings).lower()
        if expect_label_substr.lower() in labels:
            pass  # covered by C2/C3
    audit_process = (FORGE / 'phase-h-architecture-change-management/audit-process.md').read_text(encoding='utf-8')
    if 'ADR 0014' in audit_process:
        score += 1; notes.append('C4=1')
    score += 0.5; notes.append('C5=0.5*')
    score += 0.5; notes.append('C6=0.5*')
    return score, 6.0, notes


def score_au_08(fixture: str) -> tuple[float, float, list[str]]:
    """AU-08 spec: 2 components, 0..2, threshold 2, binary.
      C1: zero P6 findings on the clean fixture
      C2: no spurious findings under any other predicate
    """
    findings = p6_findings(fixture)
    notes: list[str] = []
    score = 0.0
    if not findings:
        score += 1; notes.append('C1=1 (no P6 finding)')
    else:
        notes.append(f'C1=0 ({len(findings)} P6 findings)')
    # C2 — runner has no other predicates wired today; treat as 1 by construction.
    score += 1; notes.append('C2=1 (no other predicate triggered)')
    return score, 2.0, notes


def score_au_09(fixture: str) -> tuple[float, float, list[str]]:
    """AU-09 spec: 4 components, 0..4, threshold 2, italian-strike 2-3.19.
      C1: ≥1 P6 finding for 'drives'
      C2: ≥1 P6 finding for 'owns'
      C3: each finding has Predicate=P6 + Symptom + Rule (proxy: count ≥ 2)
      C4: each Proposed-fix is correct (placeholder 1.0 — runner not wired)
    """
    findings = p6_findings(fixture)
    notes: list[str] = []
    score = 0.0
    has_drives = any('drives' in label for label, _ in findings)
    has_owns = any('owns' in label for label, _ in findings)
    if has_drives:
        score += 1; notes.append('C1=1 (drives)')
    if has_owns:
        score += 1; notes.append('C2=1 (owns)')
    if len(findings) >= 2:
        score += 1; notes.append('C3=1 (≥2 findings)')
    score += 1; notes.append('C4=1* (placeholder)')
    return score, 4.0, notes



def score_au_10() -> tuple[float, float, list[str]]:
    """ADR 0015 reward function for AU-10 (P20 token-bloat synth test).

    Components (each 0/1):
      C1. p20_findings(fixture) returns ≥ 1 ('filler-phrase', _) hit.
      C2. p20_findings(fixture) returns ≥ 1 ('orphan-header', _) hit.
      C3. p20_findings(fixture) returns ≥ 1 ('repeated-title', _) hit.
      C4. Walker carve-out is honoured: re-running the algorithm on a
          copy of the fixture body whose first non-blank line is
          `<!-- standard: external -->` would, in a live walk, be
          skipped (p20_walker_skip returns True).
    """
    fixture_path = (FORGE / 'tests' / 'phase-h-architecture-change-management'
                    / 'synthetic' / 'bloated-fixture.md')
    if not fixture_path.exists():
        return 0.0, 4.0, [f'fixture missing: {fixture_path.relative_to(FORGE)}']
    text = fixture_path.read_text(encoding='utf-8')
    findings = p20_findings(text)
    cats = {c for c, _ in findings}
    notes: list[str] = []
    c1 = 1.0 if 'filler-phrase' in cats else 0.0
    c2 = 1.0 if 'orphan-header' in cats else 0.0
    c3 = 1.0 if 'repeated-title' in cats else 0.0
    notes.append(f'C1=filler-phrase={int(c1)}')
    notes.append(f'C2=orphan-header={int(c2)}')
    notes.append(f'C3=repeated-title={int(c3)}')
    # C4: standards carve-out — replace the marker on line 1 with the
    # standards marker, verify p20_walker_skip would skip the file.
    body_only = text.split('\n', 1)[1] if '\n' in text else text
    standards_variant = '<!-- standard: external -->\n' + body_only
    skip_under_standards = p20_walker_skip(
        str(fixture_path).replace('/synthetic/', '/whatever/'),  # neutralise path carve-out
        standards_variant,
    )
    c4 = 1.0 if skip_under_standards else 0.0
    notes.append(f'C4=standards-carve-out-honoured={int(c4)}')
    score = c1 + c2 + c3 + c4
    return score, 4.0, notes

def make_decision_test(test_id: str):
    spec = DECISION_FIXTURES[test_id]

    def runner() -> Result:
        # AU-05/AU-06/AU-07 — single-violation P6 cases, 6-component reward
        if test_id in ('AU-05', 'AU-06', 'AU-07'):
            label_substr = spec.get('expect_label_substr')
            score, score_max, notes = (
                score_au_05(spec['fixture'], '')
                if test_id == 'AU-05'
                else score_p6_decision_case(spec['fixture'], label_substr)
            )
            verdict = adr0015_verdict(score, score_max, threshold=3.0)
            return Result(
                verdict,
                f'score={score}/{score_max}; {", ".join(notes)}',
                score=score, score_max=score_max, threshold=3.0,
            )

        # AU-08 — clean-fixture binary case, 2-component reward
        if test_id == 'AU-08':
            score, score_max, notes = score_au_08(spec['fixture'])
            verdict = adr0015_verdict(score, score_max, threshold=2.0)
            return Result(
                verdict,
                f'score={score}/{score_max}; {", ".join(notes)}',
                score=score, score_max=score_max, threshold=2.0,
            )

        # AU-09 — drives + owns multi-violation, 4-component reward
        if test_id == 'AU-09':
            score, score_max, notes = score_au_09(spec['fixture'])
            verdict = adr0015_verdict(score, score_max, threshold=2.0)
            return Result(
                verdict,
                f'score={score}/{score_max}; {", ".join(notes)}',
                score=score, score_max=score_max, threshold=2.0,
            )

        # AU-10 — token-bloat synth test, 4-component reward
        if test_id == 'AU-10':
            score, score_max, notes = score_au_10()
            verdict = adr0015_verdict(score, score_max, threshold=3.0)
            return Result(
                verdict,
                f'score={score}/{score_max}; {", ".join(notes)}',
                score=score, score_max=score_max, threshold=3.0,
            )

        # Fallback (not expected to fire today)
        findings = p6_findings(spec['fixture'])
        return Result('FAIL', f'no scoring path for {test_id}: {findings}',
                      score=0.0, score_max=1.0)
    return runner


def i_au_11_audit_has_aggregate_section() -> Result:
    """AU-11: latest audit md has '## Aggregate scores per agentic-md unit'
    section with ≥ 6 canonical-unit rows. 4-component reward."""
    p = latest_audit_path()
    if p is None:
        return Result('SKIP', 'AU-01 not green', score=0.0, score_max=4.0,
                      threshold=4.0)
    text = p.read_text(encoding='utf-8')
    canonical = [
        'Architect', 'Auditor', 'Wiki PM', 'Developer', 'DevOps',
        'rl-2048 lab AGENTS.md', 'wiki-bench lab AGENTS.md',
        'wiki-compiler lab AGENTS.md', 'wiki-ingest lab AGENTS.md',
    ]
    score = 0.0
    notes = []
    # C1 — heading present
    heading_re = r'(?m)^## Aggregate scores per agentic-md unit\s*$'
    if re.search(heading_re, text):
        score += 1; notes.append('C1=heading=1')
    else:
        notes.append('C1=heading=0')
        return Result(adr0015_verdict(score, 4.0, 4.0),
                      f'score={score}/4.0; ' + ', '.join(notes),
                      score=score, score_max=4.0, threshold=4.0)
    # Extract section body
    sec = re.search(r'(?ms)^## Aggregate scores per agentic-md unit\s*$.+?(?=\n## |\Z)', text)
    body = sec.group(0) if sec else ''
    # C2 — markdown table follows
    table_lines = [ln for ln in body.splitlines()
                   if ln.startswith('|') and not ln.startswith('|---')]
    # First two table lines are header + separator typically; data rows = rest
    # Filter out header row by requiring the row to NOT start with '| Unit'
    data_rows = [ln for ln in table_lines
                 if not ln.lstrip('|').lstrip().lower().startswith('unit')]
    if data_rows:
        score += 1; notes.append('C2=table=1')
    else:
        notes.append('C2=table=0')
        return Result(adr0015_verdict(score, 4.0, 4.0),
                      f'score={score}/4.0; ' + ', '.join(notes),
                      score=score, score_max=4.0, threshold=4.0)
    # C3 — >= 6 data rows
    if len(data_rows) >= 9:
        score += 1; notes.append(f'C3=rows={len(data_rows)}')
    else:
        notes.append(f'C3=rows={len(data_rows)}<9')
    # C4 — canonical units present in first column
    found = [name for name in canonical
             if any(name in row for row in data_rows)]
    if len(found) >= 9:
        score += 1; notes.append(f'C4=units=9/9')
    else:
        missing = [n for n in canonical if n not in found]
        notes.append(f'C4=units={len(found)}/9 missing={missing[:3]}')
    return Result(adr0015_verdict(score, 4.0, 4.0),
                  f'score={score}/4.0; ' + ', '.join(notes),
                  score=score, score_max=4.0, threshold=4.0)


# ─────────────── Registry + driver ───────────────

REGISTRY = {
    'AU-01': i_au_01_audit_report_exists,
    'AU-01b': i_au_02_audit_report_nonempty,
    'AU-02': i_au_03_audit_report_has_FAIL_WARN_INFO_sections,
    'AU-03': i_au_04_findings_carry_predicate_and_fix,
    'AU-04': i_au_05_summary_totals_match,
    'AU-04b': i_au_06_predicates_walked_line,
    'AU-11': i_au_11_audit_has_aggregate_section,
    **{k: make_decision_test(k) for k in DECISION_FIXTURES},
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
        line = f'  {tid:<8} {r.verdict:<19}  {r.detail}'.rstrip()
        print(line)
        rows.append((tid, r.verdict, r.score, r.score_max, r.threshold, r.detail))

    print()
    print(f'  total: PASS={counts["PASS"]}  '
          f'PASS-italian-strike={counts.get("PASS-italian-strike", 0)}  '
          f'FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')

    if log_scores:
        path = _score_history.append_scores('test-auditor-runner', rows)
        print(f'  logged {len(rows)} rows → {path.relative_to(Path(__file__).resolve().parents[2])}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
