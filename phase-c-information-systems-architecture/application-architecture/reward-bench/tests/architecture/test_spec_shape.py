"""Corpus-wide fitness functions for the spec corpus.

Asserted properties:
- No cycle/ADR archaeology in test_spec bodies (git-is-history rule).
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


def _discover_test_specs() -> tuple[Path, ...]:
    return tuple(sorted(TESTS_SPEC.rglob("test_spec_*.md")))


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
