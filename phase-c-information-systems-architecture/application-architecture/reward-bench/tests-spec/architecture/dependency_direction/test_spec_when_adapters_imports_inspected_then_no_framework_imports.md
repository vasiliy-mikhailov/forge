# `test_when_adapters_imports_inspected_then_no_framework_imports`

Architectural test spec. Pins the third layer: `src/<module>/adapters/` modules
implement ports defined in `src/<module>/use_cases/`, wrapping concrete external
systems (the 2048 env, vLLM HTTP, Docker, filesystem). They MAY import
entities and use_cases. They MUST NOT import from `src.frameworks/` —
the framework layer is reserved for the lowest-level drivers, and
adapters bridge between ports and drivers without selecting drivers
themselves.

- **Arrange**: locate every `.py` file under `src/<module>/adapters/`.
  Directory MUST exist and contain at least one non-empty file.
- **Act**: ast-parse each file; collect import names.
- **Assert**: no name starts with `src.<module>.frameworks`.

Note: adapters MAY import HTTP / subprocess / docker stdlib if no
separate framework driver yet exists — those are concrete details
adapters legitimately know about. The frameworks/ layer is reserved
for cases where the adapter would otherwise grow too large.

Test code: [`tests/architecture/test_dependency_direction.py`](../../tests/architecture/test_dependency_direction.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — static AST import-graph assertion; not runtime-dependent.

