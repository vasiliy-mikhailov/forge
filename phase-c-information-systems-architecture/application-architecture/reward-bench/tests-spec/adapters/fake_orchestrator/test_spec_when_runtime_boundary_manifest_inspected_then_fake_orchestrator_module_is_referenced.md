# `test_when_runtime_boundary_manifest_inspected_then_fake_orchestrator_module_is_referenced`

Closes the ADR-0018 Port + Fake invariant for the §7 `Orchestrator`
Port: the manifest entry references the fake module, so the
parametric fitness test
`test_when_runtime_boundary_port_has_fake_then_fake_class_importable`
auto-extends to cover Orchestrator.

- **Arrange**: locate
  `tests/architecture/test_runtime_boundary_ports.py`.
- **Act**: read the file as text.
- **Assert**: the literal `"fake_orchestrator"` appears in the file.

Test code: [`../../../tests/adapters/test_fake_orchestrator.py`](../../../tests/adapters/test_fake_orchestrator.py)::`test_when_runtime_boundary_manifest_inspected_then_fake_orchestrator_module_is_referenced`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — text scan of an architecture manifest file.
