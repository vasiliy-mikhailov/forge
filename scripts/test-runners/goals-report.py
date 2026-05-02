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


def count_architect_interventions(window_days):
    """Architect-velocity KR (per ADR 0024): count of architect interventions
    in window. LOWER = BETTER. Intervention = commit message starting with
    'ADR ' OR containing 'architect call' / 'per architect' / 'architect-deferred'.

    Honest caveat: in chat-driven workflow today, most commits trace to an
    architect prompt even if the message doesn't say so. The metric
    structurally undermeasures until commit-provenance tagging lands
    (per ADR 0024 follow-up #1)."""
    import subprocess
    try:
        log = subprocess.run(
            ['git', '-C', str(FORGE), 'log',
             f'--since={window_days} days ago', '--pretty=format:%s'],
            capture_output=True, text=True, check=True).stdout
    except Exception:
        return None
    if not log.strip():
        return 0
    # Per ADR 0024 (revised 2026-05-02): architecture changes (ADR landings)
    # are NOT execution failures — the architect changing architecture is
    # the architect's job. Only count architect-call markers when the
    # commit is NOT primarily an ADR landing.
    intervention_pat = re.compile(r'architect call|per architect|architect-deferred',
                                  re.IGNORECASE)
    adr_pat = re.compile(r'^ADR \d')
    count = 0
    for line in log.split('\n'):
        if not intervention_pat.search(line):
            continue
        if adr_pat.search(line):
            continue  # architecture change, not execution failure
        count += 1
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
    interventions = count_architect_interventions(window)
    rows = [
        {'goal': 'TTS', 'kr': 'tts_share ≥ 0.30', 'target': 0.30,
         'current': None, 'lower_better': False,
         'note': 'pending TTS harness (CI cycle)'},
        {'goal': 'PTS', 'kr': 'pts_share ≥ 0.30', 'target': 0.30,
         'current': None, 'lower_better': False,
         'note': 'pending cohort engagement telemetry'},
        {'goal': 'EB', 'kr': 'unit_economics ≥ 1.0', 'target': 1.0,
         'current': None, 'lower_better': False,
         'note': 'pending eb-report.py'},
        {'goal': 'Architect-velocity',
         'kr': f'≤ 20 architect interventions / {window}-day rolling',
         'target': 20,
         'current': interventions,
         'lower_better': True,
         'note': f'{interventions} interventions in last {window} days (commit-message detection; reality higher)'},
        {'goal': 'Quality', 'kr': 'pre_prod_share ≥ 0.95', 'target': 0.95,
         'current': quality,
         'lower_better': False,
         'note': f'{quality:.3f} (365-day window)' if quality is not None else 'n/a'},
    ]
    for r in rows:
        if r['current'] is None:
            r['band'] = 'pending'
        elif r['lower_better']:
            # Lower better: PASS if current ≤ target; italian if ≤ 1.5x; FAIL otherwise
            if r['current'] <= r['target']:
                r['band'] = 'PASS'
            elif r['current'] <= 1.5 * r['target']:
                r['band'] = 'italian-strike'
            else:
                r['band'] = 'FAIL'
        else:
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
                r'(?ms)^## Measurable motivation chain\s*$.+?(?=\n## |\Z)',
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



def predicate_p30_walk():
    """Per ADR 0025: every chain MUST have **Contribution**: bullet."""
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
                r'(?ms)^## Measurable motivation chain\s*$.+?(?=\n## |\Z)', text))
            chain = None
            for cm in chain_matches:
                if '**Outcome**:' in cm.group(0):
                    chain = cm.group(0); break
            if not chain:
                continue
            if '**Contribution**:' not in chain:
                failures.append({'path': str(p.relative_to(FORGE))})
    return failures

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--window', type=int, default=30)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--predicate', choices=['P29', 'P30'])
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

    if args.predicate == 'P30':
        failures = predicate_p30_walk()
        if args.json:
            print(json.dumps(failures, ensure_ascii=False, indent=2))
        else:
            print(f'P30 walk: {len(failures)} chain(s) need **Contribution**: bullet')
            for f in failures:
                print(f'  FAIL  {f["path"]}')
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
