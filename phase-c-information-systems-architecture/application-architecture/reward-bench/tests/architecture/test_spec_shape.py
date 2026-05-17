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
SRC_SPEC = REPO_ROOT / "src-spec"


_ARCHAEOLOGY_PATTERNS = (
    re.compile(r'\bcycle\s+\d+\b', re.IGNORECASE),
    re.compile(r'\bcycles\s+\d+', re.IGNORECASE),
    re.compile(r'\bADR\s+\d{2,4}\b'),
)

_PLACEHOLDER_PATTERN = re.compile(r'\(see test body[^)]*\)')

# Test code: [`<relative-path>`](<relative-path>)::`test_when_X_then_Y`.
_TEST_CODE_LINK_RE = re.compile(
    r'Test code:\s*\[`([^`]+\.py)`\]\([^)]+\)::`(test_when_[A-Za-z0-9_]+)`'
)

# Ratchet: decrement each cycle that rewrites a stub. When 0, the test
# becomes a strict equality and the defect class is permanently extinct.
EXPECTED_MAX_PLACEHOLDERS = 0

# Ratchet: residual aggregator specs (multi-test, violate one-spec-per-
# behavior) + orphan specs (reference deleted tests). Decrement as
# each is migrated or removed in subsequent cycles.
EXPECTED_MAX_LINK_VIOLATIONS = 0


def _discover_test_specs() -> tuple[Path, ...]:
    """All test_spec_*.md under tests-spec/, EXCEPT the architecture/
    meta-test directory (those specs describe defect patterns by name
    and would self-trigger)."""
    return tuple(
        p for p in sorted(TESTS_SPEC.rglob("test_spec_*.md"))
        if "architecture" not in p.parts
    )


def _discover_src_specs() -> tuple[Path, ...]:
    """All src_spec_*.md under src-spec/."""
    return tuple(sorted(SRC_SPEC.rglob("src_spec_*.md")))


def _archaeology_violations(specs: tuple[Path, ...]) -> list[tuple[str, int, str]]:
    out: list[tuple[str, int, str]] = []
    for spec in specs:
        for lineno, line in enumerate(spec.read_text().splitlines(), start=1):
            for pat in _ARCHAEOLOGY_PATTERNS:
                if pat.search(line):
                    rel = spec.relative_to(REPO_ROOT)
                    out.append((str(rel), lineno, line.strip()[:120]))
                    break
    return out


def test_when_test_spec_corpus_walked_then_no_cycle_archaeology_present():
    """Arrange / Act / Assert."""
    # Arrange
    specs = _discover_test_specs()
    assert specs, f"no test_specs found under {TESTS_SPEC}"

    # Act
    violations = _archaeology_violations(specs)

    # Assert
    if violations:
        head = '\n'.join(
            f'  {p}:{ln}  {snippet}' for p, ln, snippet in violations[:20]
        )
        more = f'\n  ... and {len(violations) - 20} more' if len(violations) > 20 else ''
        pytest.fail(
            f'cycle/ADR archaeology in {len(violations)} test_spec line(s) '
            f'(git-is-history rule):\n{head}{more}'
        )


def test_when_src_spec_corpus_walked_then_no_cycle_archaeology_present():
    """Arrange / Act / Assert."""
    # Arrange
    specs = _discover_src_specs()
    assert specs, f"no src_specs found under {SRC_SPEC}"

    # Act
    violations = _archaeology_violations(specs)

    # Assert
    if violations:
        head = '\n'.join(
            f'  {p}:{ln}  {snippet}' for p, ln, snippet in violations[:20]
        )
        more = f'\n  ... and {len(violations) - 20} more' if len(violations) > 20 else ''
        pytest.fail(
            f'cycle/ADR archaeology in {len(violations)} src_spec line(s) '
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


def test_when_test_spec_links_followed_then_referenced_test_function_exists():
    """Arrange / Act / Assert.

    Every test_spec_*.md ends with a `Test code:` link pointing at a
    test function. This fitness function verifies the link resolves:
    the .py file exists and the test function is defined in it.
    """
    # Arrange
    specs = _discover_test_specs()
    assert specs, f"no test_specs found under {TESTS_SPEC}"

    # Act
    violations: list[str] = []
    for spec in specs:
        text = spec.read_text()
        m = _TEST_CODE_LINK_RE.search(text)
        if not m:
            violations.append(f'{spec.relative_to(REPO_ROOT)}: '
                              f'no `Test code:` link found')
            continue
        rel_path, func_name = m.group(1), m.group(2)
        resolved = (spec.parent / rel_path).resolve()
        if not resolved.exists():
            violations.append(f'{spec.relative_to(REPO_ROOT)}: '
                              f'link target missing: {rel_path}')
            continue
        # Function existence: grep for `def {name}(`. Cheap, robust.
        try:
            src = resolved.read_text()
        except Exception as e:
            violations.append(f'{spec.relative_to(REPO_ROOT)}: '
                              f'unreadable {rel_path}: {e}')
            continue
        if not re.search(rf'\bdef\s+{re.escape(func_name)}\s*\(', src):
            violations.append(f'{spec.relative_to(REPO_ROOT)}: '
                              f'function `{func_name}` not defined in '
                              f'{rel_path}')

    # Assert (ratchet: residual aggregator + orphan specs)
    if len(violations) > EXPECTED_MAX_LINK_VIOLATIONS:
        head = '\n'.join(f'  {v}' for v in violations[:20])
        more = (f'\n  ... and {len(violations) - 20} more'
                if len(violations) > 20 else '')
        pytest.fail(
            f'{len(violations)} test_spec → test-code link violation(s); '
            f'ratchet expected at most {EXPECTED_MAX_LINK_VIOLATIONS}. '
            f'Either fix the link, rename the test, or remove the orphan '
            f'spec:\n{head}{more}'
        )
