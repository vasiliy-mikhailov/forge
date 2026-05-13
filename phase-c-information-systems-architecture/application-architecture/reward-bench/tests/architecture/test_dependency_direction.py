"""Architectural test specs: dependency direction across src/ layers.

Multi-module monolith: src/ is a container of modules, each module
(src/tier1/, eventually src/reward_bench/) has its own four-layer
clean-arch. Dependency-direction tests run per-module.

See tests-spec/architecture/ for the per-rule test specs."""
import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SRC = REPO / 'src'


# Per-layer forbidden import prefixes. Names with {m} are module-scoped
# and the helper substitutes the concrete module name.
_FORBIDDEN_FOR_ENTITIES = (
    'urllib', 'http', 'requests', 'httpx', 'aiohttp',
    'subprocess', 'docker', 'os', 'socket',
    'src.{m}.use_cases', 'src.{m}.adapters', 'src.{m}.frameworks',
)

_FORBIDDEN_FOR_USE_CASES = (
    'urllib', 'http', 'requests', 'httpx', 'aiohttp',
    'subprocess', 'docker', 'os', 'socket',
    'src.{m}.adapters', 'src.{m}.frameworks',
)

_FORBIDDEN_FOR_ADAPTERS = (
    'src.{m}.frameworks',
)


def _collect_imports(py_file):
    tree = ast.parse(py_file.read_text())
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def _modules():
    """Return module folders under src/ that are clean-arch units."""
    out = []
    for child in SRC.iterdir():
        if not child.is_dir() or child.name.startswith('_'):
            continue
        # A clean-arch unit module has at least one of the four layers.
        names = {p.name for p in child.iterdir() if p.is_dir()}
        if names & {'entities', 'use_cases', 'adapters', 'frameworks'}:
            out.append(child)
    return out


def _assert_layer_imports_clean(module_dir, layer_name, forbidden_template):
    """For module/layer/, ast-walk every .py and assert no forbidden imports."""
    layer_dir = module_dir / layer_name
    if not layer_dir.is_dir():
        return  # layer may not yet exist for a young module
    files = [p for p in layer_dir.rglob('*.py') if p.name != '__init__.py']
    if not files:
        return  # layer present but empty
    forbidden = tuple(t.format(m=module_dir.name) for t in forbidden_template)
    for f in files:
        imports = _collect_imports(f)
        for imp in imports:
            for fb in forbidden:
                assert not imp.startswith(fb), (
                    f'{f.relative_to(REPO)}: forbidden import {imp!r} '
                    f'(starts with {fb!r})'
                )


def test_when_entities_imports_inspected_then_only_pure_imports_allowed():
    # Arrange
    modules = _modules()
    assert modules, f'no modules under {SRC}'

    # Act + Assert per module
    for module in modules:
        _assert_layer_imports_clean(module, 'entities', _FORBIDDEN_FOR_ENTITIES)


def test_when_use_cases_imports_inspected_then_no_outer_imports():
    # Arrange
    modules = _modules()
    assert modules, f'no modules under {SRC}'

    # Act + Assert per module
    for module in modules:
        _assert_layer_imports_clean(module, 'use_cases', _FORBIDDEN_FOR_USE_CASES)


def test_when_adapters_imports_inspected_then_no_framework_imports():
    # Arrange
    modules = _modules()
    assert modules, f'no modules under {SRC}'

    # Act + Assert per module
    for module in modules:
        _assert_layer_imports_clean(module, 'adapters', _FORBIDDEN_FOR_ADAPTERS)
