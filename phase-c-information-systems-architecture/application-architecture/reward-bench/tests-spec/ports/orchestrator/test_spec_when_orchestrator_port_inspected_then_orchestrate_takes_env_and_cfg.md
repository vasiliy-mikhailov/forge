# `test_when_orchestrator_port_inspected_then_orchestrate_takes_env_and_cfg`

Pins the `Orchestrator` Port per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7. `Orchestrator` is the seam both strategies implement:

    orchestrate :: Env -> BenchConfig -> [Submission]

Keeps the bench-side independent of any agent framework (OpenHands,
ralph, future) — the port is the contract; adapters wrap whichever
framework runs underneath.

- **Arrange**: import `Orchestrator` from `src.ports.orchestrator`;
  `inspect.signature(Orchestrator.orchestrate)`.
- **Act**: read the parameter names.
- **Assert**: parameter list is exactly `['self', 'env', 'cfg']`.

Test code: [`../../../tests/ports/test_orchestrator.py`](../../../tests/ports/test_orchestrator.py)::`test_when_orchestrator_port_inspected_then_orchestrate_takes_env_and_cfg`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — Protocol method-signature contract; no runtime boundary involved.
