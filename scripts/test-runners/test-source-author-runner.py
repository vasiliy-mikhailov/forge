#!/usr/bin/env python3
"""Runner for tests/phase-b-business-architecture/roles/test-source-author.md

Mechanical inspection of the source.md files the role has shipped
to kurpatov-wiki-wiki/data/sources/. The wiki repo lives outside
forge (it's a sibling repo per ADR 0005); the runner walks the
filesystem to locate it. Defaults assume both repos sit under the
same parent (the architect's repos/ dir on the Cowork host or
${STORAGE_ROOT}/labs/wiki-ingest/vault/ on mikhailov.tech).

Usage:
    python3 scripts/test-runners/test-source-author-runner.py
    python3 scripts/test-runners/test-source-author-runner.py --log-scores
    python3 scripts/test-runners/test-source-author-runner.py 'SA-0[1-3]'
    python3 scripts/test-runners/test-source-author-runner.py \\
        --wiki /custom/path/to/kurpatov-wiki-wiki \\
        --raw  /custom/path/to/kurpatov-wiki-raw

Exit code: 0 if no FAIL; 1 otherwise.
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

FORGE = Path(__file__).resolve().parents[2]


def _find_repo(name: str) -> Path | None:
    """Locate a sibling repo by walking parents of forge."""
    candidates = [
        FORGE.parent / name,
        FORGE.parent.parent / 'repos' / name,
        Path.home() / 'repos' / name,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


@dataclass
class Result:
    verdict: str
    detail: str = ''
    score: float | None = None
    score_max: float | None = None
    threshold: float | None = None


def adr0015_verdict(score, score_max, threshold):
    if score < threshold:
        return 'FAIL'
    if score >= 0.8 * score_max:
        return 'PASS'
    return 'PASS-italian-strike'


# ─────────────── Frontmatter parsing ───────────────

YAML_LIST_RE = re.compile(r'^\s*-\s*(.+?)\s*$', re.MULTILINE)


def parse_frontmatter(text: str) -> dict | None:
    """Naive YAML frontmatter parser — sufficient for the
    flat-key + simple-list shape the wiki schema uses.
    Returns dict[str, str | list[str]] or None if absent."""
    if not text.startswith('---\n') and not text.startswith('---\r'):
        return None
    end = text.find('\n---', 4)
    if end == -1:
        return None
    body = text[4:end]
    out: dict = {}
    cur_key: str | None = None
    for ln in body.splitlines():
        if not ln.strip():
            continue
        if ln.startswith('  ') or ln.startswith('\t'):
            # list item under cur_key
            if cur_key is not None:
                m = re.match(r'\s*-\s*(.+)', ln)
                if m:
                    if not isinstance(out.get(cur_key), list):
                        out[cur_key] = []
                    out[cur_key].append(m.group(1).strip())
            continue
        m = re.match(r'^([A-Za-z_][\w\-]*)\s*:\s*(.*)$', ln)
        if not m:
            cur_key = None
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == '' or val == '[]':
            out[key] = [] if val == '[]' else None
            cur_key = key
        elif val.startswith('[') and val.endswith(']'):
            inner = val[1:-1].strip()
            out[key] = [x.strip() for x in inner.split(',')] if inner else []
            cur_key = None
        else:
            out[key] = val
            cur_key = key
    return out


# ─────────────── source.md walk ───────────────

def _list_sources(wiki: Path) -> list[Path]:
    src_root = wiki / 'data' / 'sources'
    if not src_root.exists():
        return []
    out = []
    for root, _, files in os.walk(src_root):
        for fn in files:
            if fn.endswith('.md') and fn != '_template.md':
                out.append(Path(root) / fn)
    return sorted(out)


# ─────────────── SA-01: required frontmatter fields ───────────────

REQUIRED_SOURCE_FRONTMATTER = [
    'slug', 'course', 'module', 'source_raw', 'language',
    'processed_at', 'concepts_touched', 'concepts_introduced',
]


def sa_01_frontmatter_required_fields(wiki: Path, **_) -> Result:
    sources = _list_sources(wiki)
    if not sources:
        return Result('SKIP', 'no source.md files',
                      score=0.0, score_max=2.0, threshold=1.6)
    total_c1 = total_c2 = 0
    n = len(sources)
    for s in sources:
        text = s.read_text(encoding='utf-8')
        fm = parse_frontmatter(text)
        if fm is not None:
            total_c1 += 1
            if all(k in fm for k in REQUIRED_SOURCE_FRONTMATTER):
                total_c2 += 1
    score = round((total_c1 + total_c2) / n, 4)
    score_max = 2.0
    return Result(adr0015_verdict(score, score_max, 1.6),
                  f'{total_c1}/{n} have FM, {total_c2}/{n} have all 8 fields',
                  score=score, score_max=score_max, threshold=1.6)


# ─────────────── SA-02: required body sections ───────────────

def sa_02_body_sections(wiki: Path, **_) -> Result:
    sources = _list_sources(wiki)
    if not sources:
        return Result('SKIP', 'no source.md files',
                      score=0.0, score_max=3.0, threshold=1.6)
    n = len(sources)
    c1 = c2 = c3 = 0
    for s in sources:
        text = s.read_text(encoding='utf-8')
        if re.search(r'(?im)^#{2,}\s*tl;?\s*dr', text):
            c1 += 1
        if re.search(r'(?im)^#{2,}\s*claims', text):
            c2 += 1
        if '## Лекция' in text:
            c3 += 1
    score = round((c1 + c2 + c3) / n, 4)
    return Result(adr0015_verdict(score, 3.0, 1.6),
                  f'TL;DR={c1}/{n}, Claims={c2}/{n}, Лекция={c3}/{n}',
                  score=score, score_max=3.0, threshold=1.6)


# ─────────────── SA-03: provenance markers ───────────────

def sa_03_provenance_markers(wiki: Path, **_) -> Result:
    sources = _list_sources(wiki)
    if not sources:
        return Result('SKIP', 'no source.md files',
                      score=0.0, score_max=2.0, threshold=1.0)
    n = len(sources)
    c1 = c2 = 0
    for s in sources:
        text = s.read_text(encoding='utf-8')
        if 'NEW' in text:
            c1 += 1
        if 'REPEATED' in text or 'CONTRADICTS' in text:
            c2 += 1
    score = round((c1 + c2) / n, 4)
    return Result(adr0015_verdict(score, 2.0, 1.0),
                  f'NEW={c1}/{n}, REPEATED|CONTRADICTS={c2}/{n}',
                  score=score, score_max=2.0, threshold=1.0)


# ─────────────── SA-04: concepts_touched resolves ───────────────

def sa_04_concepts_resolve(wiki: Path, **_) -> Result:
    sources = _list_sources(wiki)
    if not sources:
        return Result('SKIP', 'no source.md files',
                      score=0.0, score_max=2.0, threshold=1.0)
    concept_root = wiki / 'data' / 'concepts'
    existing_slugs = {p.stem for p in concept_root.glob('*.md')} if concept_root.exists() else set()
    n = len(sources)
    c1 = c2 = 0
    for s in sources:
        text = s.read_text(encoding='utf-8')
        fm = parse_frontmatter(text) or {}
        slugs = fm.get('concepts_touched') or []
        if not isinstance(slugs, list):
            slugs = []
        if not slugs:
            # vacuous (the source touches no concepts) — count as PASS
            c1 += 1; c2 += 1
            continue
        resolved = sum(1 for sl in slugs if sl in existing_slugs)
        rate = resolved / len(slugs) if slugs else 0
        if rate >= 0.95:
            c1 += 1
        if rate >= 0.999:
            c2 += 1
    score = round((c1 + c2) / n, 4)
    return Result(adr0015_verdict(score, 2.0, 1.0),
                  f'rate≥0.95: {c1}/{n}; rate=1.0: {c2}/{n}',
                  score=score, score_max=2.0, threshold=1.0)


# ─────────────── SA-05: slug matches path ───────────────

def sa_05_slug_matches_path(wiki: Path, **_) -> Result:
    sources = _list_sources(wiki)
    if not sources:
        return Result('SKIP', 'no source.md files',
                      score=0.0, score_max=1.0, threshold=1.0)
    src_root = wiki / 'data' / 'sources'
    n = len(sources)
    matches = 0
    for s in sources:
        text = s.read_text(encoding='utf-8')
        fm = parse_frontmatter(text) or {}
        slug = fm.get('slug', '')
        rel = s.relative_to(src_root).with_suffix('')
        # NFC-normalise both sides (Cyrillic mac/linux mismatch)
        if unicodedata.normalize('NFC', str(rel)) == unicodedata.normalize('NFC', str(slug)):
            matches += 1
    score = round(matches / n, 4)
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'{matches}/{n} slugs match path',
                  score=score, score_max=1.0, threshold=1.0)


# ─────────────── SA-06: source_raw resolves ───────────────

def sa_06_source_raw_resolves(wiki: Path, raw: Path | None, **_) -> Result:
    sources = _list_sources(wiki)
    if not sources:
        return Result('SKIP', 'no source.md files',
                      score=0.0, score_max=1.0, threshold=1.0)
    if raw is None:
        return Result('SKIP', 'kurpatov-wiki-raw not found',
                      score=0.0, score_max=1.0, threshold=1.0)
    n = len(sources)
    resolved = 0
    # Build NFC-normalised lookup of every raw.json relative path
    raw_paths = set()
    for r, _, files in os.walk(raw):
        for fn in files:
            if fn == 'raw.json':
                relp = os.path.relpath(os.path.join(r, fn), raw)
                raw_paths.add(unicodedata.normalize('NFC', relp))
    for s in sources:
        text = s.read_text(encoding='utf-8')
        fm = parse_frontmatter(text) or {}
        sr = fm.get('source_raw', '')
        if not sr:
            continue
        # source_raw is 'data/<course>/<module>/<stem>/raw.json'
        # raw_paths set was built relative to the kurpatov-wiki-raw
        # repo root, which already includes the 'data/' prefix — so
        # do NOT strip it.
        if unicodedata.normalize('NFC', sr) in raw_paths:
            resolved += 1
    score = round(resolved / n, 4)
    return Result(adr0015_verdict(score, 1.0, 1.0),
                  f'{resolved}/{n} source_raw paths resolve',
                  score=score, score_max=1.0, threshold=1.0)


REGISTRY = {
    'SA-01': sa_01_frontmatter_required_fields,
    'SA-02': sa_02_body_sections,
    'SA-03': sa_03_provenance_markers,
    'SA-04': sa_04_concepts_resolve,
    'SA-05': sa_05_slug_matches_path,
    'SA-06': sa_06_source_raw_resolves,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('pattern', nargs='?', default='*')
    parser.add_argument('--log-scores', action='store_true')
    parser.add_argument('--wiki', type=Path,
                        default=_find_repo('kurpatov-wiki-wiki'))
    parser.add_argument('--raw', type=Path,
                        default=_find_repo('kurpatov-wiki-raw'))
    args = parser.parse_args()
    if args.wiki is None:
        print('kurpatov-wiki-wiki not found; pass --wiki', file=sys.stderr)
        return 1

    selected = [k for k in REGISTRY if fnmatch(k, args.pattern)]
    counts = {'PASS': 0, 'FAIL': 0, 'SKIP': 0, 'PASS-italian-strike': 0}
    rows = []
    for tid in selected:
        r = REGISTRY[tid](wiki=args.wiki, raw=args.raw)
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
        path = _score_history.append_scores('test-source-author-runner', rows)
        print(f'  logged {len(rows)} rows -> {path.relative_to(FORGE)}')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
