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

# Ratchet: tests defined under tests/ without a corresponding
# test_spec_when_X.md anywhere in tests-spec/. Decrement as each is
# either spec'd or removed.
EXPECTED_MAX_ORPHAN_TESTS = 32

# Ratchet: src_spec_*.md files missing or referencing a non-existent
# `src/...py` link.
EXPECTED_MAX_SRC_LINK_VIOLATIONS = 41

# Ratchet: src/*.py modules not referenced by any src_spec.
EXPECTED_MAX_ORPHAN_SRC_MODULES = 0


TESTS_DIR = REPO_ROOT / "tests"
SRC_DIR = REPO_ROOT / "src"

_TEST_FUNC_RE = re.compile(r'^def\s+(test_when_[A-Za-z0-9_]+)\s*\(', re.MULTILINE)
_SRC_LINK_RE = re.compile(
    r'\[`([^`]+\.py)`\]\([^)]+\)|`(src/[A-Za-z0-9_/.]+\.py)`'
)


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


def test_when_test_functions_walked_then_each_has_a_corresponding_test_spec():
    """Arrange / Act / Assert.

    Every `test_when_X_then_Y` function in tests/ must have a
    corresponding `test_spec_when_X_then_Y.md` somewhere under
    tests-spec/. Enforces the CATS "no code without a spec" rule
    from the side of code-already-exists-but-spec-doesn't.
    """
    # Arrange: collect all test_when_X function names in tests/.
    test_funcs: dict[str, list[Path]] = {}
    for f in TESTS_DIR.rglob("*.py"):
        for m in _TEST_FUNC_RE.finditer(f.read_text()):
            test_funcs.setdefault(m.group(1), []).append(f)

    # Arrange: collect spec stems (test_spec_when_X_then_Y.md -> test_when_X_then_Y).
    spec_funcs: set[str] = set()
    for spec in TESTS_SPEC.rglob("test_spec_when_*.md"):
        if "architecture" in spec.parts:
            continue
        spec_funcs.add("test_" + spec.stem[len("test_spec_"):])

    # Act
    orphans = [name for name in sorted(test_funcs) if name not in spec_funcs]

    # Assert
    if len(orphans) > EXPECTED_MAX_ORPHAN_TESTS:
        head = '\n'.join(
            f'  {name}  (in {test_funcs[name][0].relative_to(REPO_ROOT)})'
            for name in orphans[:20]
        )
        more = (f'\n  ... and {len(orphans) - 20} more'
                if len(orphans) > 20 else '')
        pytest.fail(
            f'{len(orphans)} test function(s) without a corresponding '
            f'test_spec_*.md; ratchet expected at most '
            f'{EXPECTED_MAX_ORPHAN_TESTS}. Write a spec or remove the '
            f'test:\n{head}{more}'
        )


def _src_spec_link_target(spec: Path) -> Path | None:
    """Return the resolved path of the first `[`src/X.py`](rel-path)` link
    in the spec, or None if no such link found."""
    text = spec.read_text()
    for m in _SRC_LINK_RE.finditer(text):
        # group 1: relative-path link  group 2: bare src/...  bracket form
        rel = m.group(1)
        if rel and rel.startswith("..") and rel.endswith(".py"):
            resolved = (spec.parent / rel).resolve()
            if str(resolved).startswith(str(SRC_DIR.parent)):
                return resolved
        bare = m.group(2)
        if bare:
            return (REPO_ROOT / bare).resolve()
    return None


def test_when_src_spec_walked_then_first_src_link_resolves_to_existing_module():
    """Arrange / Act / Assert.

    Every src_spec_*.md should name the src/ module it describes. We
    parse for the first `src/...py` link and assert it exists.
    """
    # Arrange
    specs = _discover_src_specs()
    assert specs, f"no src_specs found under {SRC_SPEC}"

    # Act
    violations: list[str] = []
    for spec in specs:
        target = _src_spec_link_target(spec)
        rel = spec.relative_to(REPO_ROOT)
        if target is None:
            violations.append(f'{rel}: no `src/...py` link found')
            continue
        if not target.exists():
            violations.append(
                f'{rel}: link target missing: '
                f'{target.relative_to(REPO_ROOT)}'
            )

    # Assert
    if len(violations) > EXPECTED_MAX_SRC_LINK_VIOLATIONS:
        head = '\n'.join(f'  {v}' for v in violations[:20])
        more = (f'\n  ... and {len(violations) - 20} more'
                if len(violations) > 20 else '')
        pytest.fail(
            f'{len(violations)} src_spec → src/ link violation(s); '
            f'ratchet expected at most {EXPECTED_MAX_SRC_LINK_VIOLATIONS}.'
            f'\n{head}{more}'
        )


def _all_src_modules() -> list[Path]:
    """All non-trivial Python modules under src/ (excluding __init__.py
    and __pycache__/)."""
    out = []
    for f in sorted(SRC_DIR.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        if f.name == "__init__.py":
            continue
        out.append(f)
    return out


def test_when_src_modules_walked_then_each_referenced_by_at_least_one_src_spec():
    """Arrange / Act / Assert.

    Every non-trivial src/*.py module must be referenced by at least
    one src_spec_*.md (anywhere in its text — link, code-block, or
    backtick mention). Catches orphan source modules.
    """
    # Arrange
    modules = _all_src_modules()
    assert modules, f"no src modules found under {SRC_DIR}"
    specs_text = "\n".join(s.read_text() for s in _discover_src_specs())

    # Act
    orphans: list[str] = []
    for mod in modules:
        rel = str(mod.relative_to(REPO_ROOT))         # e.g. "src/ports/tool.py"
        dotted = rel[:-3].replace('/', '.')           # "src.ports.tool"
        if rel in specs_text or dotted in specs_text:
            continue
        orphans.append(rel)

    # Assert
    if len(orphans) > EXPECTED_MAX_ORPHAN_SRC_MODULES:
        head = '\n'.join(f'  {v}' for v in orphans[:20])
        more = (f'\n  ... and {len(orphans) - 20} more'
                if len(orphans) > 20 else '')
        pytest.fail(
            f'{len(orphans)} src module(s) not referenced by any '
            f'src_spec; ratchet expected at most '
            f'{EXPECTED_MAX_ORPHAN_SRC_MODULES}:\n{head}{more}'
        )
