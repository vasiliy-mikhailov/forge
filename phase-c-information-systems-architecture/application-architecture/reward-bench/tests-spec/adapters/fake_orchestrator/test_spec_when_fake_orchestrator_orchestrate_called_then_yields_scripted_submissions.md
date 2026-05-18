# `test_when_fake_orchestrator_orchestrate_called_then_yields_scripted_submissions`

Pins the `FakeOrchestrator` shape — the `Orchestrator` Port's test
double under the ADR-0018 Port + Fake convention. Used by the
dominance harness and any unit test that needs a controllable
orchestrator result.

- **Arrange**: two scripted Submissions `a, b`. Construct
  `FakeOrchestrator(submissions=(a, b))`.
- **Act**: `list(fake.orchestrate(env=None, cfg=None))`.
- **Assert**: result equals `[a, b]`.

Test code: [`../../../tests/adapters/test_fake_orchestrator.py`](../../../tests/adapters/test_fake_orchestrator.py)::`test_when_fake_orchestrator_orchestrate_called_then_yields_scripted_submissions`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — scripted in-memory adapter; no IO.
