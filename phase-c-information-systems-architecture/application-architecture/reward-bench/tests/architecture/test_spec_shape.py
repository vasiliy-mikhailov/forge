"""Corpus-wide fitness functions for the spec corpus.

Asserted properties:
- No cycle/ADR archaeology in test_spec bodies (git-is-history rule).
- Placeholder count (`(see test body)`) bounded by a ratchet that
  decreases as stubs are rewritten cycle-by-cycle.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_SPEC = REPO_ROOT / "tests-spec"


_ARCHAEOLOGY_PATTERNS = (
    re.compile(r'\bcycle\s+\d+\b', re.IGNORECASE),
    re.compile(r'\bcycles\s+\d+', re.IGNORECASE),
    re.compile(r'\bADR\s+\d{2,4}\b'),
)

_PLACEHOLDER_PATTERN = re.compile(r'\(see test body[^)]*\)')

# Ratchet: decrement each cycle that rewrites a stub. When 0, the test
# becomes a strict equality and the defect class is permanently extinct.
EXPECTED_MAX_PLACEHOLDERS = 0


def _discover_test_specs() -> tuple[Path, ...]:
    """All test_spec_*.md under tests-spec/, EXCEPT the architecture/
    meta-test directory (those specs describe defect patterns by name
    and would self-trigger)."""
    return tuple(
        p for p in sorted(TESTS_SPEC.rglob("test_spec_*.md"))
        if "architecture" not in p.parts
    )


def test_when_test_spec_corpus_walked_then_no_cycle_archaeology_present():
    """Arrange / Act / Assert."""
    # Arrange
    specs = _discover_test_specs()
    assert specs, f"no test_specs found under {TESTS_SPEC}"

    # Act
    violations: list[tuple[str, int, str]] = []
    for spec in specs:
        for lineno, line in enumerate(spec.read_text().splitlines(), start=1):
            for pat in _ARCHAEOLOGY_PATTERNS:
                if pat.search(line):
                    rel = spec.relative_to(REPO_ROOT)
                    violations.append((str(rel), lineno, line.strip()[:120]))
                    break

    # Assert
    if violations:
        head = '\n'.join(
            f'  {p}:{ln}  {snippet}' for p, ln, snippet in violations[:20]
        )
        more = f'\n  ... and {len(violations) - 20} more' if len(violations) > 20 else ''
        pytest.fail(
            f'cycle/ADR archaeology in {len(violations)} spec line(s) '
            f'(git-is-history rule):\n{head}{more}'
        )


def test_when_test_spec_corpus_walked_then_placeholder_count_at_or_below_known_max():
    """Arrange / Act / Assert."""
    # Arrange
    specs = _discover_test_specs()
    assert specs, f"no test_specs found under {TESTS_SPEC}"

    # Act
    violations: list[str] = []
    for spec in specs:
        if _PLACEHOLDER_PATTERN.search(spec.read_text()):
            violations.append(str(spec.relative_to(REPO_ROOT)))

    # Assert
    if len(violations) > EXPECTED_MAX_PLACEHOLDERS:
        head = '\n'.join(f'  {p}' for p in violations[:20])
        more = (f'\n  ... and {len(violations) - 20} more'
                if len(violations) > 20 else '')
        pytest.fail(
            f'{len(violations)} test_specs still contain placeholder text '
            f'`(see test body ...)`; ratchet expected at most '
            f'{EXPECTED_MAX_PLACEHOLDERS}. Spec-rewrite cycles must be '
            f'monotonically lowering this; a regression is in:\n{head}{more}'
        )
