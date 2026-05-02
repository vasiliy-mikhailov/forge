#!/usr/bin/env python3
"""Contribution report — for each in-scope artifact, classify:

  - Live              (citation is runner / lab-tests / audit-predicate /
                       catalog-row / experiment-closure / corpus-walk /
                       customer-cycle — directly measurable)
  - Carrying          (n/a — declarative AND >= 1 inbound reference from a
                       Live or Carrying artifact — load-bearing infra)
  - Orphan            (n/a — declarative AND 0 inbound references —
                       no Live artifact depends on it)
  - Stale-pending     (n/a — pending — placeholder for an unstarted artifact;
                       per delete-on-promotion shouldn't exist until R-NN
                       demands it)

Usage:
    python3 scripts/test-runners/contribution-report.py
    python3 scripts/test-runners/contribution-report.py --orphans-only
    python3 scripts/test-runners/contribution-report.py --json

Per ADR 0020 (queued) + P27 (queued): an artifact landing in forge that
classifies Orphan / Stale-pending = FAIL.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history  # noqa: E402

FORGE = Path(__file__).resolve().parents[2]

SCOPED_DIRS = ['phase-a-architecture-vision', 'phase-b-business-architecture',
               'phase-c-information-systems-architecture',
               'phase-d-technology-architecture',
               'phase-e-opportunities-and-solutions',
               'phase-f-migration-planning',
               'phase-g-implementation-governance',
               'phase-h-architecture-change-management',
               'phase-preliminary',
               'phase-requirements-management',
               'tests',
               'scripts']

LINK_RE = re.compile(r'\[[^\]]*\]\(([^)#]+?)(?:#[^)]*)?\)')


def list_md_artifacts():
    """Yield every .md file under scoped dirs (audit + script files included
    so cross-references are discoverable)."""
    out = []
    for d in SCOPED_DIRS:
        full_d = FORGE / d
        if not full_d.exists():
            continue
        for root, _, files in os.walk(full_d):
            for fn in files:
                if not fn.endswith('.md'):
                    continue
                if fn in ('CLAUDE.md',):
                    continue
                p = Path(root) / fn
                rel = str(p.relative_to(FORGE))
                # Skip standard carve-outs
                if any(s in rel for s in ['/.agents/']):
                    continue
                out.append(rel)
    return sorted(out)


def find_chain(text):
    """Find the **Outcome**:-bearing motivation chain (if any)."""
    matches = list(re.finditer(r'(?ms)^## Motivation(?: chain)?\s*$.+?(?=\n## |\Z)', text))
    if matches:
        for m in matches:
            if '**Outcome**:' in m.group(0):
                return m.group(0)
        return matches[0].group(0)
    return None


def extract_citation(chain_text):
    if not chain_text:
        return None
    m = re.search(r'\*\*Measurement source\*\*:\s*([^\n]+)', chain_text)
    if not m:
        return None
    return m.group(1).strip()


def is_transitive(text):
    return bool(re.search(r'(?:^|\n)(?:Transitive coverage:|\*\*Transitive coverage\*\*)', text))


def citation_band(citation):
    """Classify a citation string as Live / NA-declarative / NA-pending / Unknown."""
    if not citation:
        return 'Unknown'
    cit = citation.strip()
    if cit.startswith('n/a'):
        if 'declarative' in cit:
            return 'NA-declarative'
        if 'pending' in cit:
            return 'NA-pending'
        return 'NA-other'
    for prefix in ('runner:', 'runner-aggregate:', 'lab-tests:', 'audit-predicate:',
                   'catalog-row:', 'experiment-closure:', 'corpus-walk:', 'customer-cycle:'):
        if cit.startswith(prefix):
            return 'Live'
    return 'Unknown'


def resolve_link(target, source_path):
    """Resolve a relative markdown link to a path relative to FORGE."""
    if target.startswith('http://') or target.startswith('https://'):
        return None
    if target.startswith('mailto:'):
        return None
    src = (FORGE / source_path).parent
    try:
        resolved = (src / target).resolve()
    except (OSError, ValueError):
        return None
    try:
        rel = resolved.relative_to(FORGE)
    except ValueError:
        return None
    return str(rel)


def collect_inbound(artifacts):
    """Walk every md file (including audits/scripts/tests) and tally inbound refs
    per scoped artifact."""
    inbound = defaultdict(set)
    # Walk EVERYTHING in forge for outbound links so we don't miss cross-cites
    for root, _, files in os.walk(FORGE):
        for fn in files:
            if not fn.endswith('.md'):
                continue
            p = Path(root) / fn
            try:
                rel = str(p.relative_to(FORGE))
            except ValueError:
                continue
            if rel.startswith('.git/'):
                continue
            try:
                text = p.read_text(encoding='utf-8')
            except Exception:
                continue
            for target in LINK_RE.findall(text):
                resolved = resolve_link(target, rel)
                if resolved and resolved in artifacts and resolved != rel:
                    inbound[resolved].add(rel)
    return inbound


def classify_contribution(rel, citation_band_value, inbound_count, transitive):
    """Return 'Live' / 'Carrying' / 'Orphan' / 'Stale-pending' / 'Transitive'."""
    if transitive:
        return 'Transitive'
    if citation_band_value == 'Live':
        return 'Live'
    if citation_band_value == 'NA-pending':
        return 'Stale-pending'
    if citation_band_value == 'NA-declarative':
        if inbound_count >= 1:
            return 'Carrying'
        return 'Orphan'
    if citation_band_value == 'NA-other':
        return 'Orphan'
    # No measurement source line at all — file is out-of-scope for ADR 0019
    # (audit md, script docs). Treat as auxiliary; not counted in prune list.
    return 'Auxiliary'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--orphans-only', action='store_true')
    ap.add_argument('--prune-candidates', action='store_true',
                    help='Show only Orphan + Stale-pending rows')
    args = ap.parse_args()

    # In-scope = the same set the motivation-measurability-report walks
    # (phases A-G + preliminary). Audit md / scripts / tests are auxiliary.
    in_scope_dirs = ['phase-a-architecture-vision', 'phase-b-business-architecture',
                     'phase-c-information-systems-architecture',
                     'phase-d-technology-architecture',
                     'phase-e-opportunities-and-solutions',
                     'phase-f-migration-planning',
                     'phase-g-implementation-governance',
                     'phase-preliminary']

    rows = []
    artifacts = []
    artifact_meta = {}
    for rel in list_md_artifacts():
        if not any(rel.startswith(d + '/') for d in in_scope_dirs):
            continue
        # Skip carve-outs from P24 scope
        fn = Path(rel).name
        if fn in ('README.md', '_template.md', 'CLAUDE.md'):
            continue
        if any(s in rel for s in ['/.agents/', '/tests/synthetic/fixtures/']):
            continue
        text = (FORGE / rel).read_text(encoding='utf-8')
        chain = find_chain(text)
        citation = extract_citation(chain) if chain else None
        transitive = is_transitive(text)
        artifacts.append(rel)
        artifact_meta[rel] = {
            'citation': citation,
            'band': citation_band(citation),
            'transitive': transitive,
        }

    inbound = collect_inbound(set(artifacts))

    for rel in artifacts:
        meta = artifact_meta[rel]
        in_count = len(inbound.get(rel, []))
        contrib = classify_contribution(rel, meta['band'], in_count, meta['transitive'])
        rows.append({
            'path': rel,
            'citation': meta['citation'] or '(none)',
            'band': meta['band'],
            'inbound_count': in_count,
            'inbound_from': sorted(inbound.get(rel, []))[:5],
            'contribution': contrib,
        })

    if args.orphans_only or args.prune_candidates:
        rows = [r for r in rows if r['contribution'] in ('Orphan', 'Stale-pending')]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    # Markdown report
    out = ['# Contribution report',
           '',
           f'Walked {len(artifacts)} in-scope artifacts. ',
           f'Per ADR 0020 (queued) + P27 (queued): every artifact MUST be Live or Carrying.',
           '']

    # Counts by band
    counts = defaultdict(int)
    for r in rows:
        counts[r['contribution']] += 1
    if not (args.orphans_only or args.prune_candidates):
        out.append('## Bands')
        out.append('')
        out.append('| Band | Count |')
        out.append('|---|---|')
        for band in ('Live', 'Carrying', 'Transitive', 'Orphan', 'Stale-pending', 'Auxiliary'):
            out.append(f'| {band} | {counts.get(band, 0)} |')
        out.append('')

    if args.orphans_only or args.prune_candidates:
        out.append(f'**Prune candidates**: {len(rows)} artifacts (Orphan + Stale-pending)')
        out.append('')

    out.append('| Artifact | Inbound | Citation | Band |')
    out.append('|---|---|---|---|')
    for r in rows:
        cit = (r['citation'] or '')[:60]
        out.append(f'| `{r["path"]}` | {r["inbound_count"]} | {cit} | **{r["contribution"]}** |')

    print('\n'.join(out))


if __name__ == '__main__':
    main()
