"""K2-R1 — Air-strip pattern catalog.

Patterns are derived from the Wiki PM corpus walk (Air bucket
observations OBS-A-* and OBS-X-* in the synth corpus). Each
pattern is a `(label, regex)` tuple. The L1 compact() applies
them in order; later patterns can clean up artefacts left by
earlier ones (e.g. a comma left dangling after vocalised
hesitation removal).

The pattern set is deliberately conservative — every pattern
must be defensible as "carries no information beyond the
surrounding Substance / Form" per the WP-07..14 reward functions
in tests/phase-b-business-architecture/roles/test-wiki-pm.md.

Variants for the K2-R1 RLVR sweep live below the canonical set
as `VARIANT_*` named groups; the sweep CLI enumerates them.
"""
from __future__ import annotations
import re

# ───────────────── canonical (default) Air pattern set ─────────────────

# 1. Vocalised hesitations: standalone 'эээ' / 'ээ' / 'эээээ' tokens.
#    Match as standalone word — surrounding commas eaten if present.
PATTERN_VOCALISED_HESITATION = (
    'vocalised_hesitation',
    re.compile(r'(?i)(?:^|(?<=[\s,—]))э{2,}\b[\s,]*'),
)

# 2. Triple-trail и-так-далее (≥2 adjacent occurrences). Collapse to
#    nothing (the surrounding Substance carries the meaning; the
#    triple-trail just signals "list goes on" with no info).
PATTERN_TRIPLE_TRAIL_ITD = (
    'triple_trail_i_tak_dalee',
    re.compile(r'(?i)(?:[,.\s]*и\s+так\s+далее){2,}[,.]*'),
)

# 3. Adjacent identical Cyrillic word (length ≥4). Collapse to one
#    occurrence. Matches "эмпатические эмпатические" → "эмпатические".
PATTERN_WORD_DOUBLING = (
    'word_doubling',
    re.compile(r'(?i)\b([а-яё]{4,})\s+\1\b'),
)
WORD_DOUBLING_REPL = r'\1'

# 4. Triple-word repeat with comma separators ("стрессом, стрессом,
#    стрессом" → "стрессом").
PATTERN_TRIPLE_WORD = (
    'triple_word',
    re.compile(r'(?i)\b([а-яё]{4,})[\s,]+\1[\s,]+\1\b'),
)
TRIPLE_WORD_REPL = r'\1'

# 5. Triple-phrase repeat ("представьте себе, представьте себе,
#    представьте себе" → "представьте себе"). 2-word phrases.
PATTERN_TRIPLE_PHRASE = (
    'triple_phrase',
    re.compile(r'(?i)\b([а-яё]{3,}\s+[а-яё]{3,})[,\s]+\1[,\s]+\1\b'),
)
TRIPLE_PHRASE_REPL = r'\1'

# 6. Filler conjunctions used as stand-alone discourse markers when
#    flanked by commas (so the surrounding sentence reads naturally
#    after removal). Conservative — does NOT match these tokens
#    when they carry sentence load.
PATTERN_FILLER_CONJ = (
    'filler_conjunction',
    re.compile(r'(?i)(?:^|(?<=[\s,—]))(?:ну\s+вот|как\s+бы|это\s+самое|значит|ну)[\s,]+'),
)

# 7. Self-Q&A scaffolding: rhetorical question lifting the next
#    claim ("Все ли это? Тоже далеко не все."). Match the question
#    + its dismissive answer; the next sentence carries the load.
PATTERN_SELF_QA = (
    'self_qa',
    re.compile(r'(?i)\b(?:все\s+ли\s+это|это\s+ли\s+все)\?\s*тоже\s+далеко\s+не\s+вс[ёе]\.?\s*'),
)

