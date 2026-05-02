#!/usr/bin/env python3
"""K2 falsifier-first probe — measure real signal before building algorithm.

Per the lesson from K2-R1 → K2-R2 (synth fixture passed at trip-quality
0.2261; real lecture A crashed to 0.0116): pytest-green doesn't equal
real-data-works. Every K2 layer beyond L1 must answer "does this layer
have signal to extract on real corpus?" BEFORE any algorithm code.

This probe answers two specific questions:

L2 (cross-source surface dedup) signal:
  How much of lecture A's 5-gram shingle space appears in any other
  raw transcript? If <1% → don't build L2. If 5%+ → L2 has runway.

L3 (concept-graph link-out) signal:
  How many of the 51 published concept names appear by name in
  lecture A's transcript? Each hit is a place where L3 can replace
  a definition-paragraph with a `[concept](link)` link-stub.

Usage:
    python3 phase-c-…/wiki-bench/compact_restore/probe_overlap.py \\
        --raw-repo /path/to/kurpatov-wiki-raw \\
        --wiki-repo /path/to/kurpatov-wiki-wiki \\
        --lecture-match '000 Знакомство'

Output: per-pair shingle-overlap table + concept-hit list. No file
writes. Run as exploratory measurement; commit the result into the
K2 spec's Execution log + Post-Mortem.

Result on 2026-05-02 against lecture A:
  L2 signal = 0.02% best, 0.00% mean across 60 other raws
              → STOP, surface dedup has no runway on this corpus.
  L3 signal = 21.6% (11 of 51 concepts mention by name)
              → GO, build L3 next.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import unicodedata
from pathlib import Path

# Russian stopwords + observed K2-R3 filler vocabulary.
STOPWORDS = {
    'это','этот','этой','этом','этого','эти','этих','тот','того','той','тех','там','тут',
    'который','которая','которое','которые','которых','наш','наша','наше','наши','наших',
    'свой','своя','свое','свои','своих','один','одна','одно','одни','если','когда','чтобы',
    'потому','хотя','пока','может','можно','все','всё','всех','всем','еще','ещё','уже',
    'тоже','также','есть','нет','нужно','надо','было','была','были','будет','будут',
    'через','между','после','перед','около','каждый','каждое','каждая','каждые','таким',
    'такой','такая','такое','такие','образом','смысле','свою','своей',
    # K2-R3 discourse markers
    'значит','собственно','допустим','скажем','кстати','короче',
    'самом','деле','общем','быть','стать','делать','сделать',
    'говорить','сказать','знать','понимать',
}


def normalize(text: str) -> list[str]:
    text = unicodedata.normalize('NFC', text).lower()
    return [t for t in re.findall(r'[а-яё]+', text)
            if t not in STOPWORDS and len(t) >= 4]


def shingles(toks: list[str], n: int = 5) -> set[str]:
    return {' '.join(toks[i:i + n]) for i in range(len(toks) - n + 1)}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a and b) else 0.0


def asym_a_in_b(a: set, b: set) -> float:
    return len(a & b) / len(a) if a else 0.0


def find_lecture_a(raw_repo: Path, match: str):
    for r, _, files in os.walk(raw_repo / 'data'):
        if 'raw.json' in files and match in r:
            return r, os.path.join(r, 'raw.json')
    return None, None


def load_raw_text(p: str) -> str:
    d = json.load(open(p, encoding='utf-8'))
    return ' '.join(s.get('text', '').strip() for s in d.get('segments', []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw-repo', type=Path, required=True)
    ap.add_argument('--wiki-repo', type=Path, required=True)
    ap.add_argument('--lecture-match', default='000 Знакомство')
    ap.add_argument('--shingle-n', type=int, default=5)
    args = ap.parse_args()

    # Locate the lecture under test
    a_dir, a_path = find_lecture_a(args.raw_repo, args.lecture_match)
    if a_path is None:
        raise SystemExit(f'no raw.json matching {args.lecture_match!r}')
    a_rel = os.path.relpath(a_dir, args.raw_repo / 'data')
    a_text = load_raw_text(a_path)
    a_tokens = normalize(a_text)
    a_shingles = shingles(a_tokens, args.shingle_n)
    a_words = len(a_text.split())
    print(f'Lecture A: {a_rel}')
    print(f'  {a_words} words, {len(a_tokens)} content-tokens, '
          f'{len(a_shingles)} {args.shingle_n}-gram shingles\n')

    # Walk every other raw.json
    others = []
    for r, _, files in os.walk(args.raw_repo / 'data'):
        if 'raw.json' in files:
            full = os.path.join(r, 'raw.json')
            if full == a_path:
                continue
            rel = os.path.relpath(r, args.raw_repo / 'data')
            others.append((rel, full))
    others.sort()

    # === L2 signal ===
    print(f'=== L2 falsifier — surface shingle overlap (A vs {len(others)} '
          f'other raws) ===\n')
    print(f'{"Other raw lecture":<70} {"toks":>5} {"Jacc":>6} {"A∩B/|A|":>9}')
    rows = []
    for rel, p in others:
        sh = shingles(normalize(load_raw_text(p)), args.shingle_n)
        rows.append((rel, len(sh),
                     jaccard(a_shingles, sh),
                     asym_a_in_b(a_shingles, sh)))
    rows.sort(key=lambda r: -r[3])
    for rel, ntok, j, a_in_b in rows[:10]:
        print(f'{rel[:70]:<70} {ntok:>5} {j:>6.4f} {a_in_b:>9.4f}')
    best = rows[0][3]
    mean = sum(r[3] for r in rows) / len(rows) if rows else 0
    print(f'\n  best A∩B/|A| = {best:.4f} ({best*100:.2f}%)')
    print(f'  mean A∩B/|A| = {mean:.4f}')
    decision_l2 = ('GO — build L2' if best >= 0.05
                   else 'DEFER — marginal' if best >= 0.01
                   else 'STOP — no signal to extract')
    print(f'  → L2 decision: {decision_l2}')

    # === L3 signal ===
    print(f'\n=== L3 falsifier — concept-name hits in lecture A ===\n')
    concept_root = args.wiki_repo / 'data' / 'concepts'
    a_norm = unicodedata.normalize('NFC', a_text).lower()
    hits = []
    total = 0
    for p in sorted(concept_root.glob('*.md')):
        text = p.read_text(encoding='utf-8')
        m = re.search(r'^#\s+([^\n]+)', text, re.MULTILINE)
        if not m:
            continue
        total += 1
        name = m.group(1).strip()
        name_norm = unicodedata.normalize('NFC', name).lower()
        if len(name_norm) >= 5 and name_norm in a_norm:
            hits.append((p.stem, name))
    print(f'  {len(hits)} of {total} concepts mention by name '
          f'({100 * len(hits) / total:.1f}%)\n')
    for slug, name in hits:
        print(f'  ✓ {slug:<35} "{name}"')
    decision_l3 = ('GO — build L3' if len(hits) / total >= 0.10
                   else 'DEFER — marginal' if len(hits) / total >= 0.03
                   else 'STOP — no signal to extract')
    print(f'\n  → L3 decision: {decision_l3}')


if __name__ == '__main__':
    main()
