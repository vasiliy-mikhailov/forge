#!/usr/bin/env python3
"""K2-R1 RLVR sweep — pick the best L1 variant.

Per ADR 0015 (verifiable agent rewards): the reward is
`trip-quality = min(fwd_recall, bwd_recall) × (1 - compression_ratio)`,
computed mechanically by `scripts/test-runners/measure-corpus-recall.py`
against the synth corpus-observations.

For L1, restore() is identity (lossless), so bwd_recall = fwd_recall
and trip-quality simplifies to `fwd_recall × (1 - ratio)`. Higher is
better. The sweep enumerates the 4 named variants and prints a
markdown table; exit code 0 if any variant beats the K2 hypothesis
target for L1 (trip-quality ≥ 0.20), else 1.

Usage:
    python3 phase-c-…/wiki-bench/compact_restore/sweep.py

Output: a markdown table the architect pastes into K2's Execution
log + the winning variant's name.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
LAB = THIS_DIR.parent
FORGE = LAB.parents[2]
FIXTURE = LAB / 'tests' / 'synthetic' / 'fixtures' / 'k2' / 'lecture_A_synth.json'
SYNTH_OBS = LAB / 'tests' / 'synthetic' / 'fixtures' / 'k2' / 'synth-corpus-observations.md'
RECALL_HARNESS = FORGE / 'scripts' / 'test-runners' / 'measure-corpus-recall.py'

sys.path.insert(0, str(LAB))
from compact_restore.compact import compact_l1   # noqa: E402
from compact_restore.filler_patterns import VARIANTS  # noqa: E402


def run_recall(target_path: Path, source_letter: str = 'X') -> dict:
    out = subprocess.run(
        ['python3', str(RECALL_HARNESS),
         '--source', source_letter,
         '--observations', str(SYNTH_OBS),
         '--against', str(target_path),
         '--json'],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def trip_quality(fwd_recall: float, ratio: float, leakage: float = 0.0) -> float:
    """K2 spec primary metric: trip-quality = min(fwd_recall,
    bwd_recall) × (1 - compression_ratio). For L1, bwd = fwd
    (lossless), so trip-quality = fwd × (1 - ratio).

    air_leakage is a *guardrail* metric per the K2 spec's
    'no factual loss / no fabrication' clause — reported alongside
    trip-quality but NOT folded into the primary reward. The
    leakage parameter is here for future composability but
    currently un-used in the formula. (Folding it in punishes
    Air observations whose verbatim shares content words with
    surrounding Substance — a measurement artefact, not algo
    failure.)
    """
    _ = leakage  # see docstring
    return round(fwd_recall * (1 - ratio), 4)


def render_md(rows: list[dict]) -> str:
    out = [
        '## K2-R1 sweep — variants × trip-quality',
        '',
        '| Variant         | Patterns fired                                | Ratio  | Saved-time% | Fwd recall | Air leakage | Trip-quality |',
        '|-----------------|-----------------------------------------------|--------|-------------|------------|-------------|--------------|',
    ]
    for r in rows:
        fired = ', '.join(r['fired']) or '—'
        out.append(
            f'| {r["variant"]:<15} '
            f'| {fired:<46}'
            f'| {r["ratio"]:.3f} '
            f'| {(1-r["ratio"])*100:.1f}%       '
            f'| {r["fwd_recall"]:.3f}      '
            f'| {r["air_leakage"]:.3f}       '
            f'| **{r["trip_quality"]:.4f}**     |'
        )
    return '\n'.join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--variants', nargs='*', default=list(VARIANTS.keys()))
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()

    raw = json.loads(FIXTURE.read_text(encoding='utf-8'))
    rows = []
    for v in args.variants:
        if v not in VARIANTS:
            print(f'unknown variant: {v}', file=sys.stderr)
            return 2
        compacted = compact_l1(raw, variant=v)
        # Write compacted to temp file as transcript-only md the
        # recall harness can grep
        with tempfile.NamedTemporaryFile('w', suffix='.md',
                                         delete=False, encoding='utf-8') as fh:
            fh.write(compacted['transcript'])
            tmp_path = Path(fh.name)
        recall = run_recall(tmp_path)
        agg = recall['aggregate']
        fwd = agg['_forward_recall']['rate'] or 0.0
        air = agg['_air_leakage']['rate']
        ratio = compacted['compact_metadata']['compression_ratio']
        rows.append({
            'variant': v,
            'fired': compacted['compact_metadata']['filler_patterns_applied'],
            'ratio': ratio,
            'fwd_recall': fwd,
            'air_leakage': air,
            'trip_quality': trip_quality(fwd, ratio, air),
        })
        tmp_path.unlink()

    rows.sort(key=lambda r: -r['trip_quality'])
    winner = rows[0]
    if args.json:
        print(json.dumps({'rows': rows, 'winner': winner['variant']},
                         ensure_ascii=False, indent=2))
    else:
        print(render_md(rows))
        print()
        print(f'**Winner**: `{winner["variant"]}` — trip-quality {winner["trip_quality"]:.4f} '
              f'(fwd recall {winner["fwd_recall"]:.3f}, ratio {winner["ratio"]:.3f}, '
              f'air-leakage {winner["air_leakage"]:.3f}).')
        gate = 0.20
        verdict = 'PASS' if winner['trip_quality'] >= gate else 'FAIL'
        print(f'\nL1 hypothesis gate (trip-quality ≥ {gate:.2f}): **{verdict}**')

    return 0 if winner['trip_quality'] >= 0.20 else 1


if __name__ == '__main__':
    sys.exit(main())
