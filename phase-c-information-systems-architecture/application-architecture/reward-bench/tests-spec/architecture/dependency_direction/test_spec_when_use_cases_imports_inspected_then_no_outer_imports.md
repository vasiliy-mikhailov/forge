# `test_when_use_cases_imports_inspected_then_no_outer_imports`

Architectural test spec. Pins the second layer of the Clean
Architecture dependency graph: `src/<module>/use_cases/` modules MUST NOT
import HTTP libraries, subprocess, docker, the OS, or any outer
src/ layer (adapters/, frameworks/). They MAY import from
`src.tier1.entities` and standard-library pure-data modules.

- **Arrange**: locate every `.py` file under `src/<module>/use_cases/`
  (recursively). The directory MUST exist and contain at least one
  non-empty file beyond `__init__.py`.
- **Act**: parse each file via `ast.parse`; collect every module name
  appearing in `Import` and `ImportFrom` nodes.
- **Assert**: no collected name starts with any of:
    - `urllib`, `http`, `requests`, `httpx`, `aiohttp`
    - `subprocess`, `docker`, `os`, `socket`
    - `src.<module>.adapters`, `src.<module>.frameworks`

Test code: [`tests/architecture/test_dependency_direction.py`](../../tests/architecture/test_dependency_direction.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — static AST import-graph assertion; not runtime-dependent.

