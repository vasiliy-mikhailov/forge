#!/usr/bin/env python3
"""Runner for tests/phase-b-business-architecture/roles/test-concept-curator.md

Mechanical inspection of the concept.md files the role has shipped
to kurpatov-wiki-wiki/data/concepts/.

Usage:
    python3 scripts/test-runners/test-concept-curator-runner.py
    python3 scripts/test-runners/test-concept-curator-runner.py --log-scores
    python3 scripts/test-runners/test-concept-curator-runner.py 'CC-0[1-3]'
"""
from __future__ import annotations
import argparse
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _score_history  # noqa: E402

# Reuse the source-author runner's frontmatter parser + repo locator
import importlib.util
_sa_spec = importlib.util.spec_from_file_location(
    '_sa', str(Path(__file__).resolve().parent / 'test-source-author-runner.py'))
_sa = importlib.util.module_from_spec(_sa_spec)
sys.modules['_sa'] = _sa
_sa_spec.loader.exec_module(_sa)
parse_frontmatter = _sa.parse_frontmatter
_find_repo = _sa._find_repo
adr0015_verdict = _sa.adr0015_verdict
Result = _sa.Result

FORGE = Path(__file__).resolve().parents[2]


def _list_concepts(wiki: Path) -> list[Path]:
    root = wiki / 'data' / 'concepts'
    if not root.exists():
        return []
    return sorted(p for p in root.glob('*.md'))


# ─────────────── CC-01: required frontmatter ───────────────

REQUIRED_CONCEPT_FRONTMATTER = ['slug', 'first_introduced_in', 'touched_by']


def cc_01_frontmatter_required_fields(wiki: Path, **_) -> Result:
    concepts = _list_concepts(wiki)
    if not concepts:
        return Result('SKIP', 'no concept.md files',
                      score=0.0, score_max=2.0, threshold=1.6)
    n = len(concepts)
    c1 = c2 = 0
    for c in concepts:
        text = c.read_text(encoding='utf-8')
        fm = parse_frontmatter(text)
        if fm is not None:
            c1 += 1
            if all(k in fm for k in REQUIRED_CONCEPT_FRONTMATTER):
                c2 += 1
    score = round((c1 + c2) / n, 4)
    return Result(adr0015_verdict(score, 2.0, 1.6),
                  f'{c1}/{n} have FM; {c2}/{n} have all 3 fields',
                  score=score, score_max=2.0, threshold=1.6)


# ─────────────── CC-02: Definition section present ───────────────

def cc_02_definition_section(wiki: Path, **_) -> Result:
    concepts = _list_concepts(wiki)
    if not concepts:
        return Result('SKIP', 'no concept.md files',
                      score=0.0, score_max=1.0, threshold=0.95)
    n = len(concepts)
    has_def = 0
    for c in concepts:
        text = c.read_text(encoding='utf-8')
        if re.search(r'(?im)^#{2,}\s*definition\b', text):
            has_def += 1
    score = round(has_def / n, 4)
    return Result(adr0015_verdict(score, 1.0, 0.95),
                  f'{has_def}/{n} have ## Definition',
                  score=score, score_max=1.0, threshold=0.95)


# ─────────────── CC-03: bidirectional cross-refs ───────────────

RELATED_LINK_RE = re.compile(r'\[([\w\-]+)\]\([\w\-]+\.md\)')


def _related_concepts(text: str) -> set[str]:
    """Extract slugs from the '## Related concepts' section."""
    m = re.search(r'(?ims)^#{2,}\s*related\s+concepts?\s*$.+?(?=\n#{1,2}\s|\Z)',
                  text)
    if not m:
        return set()
    return set(RELATED_LINK_RE.findall(m.group(0)))


def cc_03_bidirectional_links(wiki: Path, **_) -> Result:
    concepts = _list_concepts(wiki)
    if not concepts:
        return Result('SKIP', 'no concept.md files',
                      score=0.0, score_max=2.0, threshold=1.0)
    rels = {}
    for c in concepts:
        text = c.read_text(encoding='utf-8')
        rels[c.stem] = _related_concepts(text)
    total_links = 0
    bidir_links = 0
    for src_slug, targets in rels.items():
        for tgt_slug in targets:
            total_links += 1
            if src_slug in rels.get(tgt_slug, set()):
                bidir_links += 1
    rate = bidir_links / total_links if total_links else 0
    score = (1.0 if rate >= 0.5 else 0.0) + (1.0 if rate >= 0.8 else 0.0)
    return Result(adr0015_verdict(score, 2.0, 1.0),
                  f'{bidir_links}/{total_links} links round-trip (rate={rate:.3f})',
                  score=score, score_max=2.0, threshold=1.0)


# ─────────────── CC-04: first_introduced_in resolves to source.md ───────────────

