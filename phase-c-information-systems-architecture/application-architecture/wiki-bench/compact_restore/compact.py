"""K2-R1 compact() L1 — Air-strip on raw.json transcripts.

L1 is pure regex over Cyrillic spoken text. No GPU. No network.
No LLM. Runs on CPU in milliseconds — the cheap floor of the K2
layered hypothesis.

Input: a kurpatov-wiki-raw raw.json dict
       {stem, course, module, transcript, segments, …}.

Output: a dict with the same identifying keys plus
       compact_metadata = {layer, compression_ratio, tok_original,
                           tok_compact, filler_patterns_applied}.

The transcript field is rewritten by stripping Air patterns; the
segments field is rewritten in-place per segment. Substance and
Form patterns are out of scope for L1 (handled at L2/L3).
"""
from __future__ import annotations
from typing import Iterable

from .filler_patterns import CANONICAL, VARIANTS


def _apply_patterns(text: str, patterns: Iterable) -> tuple[str, list[str]]:
    """Run patterns in order, returning (new_text, [pattern_label …])
    listing every pattern that fired at least once."""
    fired = []
    for p in patterns:
        if len(p) == 2:
            label, regex = p
            new = regex.sub('', text)
        else:
            label, regex, repl = p
            new = regex.sub(repl, text)
        if new != text:
            fired.append(label)
        text = new
    return text, fired


def _approx_token_count(text: str) -> int:
    """Whitespace-token count — proxy for tokenizer-agnostic tokens.
    Matches what `tiktoken` cl100k_base produces within ±10% on
    Cyrillic spoken text per K2 spec assumption."""
    return len(text.split())


def compact_l1(raw: dict, variant: str | None = None) -> dict:
    """Apply L1 Air-strip and return the compact-form dict.

    `variant`: name of a pattern set in `filler_patterns.VARIANTS`
    (e.g., 'V1_minimal', 'V4_aggressive'). Default: the canonical
    V3_discourse set.
    """
    patterns = VARIANTS[variant] if variant else CANONICAL
    transcript = raw['transcript']
    new_transcript, fired = _apply_patterns(transcript, patterns)
    # Rewrite segments
    new_segments = []
    for seg in raw.get('segments', []):
        new_text, _ = _apply_patterns(seg['text'], patterns)
        new_segments.append({**seg, 'text': new_text.strip()})
    tok_original = _approx_token_count(transcript)
    tok_compact = _approx_token_count(new_transcript)
    return {
        'stem': raw['stem'],
        'course': raw.get('course', ''),
        'module': raw.get('module', ''),
        'transcript': new_transcript.strip(),
        'segments': new_segments,
        'compact_metadata': {
            'layer': 'L1',
            'variant': variant or 'V3_discourse',
            'compression_ratio': round(tok_compact / tok_original, 4),
            'tok_original': tok_original,
            'tok_compact': tok_compact,
            'filler_patterns_applied': fired,
        },
    }
