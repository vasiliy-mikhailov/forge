#!/usr/bin/env python3
"""ADR 0015 dec 6 — print per-agentic-md-unit aggregate scores.

Reads all 3 score-history JSONL files; emits a markdown table the
architect pastes into the audit md under the section heading
`## Aggregate scores per agentic-md unit` (audited by P22 + AU-11).

Usage:
    python3 scripts/test-runners/aggregate-scores.py
    python3 scripts/test-runners/aggregate-scores.py --raw   # stdout JSON

The table covers 6 units (1 row per agentic-md the test suite covers):

    Auditor                       | …
    Wiki PM                       | …
    rl-2048 lab AGENTS.md         | …
    wiki-bench lab AGENTS.md      | …
    wiki-compiler lab AGENTS.md   | …
    wiki-ingest lab AGENTS.md     | …
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history as sh  # noqa: E402

HISTORY = Path(__file__).resolve().parent / '.score-history'

LAB_LABEL = {
    'RL': 'rl-2048',
    'WB': 'wiki-bench',
    'WC': 'wiki-compiler',
    'WI': 'wiki-ingest',
}


def gather() -> list[dict]:
    rows = []
    auditor = sh.aggregate_per_runner(HISTORY / 'test-auditor-runner.jsonl')
    auditor['unit'] = 'Auditor'
    rows.append(auditor)
    wiki_pm = sh.aggregate_per_runner(HISTORY / 'test-wiki-pm-runner.jsonl')
    wiki_pm['unit'] = 'Wiki PM'
    rows.append(wiki_pm)
    developer = sh.aggregate_per_runner(HISTORY / 'test-developer-runner.jsonl')
    developer['unit'] = 'Developer'
    rows.append(developer)
    devops = sh.aggregate_per_runner(HISTORY / 'test-devops-runner.jsonl')
    devops['unit'] = 'DevOps'
    rows.append(devops)
    per_lab = sh.aggregate_per_lab(HISTORY / 'test-lab-AGENTS-runner.jsonl')
    for code in ['RL', 'WB', 'WC', 'WI']:
        if code in per_lab:
            row = per_lab[code]
            row['unit'] = f'{LAB_LABEL[code]} lab AGENTS.md'
            rows.append(row)
    return rows


def render_md(rows: list[dict]) -> str:
    out = ['## Aggregate scores per agentic-md unit',
           '',
           '| Unit                            | Cases (scored / total) | Aggregate score   | Band            | PASS / italian-strike / FAIL |',
           '|---------------------------------|------------------------|-------------------|-----------------|------------------------------|']
    for r in rows:
        norm = r['score_norm']
        norm_str = f'{r["score_sum"]} / {r["score_max_sum"]} = {norm:.3f}' if norm is not None else 'n/a'
        out.append(
            f'| {r["unit"]:<31} '
            f'| {r["n_cases_scored"]:>2} / {r["n_cases_total"]:<2}              '
            f'| {norm_str:<17} '
            f'| {r["band"]:<15} '
            f'| {r["pass_count"]} / {r["italian_strike_count"]} / {r["fail_count"]:<22} |'
        )
    return '\n'.join(out)


def main() -> int:
    rows = gather()
    if '--raw' in sys.argv[1:]:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(render_md(rows))
    return 0


if __name__ == '__main__':
    sys.exit(main())
