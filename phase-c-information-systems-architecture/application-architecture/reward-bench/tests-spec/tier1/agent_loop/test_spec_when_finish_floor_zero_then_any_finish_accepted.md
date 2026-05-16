# `test_when_finish_floor_zero_then_any_finish_accepted`

Pins the **default / back-compat** path of the cycle-50 finish-floor
contract: when `finish_floor=0.0` (the BenchConfig default), the
bench accepts ANY `finish` call regardless of `best_dev_mean`.

Negative-control for the floored-rejection test. Confirms that
smoke configs and any legacy campaign relying on
"model decides when to finish" are not broken by the cycle-50
addition.

- **Arrange**: stub `_call_model` to emit a `finish` immediately
  with `best_dev_mean = None` (no execute_submission run yet).
- **Act**: `run_loop(..., finish_floor=0.0)`.
- **Assert**: `result['finished'] is True` after iter 1; loop
  exits without running another `_call_model`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

