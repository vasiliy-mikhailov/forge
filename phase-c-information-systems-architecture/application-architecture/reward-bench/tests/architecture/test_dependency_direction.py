"""Architectural test specs: dependency direction across src/ layers.
See tests-spec/architecture/ for the per-rule test specs."""
import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


_FORBIDDEN_FOR_ENTITIES = (
    'urllib', 'http', 'requests', 'httpx', 'aiohttp',
    'subprocess', 'docker', 'os', 'socket',
    'src.use_cases', 'src.adapters', 'src.frameworks',
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


def test_when_entities_imports_inspected_then_only_pure_imports_allowed():
    # Arrange
    entities_dir = REPO / 'src' / 'entities'
    assert entities_dir.is_dir(), f'{entities_dir} does not exist'
    files = [p for p in entities_dir.rglob('*.py') if p.name != '__init__.py']
    assert files, f'no entity .py files under {entities_dir}'

    # Act + Assert per file
    for f in files:
        imports = _collect_imports(f)
        for imp in imports:
            for forbidden in _FORBIDDEN_FOR_ENTITIES:
                assert not imp.startswith(forbidden), (
                    f'{f.relative_to(REPO)}: forbidden import {imp!r} '
                    f'(starts with {forbidden!r})'
                )