def cc_04_first_introduced_resolves(wiki: Path, **_) -> Result:
    concepts = _list_concepts(wiki)
    if not concepts:
        return Result('SKIP', 'no concept.md files',
                      score=0.0, score_max=1.0, threshold=0.95)
    src_root = wiki / 'data' / 'sources'
    n = len(concepts)
    resolved = 0
    for c in concepts:
        text = c.read_text(encoding='utf-8')
        fm = parse_frontmatter(text) or {}
        slug = fm.get('first_introduced_in', '')
        if not slug:
            continue
        target = (src_root / (slug + '.md'))
        # NFC-safe lookup
        target_nfc = unicodedata.normalize('NFC', str(target))
        for r, _, files in os.walk(src_root):
            for fn in files:
                full_nfc = unicodedata.normalize('NFC', os.path.join(r, fn))
                if full_nfc == target_nfc:
                    resolved += 1
                    break
            else:
                continue
            break
    score = round(resolved / n, 4)
    return Result(adr0015_verdict(score, 1.0, 0.95),
                  f'{resolved}/{n} first_introduced_in resolves',
                  score=score, score_max=1.0, threshold=0.95)


# ─────────────── CC-05: no duplicate slugs ───────────────

def cc_05_no_duplicate_slugs(wiki: Path, **_) -> Result:
    concepts = _list_concepts(wiki)
    if not concepts:
        return Result('SKIP', 'no concept.md files',
                      score=0.0, score_max=1.0, threshold=1.0)
    slugs = []
    for c in concepts:
        text = c.read_text(encoding='utf-8')
        fm = parse_frontmatter(text) or {}
        slugs.append(fm.get('slug', c.stem))
    score = 1.0 if len(slugs) == len(set(slugs)) else 0.0
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'{len(slugs)} files / {len(set(slugs))} distinct slugs',
                  score=score, score_max=1.0, threshold=1.0)


# ─────────────── CC-06: self-attestation in touched_by ───────────────

def cc_06_self_attest(wiki: Path, **_) -> Result:
    concepts = _list_concepts(wiki)
    if not concepts:
        return Result('SKIP', 'no concept.md files',
                      score=0.0, score_max=1.0, threshold=0.9)
    n = len(concepts)
    consistent = 0
    for c in concepts:
        text = c.read_text(encoding='utf-8')
        fm = parse_frontmatter(text) or {}
        intro = fm.get('first_introduced_in', '')
        touched = fm.get('touched_by', []) or []
        if not isinstance(touched, list):
            touched = []
        if not intro:
            consistent += 1  # vacuous (no intro to check)
            continue
        intro_nfc = unicodedata.normalize('NFC', intro)
        if any(unicodedata.normalize('NFC', t) == intro_nfc for t in touched):
            consistent += 1
    score = round(consistent / n, 4)
    return Result(adr0015_verdict(score, 1.0, 0.9),
                  f'{consistent}/{n} concepts have intro∈touched_by',
                  score=score, score_max=1.0, threshold=0.9)


REGISTRY = {
    'CC-01': cc_01_frontmatter_required_fields,
    'CC-02': cc_02_definition_section,
    'CC-03': cc_03_bidirectional_links,
    'CC-04': cc_04_first_introduced_resolves,
    'CC-05': cc_05_no_duplicate_slugs,
    'CC-06': cc_06_self_attest,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('pattern', nargs='?', default='*')
    parser.add_argument('--log-scores', action='store_true')
    parser.add_argument('--wiki', type=Path,
                        default=_find_repo('kurpatov-wiki-wiki'))
    args = parser.parse_args()
    if args.wiki is None:
        print('kurpatov-wiki-wiki not found; pass --wiki', file=sys.stderr)
        return 1

    selected = [k for k in REGISTRY if fnmatch(k, args.pattern)]
    counts = {'PASS': 0, 'FAIL': 0, 'SKIP': 0, 'PASS-italian-strike': 0}
    rows = []
    for tid in selected:
        r = REGISTRY[tid](wiki=args.wiki)
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
        score_str = (f' [{r.score}/{r.score_max}]'
                     if r.score is not None else '')
        print(f'  {tid:<6} {r.verdict:<19}{score_str}  {r.detail}'.rstrip())
        rows.append((tid, r.verdict, r.score, r.score_max, r.threshold,
                     r.detail))
    print()
    print(f'  total: PASS={counts["PASS"]}  '
          f'PASS-italian-strike={counts.get("PASS-italian-strike", 0)}  '
          f'FAIL={counts["FAIL"]}  SKIP={counts["SKIP"]}')
    if args.log_scores:
        path = _score_history.append_scores('test-concept-curator-runner', rows)
        print(f'  logged {len(rows)} rows -> {path.relative_to(FORGE)}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
