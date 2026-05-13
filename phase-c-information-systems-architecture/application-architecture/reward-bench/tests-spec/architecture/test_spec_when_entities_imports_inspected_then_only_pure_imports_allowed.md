# `test_when_entities_imports_inspected_then_only_pure_imports_allowed`

Architectural test spec. Pins the innermost layer of the Clean
Architecture dependency graph: `src/entities/` modules MUST NOT import
HTTP libraries, subprocess, docker, OS access, or any outer src/ layer.
Entities are pure domain types.

- **Arrange**: locate every `.py` file under `src/entities/`
  (recursively). The directory MUST exist and contain at least one
  non-empty file beyond `__init__.py`.
- **Act**: parse each file via `ast.parse`; collect every module name
  appearing in `Import` and `ImportFrom` nodes.
- **Assert**: no collected name starts with any of:
    - `urllib`, `http`, `requests`, `httpx`, `aiohttp`
    - `subprocess`, `docker`, `os`, `socket`
    - `src.use_cases`, `src.adapters`, `src.frameworks`
  When the assertion fails, the message names the offending file and
  the import that triggered it.

This is NOT a behavioral test — it pins a static layering invariant.

Test code: [`tests/architecture/test_dependency_direction.py`](../../tests/architecture/test_dependency_direction.py).
