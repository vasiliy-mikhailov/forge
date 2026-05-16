# `test_when_supervisor_every_k_zero_then_supervisor_not_consulted`

Pins the **back-compat / default-off** path for the supervisor
hook (cycle 33, [ADR 0005](../../../../docs/adr/0005-plateau-detection-supervisor-via-llm-self-judgment.md)).

When `supervisor_every_k=0` (the BenchConfig default), the bench
MUST never call the supervisor — regardless of whether one is
passed. This preserves cycle-12 behaviour and lets callers run the
bench without an ADR-0005 plateau-detection consult.

- **Arrange**: pass a recorder supervisor that asserts on call.
- **Act**: `run_loop(..., supervisor=recorder, supervisor_every_k=0)`
  with `max_iters >= 5`.
- **Assert**: recorder was called zero times after the loop ends.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

