#!/usr/bin/env python3
"""Quality report — pre-production bug-catch share + incidents trend.

Per ADR 0021:
    pre_prod_share = pre_prod_catches / (pre_prod_catches + incidents)

Where:
    pre_prod_catches = audit FAIL + WARN findings under
        phase-h-architecture-change-management/audit-*.md
    incidents = ***-separated entries in
        phase-g-implementation-governance/postmortems.md

Window: rolling 30-day (configurable via --window).

Per ADR 0019 + ADR 0021 § Decision 4 (P28): an ADR / artifact whose
Outcome reduces a class of incidents MUST cite
`**Measurement source**: quality-ledger: <metric>` (where metric is one
of `pre_prod_share` / `incident_count`). Run with --predicate P28 to
walk for missing citations.

Usage:
    python3 scripts/test-runners/quality-report.py
    python3 scripts/test-runners/quality-report.py --window 30
    python3 scripts/test-runners/quality-report.py --json
    python3 scripts/test-runners/quality-report.py --predicate P28
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

FORGE = Path(__file__).resolve().parents[2]
AUDITS_DIR = FORGE / 'phase-h-architecture-change-management'
POSTMORTEMS = FORGE / 'phase-g-implementation-governance' / 'postmortems.md'

AUDIT_RE = re.compile(r'^audit-(\d{4}-\d{2}-\d{2})([a-z]?)\.md$')


def parse_audit_date(fn):
    m = AUDIT_RE.match(fn)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), '%Y-%m-%d').date()
    except ValueError:
        return None


def count_findings_in_audit(text):
    """Count FAIL + WARN findings in an audit md file.

    Heuristic: each `### F<N>.` heading under `## Findings — verdict FAIL`
    or `## Findings — verdict WARN` is one finding. We count by scanning
    section by section.
    """
    fails = 0
    warns = 0
    sections = re.split(r'(?m)^## ', text)
    for sec in sections:
        first_line = sec.split('\n', 1)[0]
        if 'verdict FAIL' in first_line:
            fails += len(re.findall(r'(?m)^### F\d+\.', sec))
        elif 'verdict WARN' in first_line:
            warns += len(re.findall(r'(?m)^### F\d+\.', sec))
    return fails, warns


def walk_audits(since=None):
    """Yield (audit_date, fails, warns, audit_path) per audit file."""
    out = []
    if not AUDITS_DIR.exists():
        return out
    for p in sorted(AUDITS_DIR.glob('audit-*.md')):
        d = parse_audit_date(p.name)
        if not d:
            continue
        if since and d < since:
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        fails, warns = count_findings_in_audit(text)
        out.append((d, fails, warns, str(p.relative_to(FORGE))))
    return out


def parse_postmortems(text):
    """Return list of (story_date, title, body_excerpt) per ***-separated entry.

    The file structure: top-level `## YYYY-MM-DD` day headings; within a
    day, `### Title` entries separated by `***`.
    """
    entries = []
    # Walk by day
    day_chunks = re.split(r'(?m)^## (\d{4}-\d{2}-\d{2})\s*$', text)
    # day_chunks alternates: [pre, date1, body1, date2, body2, ...]
    if len(day_chunks) < 3:
        return entries
    for i in range(1, len(day_chunks), 2):
        day_str = day_chunks[i]
        body = day_chunks[i + 1] if i + 1 < len(day_chunks) else ''
        try:
            day = datetime.strptime(day_str, '%Y-%m-%d').date()
        except ValueError:
            continue
        # Split body by *** delimiter (must be on own line)
        stories = re.split(r'(?m)^\*\*\*\s*$', body)
        for story in stories:
            # Find the title: first `### ` heading
            m = re.search(r'(?m)^### (.+)$', story)
            if not m:
                continue
            title = m.group(1).strip()
            # Skip "How to write an entry" carve-out
            if 'How to write an entry' in title:
                continue
            excerpt = story[:200].strip()
            entries.append({'date': day.isoformat(), 'title': title,
                            'excerpt_first200': excerpt})
    return entries


def compute_share(audits_in_window, incidents_in_window):
    pre_prod = sum(f + w for _, f, w, _ in audits_in_window)
    incidents = len(incidents_in_window)
    total = pre_prod + incidents
    if total == 0:
        return None, pre_prod, incidents
    return pre_prod / total, pre_prod, incidents


def predicate_p28_walk():
    """Walk every motivation chain in scope; flag any whose Outcome
    suggests quality-affecting decision but lacks `quality-ledger:` citation.

    Heuristic phrases that suggest quality-affecting:
      'fewer production', 'match production', 'rebuild before',
      'stale image', 'single source of truth', 'completeness over',
      'cheap experiment', 'data outside git', 'monorepo', 'NFC', 'NFD',
      'cross-platform', 'silent skip'.
    """
    triggers = [r'fewer\s+production', r'match\s+production', r'rebuild\s+before',
                r'stale\s+image', r'single\s+source\s+of\s+truth',
                r'completeness\s+over', r'cheap\s+experiment',
                r'data\s+outside\s+git', r'monorepo', r'NFC', r'NFD',
                r'cross-platform', r'silent\s+skip']
    pat = re.compile('|'.join(triggers), re.IGNORECASE)
    SCOPED = ['phase-a-architecture-vision', 'phase-b-business-architecture',
              'phase-c-information-systems-architecture',
              'phase-d-technology-architecture',
              'phase-e-opportunities-and-solutions',
              'phase-f-migration-planning',
              'phase-g-implementation-governance',
              'phase-preliminary']
    failures = []
    for d in SCOPED:
        full_d = FORGE / d
        if not full_d.exists():
            continue
        for p in full_d.rglob('*.md'):
            if p.name in ('README.md', '_template.md', 'CLAUDE.md'):
                continue
            text = p.read_text(encoding='utf-8')
            chain_m = re.search(r'(?ms)^## Measurable motivation chain \(OKRs\)\s*$.+?(?=\n## |\Z)', text)
            if not chain_m:
                continue
            chain = chain_m.group(0)
            # Scan only the **Outcome** bullet (and its continuation lines),
            # not the whole chain — Capability / Driver lines often mention
            # quality-shaped phrases incidentally.
            outcome_m = re.search(r'(?:- )?\*\*Outcome\*\*:\s*([^\n]+(?:\n  [^\n]+)*)', chain)
            outcome_text = outcome_m.group(1) if outcome_m else ''
            # Also accept code-block format (Outcome: text)
            if not outcome_text:
                cb_m = re.search(r'^Outcome:\s*(.+?)(?=^[A-Z][a-z]+:|\Z)', chain, re.MULTILINE | re.DOTALL)
                outcome_text = cb_m.group(1) if cb_m else ''
            if not pat.search(outcome_text):
                continue
            ms = re.search(r'\*\*Measurement source\*\*:\s*([^\n]+)', chain)
            if ms and 'quality-ledger:' in ms.group(1):
                continue
            rel = str(p.relative_to(FORGE))
            failures.append({'path': rel,
                             'cited': ms.group(1).strip() if ms else '(none)',
                             'trigger_match': pat.search(chain).group(0)})
    return failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', type=int, default=30,
                    help='Rolling window in days (default 30)')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--predicate', choices=['P28'],
                    help='Walk a specific predicate (P28 = quality-ledger citation)')
    args = ap.parse_args()

    if args.predicate == 'P28':
        failures = predicate_p28_walk()
        if args.json:
            print(json.dumps(failures, ensure_ascii=False, indent=2))
        else:
            print(f'P28 walk: {len(failures)} chain(s) need quality-ledger citation')
            for f in failures:
                print(f'  FAIL  {f["path"]}')
                print(f'        cited:    {f["cited"][:80]}')
                print(f'        trigger:  {f["trigger_match"]}')
        sys.exit(1 if failures else 0)

    today = date.today()
    since = today - timedelta(days=args.window)

    # All-time
    all_audits = walk_audits()
    pm_text = POSTMORTEMS.read_text(encoding='utf-8') if POSTMORTEMS.exists() else ''
    all_incidents = parse_postmortems(pm_text)

    # In-window
    audits_w = [a for a in all_audits if a[0] >= since]
    incidents_w = [i for i in all_incidents if i['date'] >= since.isoformat()]

    share_w, pre_prod_w, inc_w = compute_share(audits_w, incidents_w)
    share_a, pre_prod_a, inc_a = compute_share(all_audits, all_incidents)

    if args.json:
        out = {
            'window_days': args.window,
            'window_start': since.isoformat(),
            'window_end': today.isoformat(),
            'rolling': {
                'pre_prod_catches': pre_prod_w,
                'incidents': inc_w,
                'pre_prod_share': share_w,
            },
            'all_time': {
                'pre_prod_catches': pre_prod_a,
                'incidents': inc_a,
                'pre_prod_share': share_a,
            },
            'audits_walked': len(all_audits),
            'incidents_logged': len(all_incidents),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f'# Quality report')
    print()
    print(f'Window: {args.window}-day rolling, {since} → {today}.')
    print(f'Audits walked: {len(all_audits)}; incidents logged: {len(all_incidents)}.')
    print()
    print('## Rolling window')
    print()
    print(f'- pre-prod catches: **{pre_prod_w}** (FAIL + WARN audit findings)')
    print(f'- incidents:        **{inc_w}** (postmortems entries)')
    if share_w is None:
        print(f'- pre_prod_share:   n/a (no data in window)')
    else:
        print(f'- pre_prod_share:   **{share_w:.3f}**  ({pre_prod_w} / {pre_prod_w + inc_w})')
    print()
    print('## All-time')
    print()
    print(f'- pre-prod catches: **{pre_prod_a}**')
    print(f'- incidents:        **{inc_a}**')
    if share_a is None:
        print(f'- pre_prod_share:   n/a')
    else:
        print(f'- pre_prod_share:   **{share_a:.3f}**')
    print()
    if args.window <= 30 and incidents_w:
        print('## Incidents in window')
        print()
        for i in incidents_w[-10:]:
            print(f'- `{i["date"]}` — {i["title"]}')


if __name__ == '__main__':
    main()
