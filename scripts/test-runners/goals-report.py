#!/usr/bin/env python3
"""Goals report — top-level OKR cascade status.

Per ADR 0023:
  - Reads phase-a/goals.md for the 5 Goal rows + their KR targets.
  - Computes current values:
      TTS              — pending until CI cycle measurement harness lands
      PTS              — pending until cohort engagement telemetry lands
      EB               — pending until eb-report.py
      Architect-velocity — counts *Taken:* lines in postmortems +
                           closed FAIL/WARN findings in audits in window
      Quality          — defers to quality-report.py
  - Emits one row per Goal with Target / Current / Band.
  - --predicate P29 walks all chains for cascade-integrity check.

Usage:
    python3 scripts/test-runners/goals-report.py
    python3 scripts/test-runners/goals-report.py --window 30
    python3 scripts/test-runners/goals-report.py --json
    python3 scripts/test-runners/goals-report.py --predicate P29
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

FORGE = Path(__file__).resolve().parents[2]
GOALS = FORGE / 'phase-a-architecture-vision' / 'goals.md'
POSTMORTEMS = FORGE / 'phase-g-implementation-governance' / 'postmortems.md'
AUDITS_DIR = FORGE / 'phase-h-architecture-change-management'

NAMED_GOALS = {'TTS', 'PTS', 'EB', 'Architect-velocity', 'Quality'}

AUDIT_RE = re.compile(r'^audit-(\d{4}-\d{2}-\d{2})([a-z]?)\.md$')


def count_corrective_actions(window_days):
    """Architect-velocity KR: *Taken:* lines (postmortems) + closed
    FAIL/WARN findings (audits) within window."""
    today = date.today()
    since = today - timedelta(days=window_days)
    count = 0
    # Postmortems: count *Taken: ...* italicised lines
    if POSTMORTEMS.exists():
        text = POSTMORTEMS.read_text(encoding='utf-8')
        # Walk by day heading; count *Taken:* lines per day; sum within window
        day_chunks = re.split(r'(?m)^## (\d{4}-\d{2}-\d{2})\s*$', text)
        for i in range(1, len(day_chunks), 2):
            try:
                d = datetime.strptime(day_chunks[i], '%Y-%m-%d').date()
            except ValueError:
                continue
            if d < since:
                continue
            body = day_chunks[i + 1] if i + 1 < len(day_chunks) else ''
            count += len(re.findall(r'\*Taken:', body))
    # Audits: count FAIL + WARN findings closed in audits within window
    for p in sorted(AUDITS_DIR.glob('audit-*.md')):
        m = AUDIT_RE.match(p.name)
        if not m:
            continue
        try:
            d = datetime.strptime(m.group(1), '%Y-%m-%d').date()
        except ValueError:
            continue
        if d < since:
            continue
        text = p.read_text(encoding='utf-8')
        # Count FAIL + WARN finding sections; each closed finding is a corrective action
        for sec in re.split(r'(?m)^## ', text):
            first = sec.split('\n', 1)[0]
            if 'verdict FAIL' in first or 'verdict WARN' in first:
                count += len(re.findall(r'(?m)^### F\d+\.', sec))
    return count


def quality_share():
    """Defer to quality-report.py for current pre_prod_share."""
    try:
        res = subprocess.run(
            ['python3', str(Path(__file__).parent / 'quality-report.py'),
             '--json', '--window', '365'],
            capture_output=True, text=True, check=True, cwd=str(FORGE))
        return json.loads(res.stdout)['rolling']['pre_prod_share']
    except Exception:
        return None


def band_for(metric, current, target):
    """Return PASS / italian-strike / FAIL / pending."""
    if current is None:
        return 'pending'
    if current >= target:
        return 'PASS'
    if current >= 0.75 * target:
        return 'italian-strike'
    return 'FAIL'


def goals_report(window):
    quality = quality_share()
    actions = count_corrective_actions(window)
    rows = [
        {'goal': 'TTS', 'kr': 'tts_share ≥ 0.30', 'target': 0.30,
         'current': None, 'note': 'pending TTS harness (CI cycle)'},
        {'goal': 'PTS', 'kr': 'pts_share ≥ 0.30', 'target': 0.30,
         'current': None, 'note': 'pending cohort engagement telemetry'},
        {'goal': 'EB', 'kr': 'unit_economics ≥ 1.0', 'target': 1.0,
         'current': None, 'note': 'pending eb-report.py'},
        {'goal': 'Architect-velocity',
         'kr': f'≥ 50 corrective actions / {window}-day rolling',
         'target': 50,
         'current': actions,
         'note': f'{actions} actions in last {window} days'},
        {'goal': 'Quality', 'kr': 'pre_prod_share ≥ 0.95', 'target': 0.95,
         'current': quality,
         'note': f'{quality:.3f} (365-day window)' if quality is not None else 'n/a'},
    ]
    for r in rows:
        r['band'] = band_for(r['goal'], r['current'], r['target'])
    return rows


def predicate_p29_walk():
    """Walk every chain in scope; verify **Goal**: bullet cites
    one of the 5 named Goals."""
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
            chain_matches = list(re.finditer(
                r'(?ms)^## Measurable motivation chain \(OKRs\)\s*$.+?(?=\n## |\Z)',
                text))
            if not chain_matches:
                continue
            # Pick the section with **Outcome**: bullet (the actual chain)
            chain = None
            for cm in chain_matches:
                if '**Outcome**:' in cm.group(0):
                    chain = cm.group(0)
                    break
            if chain is None:
                chain = chain_matches[0].group(0)
            # Look for **Goal**: bullet
            goal_m = re.search(r'(?:- )?\*\*Goal\*\*:\s*([^\n]+)', chain)
            if not goal_m:
                # No Goal bullet at all — older code-block format roles
                # use `Goal:` (no asterisks). Tolerate.
                cb_m = re.search(r'^Goal:\s*([^\n]+)', chain, re.MULTILINE)
                if cb_m:
                    goal_text = cb_m.group(1)
                else:
                    failures.append({'path': str(p.relative_to(FORGE)),
                                     'reason': 'no Goal bullet found',
                                     'cited': '(none)'})
                    continue
            else:
                goal_text = goal_m.group(1)
            # Verify cites one of 5 named Goals
            cited_goals = [g for g in NAMED_GOALS
                           if re.search(rf'\b{re.escape(g)}\b', goal_text)]
            if not cited_goals:
                failures.append({'path': str(p.relative_to(FORGE)),
                                 'reason': 'no named Goal cited',
                                 'cited': goal_text.strip()[:80]})
            elif len(cited_goals) > 1:
                # Allowed to mention multiple in prose (e.g. "Architect-velocity (Phase A) — see also Quality")
                # Not a failure unless intent is unclear; tolerate.
                pass
    return failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', type=int, default=30)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--predicate', choices=['P29'])
    args = ap.parse_args()

    if args.predicate == 'P29':
        failures = predicate_p29_walk()
        if args.json:
            print(json.dumps(failures, ensure_ascii=False, indent=2))
        else:
            print(f'P29 walk: {len(failures)} chain(s) need named-Goal citation')
            for f in failures:
                print(f'  FAIL  {f["path"]}')
                print(f'        reason: {f["reason"]}')
                print(f'        cited:  {f["cited"]}')
        sys.exit(1 if failures else 0)

    rows = goals_report(args.window)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    print('# Goals report — top-level OKR cascade status')
    print()
    print(f'Window: {args.window}-day rolling.')
    print()
    print('| Goal | KR | Target | Current | Band |')
    print('|------|----|----|---------|------|')
    for r in rows:
        cur = f'{r["current"]:.3f}' if isinstance(r['current'], float) else (str(r['current']) if r['current'] is not None else 'n/a')
        print(f'| **{r["goal"]}** | {r["kr"]} | {r["target"]} | {cur} | **{r["band"]}** |')
    print()
    print('## Notes')
    for r in rows:
        if r.get('note'):
            print(f'- **{r["goal"]}**: {r["note"]}')


if __name__ == '__main__':
    main()
