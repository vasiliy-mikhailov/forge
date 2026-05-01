"""K2-R1 — TDD tests for compact() L1 (Air-strip) and restore() L1.

Per ADR 0013 the spec is the md (`phase-f-migration-planning/
experiments/K2-compact-restore.md`); this file is the unit tests
that drive implementation.

TDD discipline (per architecture-principles.md P5: prefer the
cheap experiment): every assertion below MUST be runnable on CPU
in < 1 s without GPU / network / sibling-repo access. The L1
algorithm is pure string/regex and has no LLM calls — that is
precisely what makes it the cheap floor.

The tests fix the contract:
  - Filler patterns (Air) are dropped.
  - Substance and Form observations survive.
  - Output schema matches the K2 spec frontmatter + sections.
  - Compression ratio is in the L1 hypothesis band (0.55..0.85).
  - restore_l1(compact_l1(x)) == compact_l1(x) — L1 is lossless
    on its own, restore for L1 is identity.

Tests run against fixtures/k2/lecture_A_synth.json (synthetic
Cyrillic transcript mirroring the structure of real lecture A).
"""
from __future__ import annotations
import json
import re
import sys
import unicodedata
from pathlib import Path

import pytest

THIS_DIR = Path(__file__).resolve().parent
LAB = THIS_DIR.parents[1]
FIXTURE = THIS_DIR / 'fixtures' / 'k2' / 'lecture_A_synth.json'

sys.path.insert(0, str(LAB))
from compact_restore.compact import compact_l1   # noqa: E402
from compact_restore.restore import restore_l1   # noqa: E402


# ─────────────── fixture helpers ───────────────

@pytest.fixture
def raw():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


@pytest.fixture
def transcript(raw):
    return raw['transcript']


@pytest.fixture
def compacted(raw):
    """Default compact_l1 with the canonical filler set."""
    return compact_l1(raw)


def _norm(s):
    return unicodedata.normalize('NFC', s).lower()


# ─────────────── Air-strip tests (RED before implementation) ───────────────

class TestAirStrip:
    def test_drops_vocalised_hesitations(self, compacted, transcript):
        """'Эээ' / 'ээ' filler tokens MUST not survive L1."""
        body = compacted['transcript']
        # The raw fixture has 'эээ' multiple times
        assert 'эээ' in _norm(transcript), 'fixture should contain эээ'
        assert 'эээ' not in _norm(body), \
            f'L1 leaked vocalised hesitation: {body[:200]}'

    def test_drops_triple_trail_i_tak_dalee(self, compacted, transcript):
        """'и так далее, и так далее, и так далее' (≥2 repetitions
        adjacent) MUST collapse to nothing in L1."""
        norm = _norm(compacted['transcript'])
        # Original fixture has the triple-trail in two places
        assert _norm(transcript).count('и так далее') >= 5, \
            'fixture should have multiple и-так-далее'
        # After L1, no stretch of ≥2 adjacent 'и так далее' may remain
        assert not re.search(r'и так далее[\s,.]*и так далее', norm), \
            f'L1 left adjacent и-так-далее: …{norm[max(0,norm.find("и так далее")-30):norm.find("и так далее")+200]}…'

    def test_drops_word_doubling(self, compacted):
        """'эмпатические эмпатические' (adjacent identical word) MUST
        reduce to a single occurrence in L1."""
        norm = _norm(compacted['transcript'])
        # No adjacent identical Cyrillic word repeats
        m = re.search(r'\b([а-яё]{4,})\s+\1\b', norm)
        assert m is None, f'L1 left word-doubling: {m.group(0)}'

    def test_drops_tripled_word(self, compacted):
        """'стрессом, стрессом, стрессом' MUST reduce to a single
        occurrence in L1."""
        norm = _norm(compacted['transcript'])
        # No 3+ comma-separated identical words
        m = re.search(r'\b([а-яё]{4,})[\s,]+\1[\s,]+\1\b', norm)
        assert m is None, f'L1 left triple-word: {m.group(0)}'

    def test_drops_triple_phrase_repeat(self, compacted):
        """'представьте себе, представьте себе, представьте себе'
        — phrase-level triple-repeat MUST reduce."""
        norm = _norm(compacted['transcript'])
        # The phrase 'представьте себе' appears 3× in raw; ≤1 in L1
        count = norm.count('представьте себе')
        assert count <= 1, \
            f'L1 left {count} occurrences of "представьте себе" (expected ≤ 1)'


# ─────────────── Substance + Form preservation tests ───────────────

class TestPreservation:
    SUBSTANCE_VERBATIMS = [
        'Ганс Селье',
        'Лимбическая система устроена ядрами',
        'Базовые потребности',
        'согласно нашей генетической программе',
    ]
    FORM_VERBATIMS = [
        'представьте себе ситуацию',
        'Курпатов сам автор СПП',
        'Контакт, рапорт, доверительные отношения',
        'Конфликт биологии и культуры',
    ]

    @pytest.mark.parametrize('verbatim', SUBSTANCE_VERBATIMS)
    def test_substance_survives(self, compacted, verbatim):
        body = _norm(compacted['transcript'])
        assert _norm(verbatim) in body, \
            f'L1 dropped Substance: {verbatim!r}'

    @pytest.mark.parametrize('verbatim', FORM_VERBATIMS)
    def test_form_survives(self, compacted, verbatim):
        body = _norm(compacted['transcript'])
        assert _norm(verbatim) in body, \
            f'L1 dropped Form: {verbatim!r}'


# ─────────────── Schema tests ───────────────

class TestSchema:
    def test_has_required_top_level_keys(self, compacted):
        for k in ('stem', 'course', 'module', 'transcript',
                  'compact_metadata'):
            assert k in compacted, f'missing top-level key {k!r}'

    def test_compact_metadata_carries_layer_and_ratio(self, compacted):
        meta = compacted['compact_metadata']
        assert meta['layer'] == 'L1', \
            f'expected layer L1, got {meta["layer"]!r}'
        assert 0.0 < meta['compression_ratio'] < 1.0, \
            f'compression_ratio out of range: {meta["compression_ratio"]}'
        assert 'filler_patterns_applied' in meta
        assert 'tok_original' in meta and 'tok_compact' in meta

    def test_stem_preserved(self, compacted, raw):
        assert compacted['stem'] == raw['stem']


# ─────────────── Compression-ratio band tests ───────────────

class TestRatio:
    def test_l1_ratio_in_hypothesis_band(self, compacted):
        """K2 hypothesis: L1 alone target ratio 0.55..0.85
        (i.e. saved-time 15..45%). Below 0.55 means Substance
        is leaking; above 0.85 means L1 is too timid."""
        ratio = compacted['compact_metadata']['compression_ratio']
        assert 0.55 <= ratio <= 0.85, \
            f'L1 ratio {ratio} outside band [0.55, 0.85]'


# ─────────────── Restore L1 tests ───────────────

class TestRestoreL1Identity:
    def test_restore_l1_is_identity(self, compacted):
        """L1 is lossless on its own (no pointers / concept-graph
        deltas needed), so restore_l1(compact_l1(x)) MUST equal
        compact_l1(x). Both ways round-trip the same content."""
        restored = restore_l1(compacted)
        assert restored['transcript'] == compacted['transcript']
        assert restored['stem'] == compacted['stem']

    def test_restore_l1_preserves_compact_metadata(self, compacted):
        restored = restore_l1(compacted)
        assert 'compact_metadata' in restored
        assert restored['compact_metadata']['layer'] == 'L1'
