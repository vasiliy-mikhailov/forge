# `test_when_use_cases_imports_inspected_then_no_outer_imports`

Architectural test spec. Pins the second layer of the Clean
Architecture dependency graph: `src/use_cases/` modules MUST NOT
import HTTP libraries, subprocess, docker, the OS, or any outer
src/ layer (adapters/, frameworks/). They MAY import from
`src.entities` and standard-library pure-data modules.

- **Arrange**: locate every `.py` file under `src/use_cases/`
  (recursively). The directory MUST exist and contain at least one
  non-empty file beyond `__init__.py`.
- **Act**: parse each file via `ast.parse`; collect every module name
  appearing in `Import` and `ImportFrom` nodes.
- **Assert**: no collected name starts with any of:
    - `urllib`, `http`, `requests`, `httpx`, `aiohttp`
    - `subprocess`, `docker`, `os`, `socket`
    - `src.adapters`, `src.frameworks`

Test code: [`tests/architecture/test_dependency_direction.py`](../../tests/architecture/test_dependency_direction.py).
