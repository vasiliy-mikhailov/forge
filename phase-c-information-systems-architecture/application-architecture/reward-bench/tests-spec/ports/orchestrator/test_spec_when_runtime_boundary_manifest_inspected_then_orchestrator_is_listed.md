# `test_when_runtime_boundary_manifest_inspected_then_orchestrator_is_listed`

Pins the §7 `Orchestrator` Port registration in the runtime-boundary
manifest per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md).

The architecture fitness function
`test_when_runtime_boundary_port_inspected_then_protocol_exists` is
parametrized over `MANIFEST` in
`tests/architecture/test_runtime_boundary_ports.py`. Registration
in that list is what brings a Port under the rule "every
runtime-boundary dependency has Port + production adapter".

- **Arrange**: locate
  `tests/architecture/test_runtime_boundary_ports.py`.
- **Act**: read the file as text.
- **Assert**: the literal `"Orchestrator"` appears in the file.

Test code: [`../../../tests/ports/test_orchestrator.py`](../../../tests/ports/test_orchestrator.py)::`test_when_runtime_boundary_manifest_inspected_then_orchestrator_is_listed`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — text scan of an architecture manifest file.
