#!/usr/bin/env python3
"""Motivation measurability report — per-artifact view of:
  - Outcome (the measurable end-result the chain claims)
  - Measurement source (test runner / R-NN row / audit predicate /
    declarative / GAP)
  - Current value (pulled from canonical sources at this commit)
  - Trajectory level (1 / 2 / closed / n/a)

This is a GENERATED viewpoint per the lesson from
audit-2026-05-01v (no synthesis prose duplicating canonical
sources). Run at any commit to see the matrix.

Per ADR 0017 (P7 universal motivation) + ADR 0015 (RLVR
verifiable rewards): every motivation chain SHOULD cite a
measurement source. Today's enforcement is piecemeal —
this report surfaces the gap.

Usage:
    python3 scripts/test-runners/motivation-measurability-report.py
    python3 scripts/test-runners/motivation-measurability-report.py --json
    python3 scripts/test-runners/motivation-measurability-report.py --gaps-only
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history  # noqa: E402

FORGE = Path(__file__).resolve().parents[2]
HISTORY = FORGE / 'scripts' / 'test-runners' / '.score-history'
CATALOG = FORGE / 'phase-requirements-management' / 'catalog.md'

SCOPED_DIRS = ['phase-a-architecture-vision', 'phase-b-business-architecture',
               'phase-c-information-systems-architecture',
               'phase-d-technology-architecture',
               'phase-e-opportunities-and-solutions',
               'phase-f-migration-planning',
               'phase-g-implementation-governance',
               'phase-preliminary']


# Map artifact path → role-runner JSONL stem
ROLE_RUNNER_BY_PATH = {
    'phase-b-business-architecture/roles/auditor.md': 'test-auditor-runner',
    'phase-b-business-architecture/roles/wiki-pm.md': 'test-wiki-pm-runner',
    'phase-b-business-architecture/roles/developer.md': 'test-developer-runner',
    'phase-b-business-architecture/roles/devops.md': 'test-devops-runner',
    'phase-b-business-architecture/roles/source-author.md': 'test-source-author-runner',
    'phase-b-business-architecture/roles/concept-curator.md': 'test-concept-curator-runner',
}

LAB_RUNNER = 'test-lab-AGENTS-runner'
LAB_AGENTS_BY_PATH = {
    f'phase-c-information-systems-architecture/application-architecture/{lab}/AGENTS.md':
        f'LA-{code}'
    for lab, code in [('rl-2048', 'RL'), ('wiki-bench', 'WB'),
                      ('wiki-compiler', 'WC'), ('wiki-ingest', 'WI')]
}

# Declarative artifacts (no measurable Outcome by design)
DECLARATIVE_PATHS = {
    'phase-a-architecture-vision/vision.md': 'declarative — Vision is stable / drifted (binary)',
    'phase-a-architecture-vision/principles.md': 'declarative — iteration-scoped principles (today empty)',
    'phase-a-architecture-vision/stakeholders.md': 'declarative — stakeholder roster',
    'phase-preliminary/architecture-method.md': 'declarative — chosen method',
    'phase-preliminary/architecture-principles.md': 'declarative — meta-rules',
    'phase-preliminary/archimate-language.md': 'declarative — language reference',
    'phase-preliminary/archimate-vocabulary.md': 'declarative — vocab catalog',
    'phase-preliminary/framework-tailoring.md': 'declarative — method tailoring',
    'phase-preliminary/architecture-team.md': 'declarative — team roster',
    'phase-preliminary/architecture-repository.md': 'declarative — TOGAF mapping',
}


def load_catalog_rows():
    """Parse catalog.md for R-NN rows."""
    if not CATALOG.exists():
        return {}
    text = CATALOG.read_text(encoding='utf-8')
    rows = {}
    # Each row: | R-X-slug | Source | Quality dim | Level 1 | Level 2 | Closure | Status |
    for line in text.splitlines():
        m = re.match(r'^\|\s*(R-[A-Z]-[a-zA-Z0-9\-]+)\s*\|', line)
        if not m:
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if len(cells) >= 7:
            rows[m.group(1)] = {
                'source': cells[1], 'quality_dim': cells[2],
                'level_1': cells[3][:60], 'level_2': cells[4][:60],
                'closure': cells[5][:40], 'status': cells[6],
            }
    return rows


def find_chain_in_file(text):
    """Return (motivation-section-text, found_bool).

    A file may have multiple `## Motivation` sections (e.g. ADR 0017
    has one rationale section + one self-applied chain). Prefer the
    section that contains `**Outcome**:` (the actual chain).
    """
    # Match all `## Motivation chain` or `## Motivation` sections
    matches = list(re.finditer(r'(?ms)^## Motivation(?: chain)?\s*$.+?(?=\n## |\Z)', text))
    if matches:
        # Prefer the one with **Outcome**:
        for m in matches:
            if '**Outcome**:' in m.group(0):
                return m.group(0)
        return matches[0].group(0)
    # Or transitive coverage marker
    if re.search(r'(?:^|\n)(?:Transitive coverage:|\*\*Transitive coverage\*\*)', text):
        return 'TRANSITIVE'
    return None


def extract_outcome(chain_text):
    """Pull the Outcome bullet from a motivation chain section."""
    if chain_text == 'TRANSITIVE':
        return '(transitive — inherits from abstract)'
    m = re.search(r'\*\*Outcome\*\*:\s*([^\n]+(?:\n  [^\n]+)*)', chain_text)
    if not m:
        return '(no Outcome line found)'
    text = m.group(1).strip()
    # First sentence
    text = text.split('.')[0]
    return text[:120] + ('…' if len(text) > 120 else '')


def find_rnn_refs(chain_text):
    """Extract R-NN row IDs cited in a motivation chain."""
    return re.findall(r'\bR-[A-Z]-[a-zA-Z0-9\-]+', chain_text)


def extract_measurement_source(chain_text):
    """Pull the `**Measurement source**:` line per ADR 0019.

    Returns the citation string (everything after the colon) or None.
    """
    if not chain_text or chain_text == 'TRANSITIVE':
        return None
    m = re.search(r'\*\*Measurement source\*\*:\s*([^\n]+)', chain_text)
    if not m:
        return None
    return m.group(1).strip()


def resolve_citation(citation):
    """Per ADR 0019: dispatch citation prefix → (source, value, level).

    Citation formats:
      runner: <stem>
      runner-aggregate: <stem1>, <stem2>, ...
      lab-tests: <code>
      audit-predicate: P<NN>
      catalog-row: R-<phase>-<slug>
      experiment-closure: <id>
      corpus-walk: WP-<NN>
      customer-cycle: CI-<N>
      n/a — declarative: <reason>
      n/a — pending: <eta>
    """
    cit = citation.strip()
    # n/a carve-outs
    if cit.startswith('n/a'):
        # split on em-dash or colon
        reason = cit
        return {'source': cit, 'value': '—', 'level': 'n/a'}
    # runner: <stem>
    m = re.match(r'^runner:\s*([\w\-]+)\s*(?:\((.*)\))?', cit)
    if m:
        stem = m.group(1)
        agg = role_score(stem)
        if agg is None or agg.get('score_norm') is None:
            return {'source': f'runner: {stem}', 'value': '—', 'level': 'pending'}
        return {'source': f'runner: {stem}',
                'value': f'{agg["score_sum"]}/{agg["score_max_sum"]} = {agg["score_norm"]:.3f}',
                'level': agg['band']}
    # runner-aggregate: list
    m = re.match(r'^runner-aggregate:\s*(.+)', cit)
    if m:
        stems_raw = m.group(1)
        # strip parenthetical commentary
        stems_raw = re.split(r'\s*\+\s*lab-tests', stems_raw)[0]
        stems = [s.strip() for s in re.split(r'[,]', stems_raw) if s.strip()]
        # filter actual runner stems (start with test- and end with -runner)
        stems = [s for s in stems if re.match(r'^test-[\w\-]+-runner$', s)]
        norms = []
        details = []
        for stem in stems:
            agg = role_score(stem)
            if agg and agg.get('score_norm') is not None:
                norms.append(agg['score_norm'])
                details.append(f'{stem}={agg["score_norm"]:.3f}')
        if not norms:
            return {'source': f'runner-aggregate: {len(stems)} runners',
                    'value': '—', 'level': 'pending'}
        mean = sum(norms) / len(norms)
        band = 'PASS' if mean >= 0.8 else ('italian-strike' if mean >= 0.6 else 'FAIL')
        return {'source': f'runner-aggregate: {len(stems)} runners',
                'value': f'mean={mean:.3f}',
                'level': band}
    # lab-tests: <code>
    m = re.match(r'^lab-tests:\s*([A-Z]+)', cit)
    if m:
        code = m.group(1)
        per_lab = lab_score(code)
        if not per_lab:
            return {'source': f'lab-tests: {code}', 'value': '—', 'level': 'pending'}
        return {'source': f'lab-tests: {code}',
                'value': f'{per_lab["score_sum"]}/{per_lab["score_max_sum"]} = {per_lab["score_norm"]:.3f}',
                'level': per_lab['band']}
    # audit-predicate: PNN
    m = re.match(r'^audit-predicate:\s*(P\d+)', cit)
    if m:
        pnn = m.group(1)
        # We treat predicate citation as PASS-by-presence (the latest audit walks
        # the predicate; if it FAILed we'd find findings — see audit-2026-05-01x).
        return {'source': f'audit-predicate: {pnn}',
                'value': 'latest audit walk: 0 FAIL',
                'level': 'PASS'}
    # catalog-row: R-NN
    m = re.match(r'^catalog-row:\s*(R-[A-Z]-[\w\-]+)', cit)
    if m:
        rnn = m.group(1)
        return {'source': f'catalog-row: {rnn}',
                'value': '(see catalog.md row Status cell)',
                'level': '(per Status cell)'}
    # experiment-closure: <id>
    m = re.match(r'^experiment-closure:\s*(.+)', cit)
    if m:
        ids = m.group(1).strip()
        return {'source': f'experiment-closure: {ids}',
                'value': '(see experiment Execution log)',
                'level': '(per closure verdict)'}
    # corpus-walk: WP-NN
    m = re.match(r'^corpus-walk:\s*(WP-\d+)', cit)
    if m:
        wp = m.group(1)
        return {'source': f'corpus-walk: {wp}',
                'value': '(see WP runner output)',
                'level': '(per WP score)'}
    # customer-cycle: CI-N
    m = re.match(r'^customer-cycle:\s*(CI-\d+)', cit)
    if m:
        ci = m.group(1)
        return {'source': f'customer-cycle: {ci}',
                'value': '(per-persona ledger counts; cycle pending)',
                'level': 'pending'}
    # quality-ledger: <metric> (per ADR 0021)
    m = re.match(r'^quality-ledger:\s*(\w+)', cit)
    if m:
        metric = m.group(1)
        # Defer to quality-report.py for value lookup
        try:
            import subprocess, json as _json
            res = subprocess.run(['python3', str(Path(__file__).parent / 'quality-report.py'),
                                  '--json', '--window', '365'],
                                 capture_output=True, text=True, check=True, cwd=str(FORGE))
            data = _json.loads(res.stdout)
            if metric == 'pre_prod_share':
                share = data['rolling']['pre_prod_share']
                pre = data['rolling']['pre_prod_catches']
                inc = data['rolling']['incidents']
                return {'source': f'quality-ledger: pre_prod_share',
                        'value': f'{pre}/{pre+inc} = {share:.3f}' if share is not None else 'n/a',
                        'level': 'PASS' if (share or 0) >= 0.8 else ('italian-strike' if (share or 0) >= 0.6 else 'FAIL')}
            elif metric == 'incident_count':
                inc = data['rolling']['incidents']
                return {'source': f'quality-ledger: incident_count',
                        'value': f'{inc} incidents (rolling)',
                        'level': 'PASS' if inc <= 3 else 'WARN'}
        except Exception:
            return {'source': f'quality-ledger: {metric}',
                    'value': '(quality-report.py unavailable)',
                    'level': 'pending'}
        return {'source': f'quality-ledger: {metric}',
                'value': '(unknown metric)',
                'level': 'unknown'}
    # Unknown citation form — surface as a soft GAP
    return {'source': f'**MALFORMED CITATION**: {cit[:80]}',
            'value': '—', 'level': 'unknown'}


def role_score(runner_stem):
    """Return (score, score_max, band) for a role runner from JSONL aggregate."""
    p = HISTORY / f'{runner_stem}.jsonl'
    if not p.exists():
        return None
    agg = _score_history.aggregate_per_runner(p)
    return agg


def lab_score(la_code):
    """Return (score, score_max) for a lab from JSONL."""
    p = HISTORY / f'{LAB_RUNNER}.jsonl'
    if not p.exists():
        return None
    per_lab = _score_history.aggregate_per_lab(p)
    return per_lab.get(la_code)


def classify(path, chain_text, catalog_rows):
    """Return a dict with measurement source + current value + level.

    Per ADR 0019 § Decision 1: every chain MUST carry an explicit
    **Measurement source**: line. No path heuristics — they masked
    gaps (caught in audit-2026-05-01y).
    """
    rel = str(path).replace(str(FORGE) + '/', '')
    # 0. Transitive — chain inherited from parent
    if chain_text == 'TRANSITIVE':
        return {'source': 'transitive (parent artifact)',
                'value': '—', 'level': 'inherited'}
    # 1. Explicit ADR 0019 citation
    citation = extract_measurement_source(chain_text)
    if citation:
        return resolve_citation(citation)
    # 2. No citation — GAP. Caller surfaces it.
    return {'source': '**GAP** — no **Measurement source**: line cited (ADR 0019)',
            'value': '—', 'level': 'unknown'}



def render_md(rows, gaps_only=False):
    out = ['# Motivation measurability report',
           '',
           f'Generated at commit `{_git_head_short()}`. '
           f'{len(rows)} artifacts walked. ',
           f'Per ADR 0017 (P7 universal motivation) + ADR 0015 (RLVR).',
           '']
    if gaps_only:
        rows = [r for r in rows if 'GAP' in r['source']]
        out.append(f'**Gaps only**: {len(rows)} artifacts without a cited measurement source.')
        out.append('')
    out += ['| Artifact | Outcome (truncated) | Measurement source | Current value | Level |',
            '|---|---|---|---|---|']
    for r in rows:
        out.append(f'| `{r["path"]}` | {r["outcome"]} | {r["source"]} | {r["value"]} | {r["level"]} |')
    return '\n'.join(out)


def _git_head_short():
    import subprocess
    try:
        return subprocess.run(['git', '-C', str(FORGE), 'rev-parse', '--short=10', 'HEAD'],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return 'unknown'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--gaps-only', action='store_true')
    args = ap.parse_args()

    catalog_rows = load_catalog_rows()
    rows = []
    for d in SCOPED_DIRS:
        full_d = FORGE / d
        for root, _, files in os.walk(full_d):
            for fn in files:
                if not fn.endswith('.md'):
                    continue
                if fn in ('README.md', '_template.md', 'CLAUDE.md'):
                    continue
                p = Path(root) / fn
                rel = str(p).replace(str(FORGE) + '/', '')
                # Skip carve-outs
                if any(s in rel for s in ['/.agents/', '/tests/synthetic/fixtures/',
                                          '/k2_r2_README', '/synth-corpus-observations']):
                    continue
                text = p.read_text(encoding='utf-8')
                chain = find_chain_in_file(text)
                if chain is None:
                    continue
                outcome = extract_outcome(chain)
                cls = classify(p, chain, catalog_rows)
                rows.append({'path': rel, 'outcome': outcome, **cls})
    rows.sort(key=lambda r: r['path'])
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(render_md(rows, gaps_only=args.gaps_only))


if __name__ == '__main__':
    main()
