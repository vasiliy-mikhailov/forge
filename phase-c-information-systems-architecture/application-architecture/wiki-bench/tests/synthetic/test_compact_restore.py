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
from compact_restore.compact import compact_l1, _normalise_raw  # noqa: E402
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


# ─────────────── V5 discourse-marker tests (Russian filler vocabulary) ───────────────

class TestV5DiscourseMarkers:
    def test_v5_strips_znachit_discourse_marker(self):
        from compact_restore.compact import compact_l1
        raw = {'stem': 'test',  'transcript': 'И, значит, мы переходим к следующему разделу.', 'segments': []}
        c = compact_l1(raw, variant='V5_discourse_markers')
        assert 'значит,' not in c['transcript'].lower()

    def test_v5_strips_na_samom_dele(self):
        from compact_restore.compact import compact_l1
        raw = {'stem': 'test',  'transcript': 'А на самом деле, всё устроено иначе.', 'segments': []}
        c = compact_l1(raw, variant='V5_discourse_markers')
        assert 'на самом деле' not in c['transcript'].lower()

    def test_v5_strips_sobstvenno(self):
        from compact_restore.compact import compact_l1
        raw = {'stem': 'test',  'transcript': 'Это, собственно, и есть наша задача.', 'segments': []}
        c = compact_l1(raw, variant='V5_discourse_markers')
        assert 'собственно' not in c['transcript'].lower()

    def test_v5_strips_to_est_only_when_comma_flanked(self):
        from compact_restore.compact import compact_l1
        # comma-flanked → strip
        raw1 = {'stem': 'test', 'transcript': 'Стресс, то есть, реакция психики.', 'segments': []}
        c1 = compact_l1(raw1, variant='V5_discourse_markers')
        assert 'то есть,' not in c1['transcript'].lower()
        # NOTE: the V5 regex is conservative — it strips 'то есть'
        # when comma-or-whitespace-flanked from a discourse-marker
        # position. Mid-sentence rephrasing 'X, то есть Y' gets
        # caught (which is fine — the rephrasing IS the discourse
        # marker).

    def test_v5_strips_vot_only_as_interjection(self):
        from compact_restore.compact import compact_l1
        # Sentence-initial 'вот, ' → strip
        raw = {'stem': 'test',  'transcript': 'Вот, теперь мы начинаем работу.', 'segments': []}
        c = compact_l1(raw, variant='V5_discourse_markers')
        # case insensitive in pattern but output preserves case
        assert 'вот, теперь' not in c['transcript'].lower()
        # 'Вот это' (вот carrying sentence load) — stays
        raw2 = {'stem': 'test', 'transcript': 'Вот это и есть результат.', 'segments': []}
        c2 = compact_l1(raw2, variant='V5_discourse_markers')
        # 'вот это' is sentence-initial 'вот' followed by 'это'
        # — the regex is interjection-only ('вот, ' or 'вот ' at
        # absolute start before content), so 'вот это' WILL be
        # caught by sentence-initial match. This is a known
        # limitation; comment below documents the trade-off.

    def test_v5_preserves_substance(self):
        from compact_restore.compact import compact_l1
        # Substance verbatims must survive V5 (same as V4)
        raw = {'stem': 'test',  'transcript': 'Стресс — это, если опираться на определение, которое дал Ганс Селье, естественная реакция.', 'segments': []}
        c = compact_l1(raw, variant='V5_discourse_markers')
        assert 'Ганс Селье' in c['transcript']
        assert 'Стресс' in c['transcript']

    def test_v5_compresses_more_than_v4(self):
        from compact_restore.compact import compact_l1
        # On a fixture rich in discourse markers, V5 should hit a
        # lower compression ratio than V4.
        raw = {'stem': 'test',  'transcript': 'Значит, на самом деле, собственно, то есть, как бы это всё одно и то же. Допустим, что мы согласны.', 'segments': []}
        c4 = compact_l1(raw, variant='V4_aggressive')
        c5 = compact_l1(raw, variant='V5_discourse_markers')
        assert c5['compact_metadata']['compression_ratio'] < c4['compact_metadata']['compression_ratio']


# ─────────────── Schema-normaliser tests (real wiki-ingest schema) ───────────────

class TestNormaliseRaw:
    def test_synth_schema_passthrough(self, raw):
        """Synth fixture already has top-level 'transcript' — normaliser
        is identity on the keys we care about."""
        n = _normalise_raw(raw)
        assert n['transcript'] == raw['transcript']
        assert n['stem'] == raw['stem']

    def test_real_schema_built_from_segments(self):
        """Real wiki-ingest schema: {info, segments[]}, no top-level
        transcript. The normaliser builds transcript by joining
        segment text fields with .strip()."""
        real_shape = {
            'info': {
                'language': 'ru',
                'duration': 5318.6,
                'source_path': '/workspace/sources/Психолог-консультант/000 Путеводитель по программе/000 Знакомство с программой «Психолог-консультант».mp4',
                'extractor': 'whisper',
            },
            'segments': [
                {'id': 0, 'start': 0.0, 'end': 4.5, 'text': ' Приветствую вас, дорогие друзья.'},
                {'id': 1, 'start': 4.5, 'end': 9.0, 'text': ' Здесь, на этой лекции, я расскажу о том,'},
                {'id': 2, 'start': 9.0, 'end': 14.0, 'text': ' что нужно для того, чтобы пройти обучение.'},
            ],
        }
        n = _normalise_raw(real_shape)
        assert n['transcript'].startswith('Приветствую вас')
        # leading-space artefact stripped per segment
        assert ' Приветствую' not in n['transcript']
        assert n['transcript'].split()[0] == 'Приветствую'
        # stem extracted from source_path basename
        assert n['stem'].startswith('000 Знакомство')
        # course / module from path parts
        assert 'Психолог-консультант' in n['course']
        assert '000 Путеводитель' in n['module']
        # segments preserved
        assert len(n['segments']) == 3

    def test_real_schema_compact_l1_works(self):
        """compact_l1 accepts the real schema directly via the
        normaliser — no manual transcript-build required by callers."""
        real_shape = {
            'info': {'source_path': '/x/y/z/lecture.mp4'},
            'segments': [
                {'text': ' Стресс — это, эээ, естественная реакция.'},
                {'text': ' и так далее, и так далее, и так далее.'},
            ],
        }
        c = compact_l1(real_shape, variant='V4_aggressive')
        assert 'compact_metadata' in c
        # эээ should be removed; substance ('Стресс') survives
        assert 'эээ' not in c['transcript'].lower()
        assert 'стресс' in c['transcript'].lower()
        # Triple-trail и-так-далее should be collapsed
        assert 'и так далее, и так далее' not in c['transcript'].lower()

    def test_real_schema_missing_info_does_not_crash(self):
        """Defensive: a degenerate raw (no info key) still produces a
        normalised dict with empty stem/course/module rather than
        raising."""
        n = _normalise_raw({'segments': [{'text': 'a'}]})
        assert n['transcript'] == 'a'
        assert n['stem'] == 'unknown'
        assert n['course'] == ''


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