# 8. Cleanup: collapse runs of whitespace + leftover comma artefacts.
PATTERN_CLEANUP_WS = (
    'cleanup_whitespace',
    re.compile(r'\s{2,}'),
)
PATTERN_CLEANUP_COMMA = (
    'cleanup_comma',
    re.compile(r',\s*,+'),
)
PATTERN_CLEANUP_LEAD_COMMA = (
    'cleanup_leading_comma',
    re.compile(r'(?<=[\.!?])\s*,+\s*'),
)


# ───────────────── named variants for the RLVR sweep ─────────────────

# V1 — minimal: only vocalised hesitation + cleanup. Conservative
#      baseline. Expected ratio ~0.92 (saved ~8%).
VARIANT_V1_MINIMAL = [
    PATTERN_VOCALISED_HESITATION,
    PATTERN_CLEANUP_COMMA,
    PATTERN_CLEANUP_WS,
]

# V2 — minimal + triple-trail + word-doubling + triple-word +
#      triple-phrase. The "structural" Air patterns. Expected ratio
#      ~0.80.
VARIANT_V2_STRUCTURAL = [
    PATTERN_VOCALISED_HESITATION,
    PATTERN_TRIPLE_TRAIL_ITD,
    (PATTERN_WORD_DOUBLING[0], PATTERN_WORD_DOUBLING[1], WORD_DOUBLING_REPL),
    (PATTERN_TRIPLE_WORD[0], PATTERN_TRIPLE_WORD[1], TRIPLE_WORD_REPL),
    (PATTERN_TRIPLE_PHRASE[0], PATTERN_TRIPLE_PHRASE[1], TRIPLE_PHRASE_REPL),
    PATTERN_CLEANUP_COMMA,
    PATTERN_CLEANUP_LEAD_COMMA,
    PATTERN_CLEANUP_WS,
]

# V3 — V2 + filler conjunctions ("ну, как бы, значит"). Expected
#      ratio ~0.70.
VARIANT_V3_DISCOURSE = VARIANT_V2_STRUCTURAL[:1] + [
    PATTERN_TRIPLE_TRAIL_ITD,
    (PATTERN_WORD_DOUBLING[0], PATTERN_WORD_DOUBLING[1], WORD_DOUBLING_REPL),
    (PATTERN_TRIPLE_WORD[0], PATTERN_TRIPLE_WORD[1], TRIPLE_WORD_REPL),
    (PATTERN_TRIPLE_PHRASE[0], PATTERN_TRIPLE_PHRASE[1], TRIPLE_PHRASE_REPL),
    PATTERN_FILLER_CONJ,
    PATTERN_CLEANUP_COMMA,
    PATTERN_CLEANUP_LEAD_COMMA,
    PATTERN_CLEANUP_WS,
]

# V4 — V3 + self-Q&A scaffolding. Most aggressive. Expected ratio
#      ~0.65.
VARIANT_V4_AGGRESSIVE = [
    PATTERN_VOCALISED_HESITATION,
    PATTERN_TRIPLE_TRAIL_ITD,
    (PATTERN_WORD_DOUBLING[0], PATTERN_WORD_DOUBLING[1], WORD_DOUBLING_REPL),
    (PATTERN_TRIPLE_WORD[0], PATTERN_TRIPLE_WORD[1], TRIPLE_WORD_REPL),
    (PATTERN_TRIPLE_PHRASE[0], PATTERN_TRIPLE_PHRASE[1], TRIPLE_PHRASE_REPL),
    PATTERN_FILLER_CONJ,
    PATTERN_SELF_QA,
    PATTERN_CLEANUP_COMMA,
    PATTERN_CLEANUP_LEAD_COMMA,
    PATTERN_CLEANUP_WS,
]


# Default canonical set used by compact_l1() when no variant
# specified — V3, the discourse-conscious mid-aggressive set.
CANONICAL = VARIANT_V3_DISCOURSE


VARIANTS = {
    'V1_minimal':     VARIANT_V1_MINIMAL,
    'V2_structural':  VARIANT_V2_STRUCTURAL,
    'V3_discourse':   VARIANT_V3_DISCOURSE,
    'V4_aggressive':  VARIANT_V4_AGGRESSIVE,
}
