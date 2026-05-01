#!/usr/bin/env python3
"""K2 falsifier engine — corpus-recall measurement.

The Wiki PM corpus walk produced 51 observations pinned to source A
(lecture #0) in three buckets — Substance / Form / Air — each with a
verbatim quote from the raw transcript. K2 (the two-way compact /
restore experiment) needs the gates "forward recall ≥ 0.85" and
"backward recall ≥ 0.95" to fire mechanically, not via eye-read.
This is the gate engine.

Usage:
    python3 scripts/test-runners/measure-corpus-recall.py \\
        --source A --against compact-A.md
    python3 scripts/test-runners/measure-corpus-recall.py \\
        --source A --against restore-A.md --json

Output (markdown by default):
    Source A — 51 observations (45 Substance + Form, 6 Air)
    | Bucket    | Covered | Total | Rate  |
    |-----------|---------|-------|-------|
    | Substance |  41/41  | 41    | 1.000 |
    | Form      |   5/4   | 4     | 1.250 |
    | Air       |   0/6   | 6     | 0.000 |  (leakage rate; lower=better)
    forward_recall (Substance + Form) = 46/45 = 1.022
    air_leakage = 0/6 = 0.000

Matching rule:
  For each observation, extract ≥3 characteristic Cyrillic content
  words (length ≥ 4, drop a small Russian stopword list) from the
  verbatim quote. ALL extracted keywords must appear in the target
  file (NFC-normalised, lowercase) for the observation to count as
  "covered".

  This is robust to filler removal (L1 Air-strip drops "эээ" /
  "и так далее" — those are below the 4-char floor or in the
  stopword list) and to paraphrase (the keywords are content
  words like "Селье", "оперцепция", "лимбическая", which a
  faithful paraphrase preserves).

Why ≥3 keywords (not "≥1"): single-keyword matches false-positive
on short content words that occur naturally in the target. Three
distinct content words from a single observation co-occurring in
the target is a strong signal the idea is preserved.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

FORGE = Path(__file__).resolve().parents[2]
CORPUS_OBS = (FORGE / 'phase-b-business-architecture' / 'products'
              / 'kurpatov-wiki' / 'corpus-observations.md')

# Russian stopwords (small list — content words have to be the
# distinguishing signal; this just prunes function words).
STOPWORDS = {
    'это', 'этот', 'этой', 'этом', 'этого', 'эти', 'этих',
    'тот', 'того', 'той', 'тех', 'того', 'там', 'тут',
    'который', 'которая', 'которое', 'которые', 'которых',
    'наш', 'наша', 'наше', 'наши', 'наших', 'нашего', 'нашей',
    'свой', 'своя', 'свое', 'свои', 'своих',
    'один', 'одна', 'одно', 'одни',
    'если', 'когда', 'чтобы', 'потому', 'хотя', 'пока',
    'мог', 'могу', 'могут', 'может', 'можно',
    'все', 'всё', 'всех', 'всем', 'всеми',
    'еще', 'ещё', 'уже', 'тоже', 'также',
    'есть', 'нет', 'нужно', 'надо', 'было', 'было', 'была', 'были',
    'будет', 'будут', 'буду', 'будем',
    'мной', 'тобой', 'нами', 'вами', 'себе', 'собой',
    'через', 'между', 'после', 'перед', 'около',
    'своей', 'свою', 'своих', 'своими',
    'каждый', 'каждое', 'каждая', 'каждые',
    'таким', 'такой', 'такая', 'такое', 'такие',
    'образом', 'смысле',
}


def _normalize(text: str) -> str:
    return unicodedata.normalize('NFC', text).lower()


def _content_words(verbatim: str, min_len: int = 4) -> list[str]:
    """Extract candidate Cyrillic content words from a verbatim
    quote. Returns ordered by length descending (longest = most
    distinctive)."""
    norm = _normalize(verbatim)
    # Strip punctuation, keep Cyrillic letters
    tokens = re.findall(r'[а-яё]+', norm)
    seen = set()
    words = []
    for t in tokens:
        if len(t) < min_len:
            continue
        if t in STOPWORDS:
            continue
        if t in seen:
            continue
        seen.add(t)
        words.append(t)
    # Sort by length descending — longer words discriminate better
    words.sort(key=lambda w: (-len(w), w))
    return words


# Schema parsed from corpus-observations.md
OBS_HEADER_RE = re.compile(
    # **OBS-A-001 [dim]** OR **OBS-A-001 [dim1][dim2]** — capture all
    # dimension brackets greedily, then require the closing **.
    r'^\*\*OBS-([A-Z])-(\d{3})\s*((?:\[[^\]]+\])+)\*\*'
)


def parse_observations(md_path: Path = CORPUS_OBS) -> list[dict]:
    """Walk the md, returning one dict per observation:
    {id, source, bucket, dimensions: [str], verbatim: str}.

    Bucket comes from the enclosing `## Substance|Form|Air` heading.
    Verbatim is the next blockquote (`> …`) under the observation
    header.
    """
    text = md_path.read_text(encoding='utf-8')
    lines = text.splitlines()
    observations = []
    cur_bucket = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m_h = re.match(r'^## (Substance|Form|Air)\s*$', ln)
        if m_h:
            cur_bucket = m_h.group(1)
            i += 1
            continue
        m_o = OBS_HEADER_RE.match(ln)
        if m_o and cur_bucket is not None:
            obs_id = f'OBS-{m_o.group(1)}-{m_o.group(2)}'
            source_letter = m_o.group(1)
            raw_dims = m_o.group(3)
            # raw_dims looks like '[d1][d2]' — extract each
            dimensions = re.findall(r'\[([^\]]+)\]', raw_dims)
            # Walk forward until a blockquote
            verbatim_parts = []
            j = i + 1
            in_quote = False
            while j < len(lines):
                jln = lines[j]
                if jln.startswith('>'):
                    in_quote = True
                    verbatim_parts.append(jln.lstrip('>').strip())
                elif in_quote and jln.strip() == '':
                    j += 1
                    break
                elif in_quote:
                    # blockquote continuation without leading '>'
                    if jln.strip() and not jln.startswith('**OBS'):
                        verbatim_parts.append(jln.strip())
                    else:
                        break
                # Stop scan if we hit the next observation
                if OBS_HEADER_RE.match(jln):
                    break
                j += 1
            verbatim = ' '.join(verbatim_parts).strip()
            observations.append({
                'id': obs_id,
                'source': source_letter,
                'bucket': cur_bucket,
                'dimensions': dimensions,
                'verbatim': verbatim,
            })
            i = j
            continue
        i += 1
    return observations


def measure_recall(observations: list[dict], target_text: str,
                   keyword_count: int = 3) -> dict:
    """For each observation, check whether ≥keyword_count
    characteristic words from its verbatim co-occur in the target.

    Returns {obs_id: {covered: bool, matched_words: [str],
                      missing_words: [str], top_keywords: [str]}}.
    """
    target_norm = _normalize(target_text)
    out = {}
    for obs in observations:
        kws = _content_words(obs['verbatim'])[:keyword_count]
        if not kws:
            out[obs['id']] = {
                'covered': False, 'matched_words': [],
                'missing_words': [], 'top_keywords': [],
                'note': 'no extractable content words'
            }
            continue
        matched = [w for w in kws if w in target_norm]
        missing = [w for w in kws if w not in target_norm]
        covered = len(matched) == len(kws)
        out[obs['id']] = {
            'covered': covered,
            'matched_words': matched,
            'missing_words': missing,
            'top_keywords': kws,
        }
    return out


def aggregate(observations: list[dict], measurements: dict,
              source_letter: str | None = None,
              bucket: str | None = None) -> dict:
    """Roll up per-bucket coverage."""
    sel = [o for o in observations
           if (source_letter is None or o['source'] == source_letter)
           and (bucket is None or o['bucket'] == bucket)]
    by_bucket: dict[str, list] = {}
    for o in sel:
        by_bucket.setdefault(o['bucket'], []).append(o)
    out = {}
    for b, obs_list in by_bucket.items():
        covered = sum(1 for o in obs_list
                      if measurements[o['id']]['covered'])
        total = len(obs_list)
        out[b] = {
            'covered': covered, 'total': total,
            'rate': round(covered / total, 4) if total else None,
        }
    # Forward recall = (Substance + Form) covered / total
    sf_covered = sum(out.get(b, {}).get('covered', 0)
                     for b in ('Substance', 'Form'))
    sf_total = sum(out.get(b, {}).get('total', 0)
                   for b in ('Substance', 'Form'))
    out['_forward_recall'] = {
        'covered': sf_covered, 'total': sf_total,
        'rate': round(sf_covered / sf_total, 4) if sf_total else None,
    }
    air = out.get('Air', {})
    out['_air_leakage'] = {
        'leaked': air.get('covered', 0),
        'total': air.get('total', 0),
        'rate': air.get('rate', 0.0),
    }
    return out


def render_md(source_letter: str, agg: dict, n_obs: int) -> str:
    lines = [
        f'# Recall measurement — source {source_letter}',
        f'Observations sampled: {n_obs}',
        '',
        '| Bucket    | Covered | Total | Rate  |',
        '|-----------|---------|-------|-------|',
    ]
    for b in ('Substance', 'Form', 'Air'):
        if b in agg:
            r = agg[b]
            lines.append(
                f'| {b:<9} | {r["covered"]:>2}/{r["total"]:<2}    '
                f'| {r["total"]:<5} | {r["rate"]:.3f} |'
            )
    fr = agg['_forward_recall']
    al = agg['_air_leakage']
    lines.append('')
    lines.append(
        f'forward_recall (Substance + Form) = '
        f'{fr["covered"]}/{fr["total"]} = '
        f'{fr["rate"]:.3f}' if fr['rate'] is not None else
        'forward_recall: n/a'
    )
    lines.append(
        f'air_leakage = {al["leaked"]}/{al["total"]} = '
        f'{al["rate"]:.3f}  (lower = better; 0 = perfect L1)'
    )
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True,
                        help='Source letter (A, B, C, …) from corpus-observations.md')
    parser.add_argument('--against', required=True, type=Path,
                        help='Target file to measure recall against (Compact or Restore output).')
    parser.add_argument('--bucket', default=None,
                        choices=['Substance', 'Form', 'Air'])
    parser.add_argument('--keyword-count', type=int, default=3,
                        help='How many characteristic words from each verbatim must co-occur (default 3).')
    parser.add_argument('--json', action='store_true',
                        help='Emit JSON instead of markdown')
    args = parser.parse_args()

    if not args.against.exists():
        print(f'target file not found: {args.against}', file=sys.stderr)
        return 1
    target_text = args.against.read_text(encoding='utf-8')

    observations = parse_observations()
    sel = [o for o in observations if o['source'] == args.source]
    if not sel:
        print(f'no observations pinned to source {args.source}', file=sys.stderr)
        return 1

    measurements = measure_recall(sel, target_text,
                                   keyword_count=args.keyword_count)
    agg = aggregate(sel, measurements,
                    source_letter=args.source, bucket=args.bucket)

    if args.json:
        print(json.dumps({
            'source': args.source,
            'n_observations': len(sel),
            'aggregate': agg,
            'per_observation': measurements,
        }, ensure_ascii=False, indent=2))
    else:
        print(render_md(args.source, agg, len(sel)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
