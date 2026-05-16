# `test_when_finish_called_below_finish_floor_via_execute_submission_then_rejected_and_loop_continues`

Sibling of [`test_when_finish_called_below_finish_floor_then_rejected_and_loop_continues`](
test_spec_when_finish_called_below_finish_floor_then_rejected_and_loop_continues.md).
Pins the same finish-floor contract but routes the best_dev_mean
via the cycle-58 `execute_submission` observation pipeline (cycle 64).

When the model calls `finish` while `best_dev_mean < finish_floor`
AND the only source of `best_dev_mean` so far has been
`execute_submission` JSON observations (not legacy bash dev_runner
stdout), the loop MUST still reject the finish and continue
iterating. The cycle-63 parser reads `<observation>{...mean...}</observation>`
into the `best_dev_mean` tracker that the finish-floor check uses.

- **Arrange**: stub `_call_model` to emit `execute_submission`
  observations carrying `dev_mean < finish_floor`, then a `finish`.
- **Act**: `run_loop(..., finish_floor=7211.0)`.
- **Assert**: `result['finished'] is False` after the rejected
  finish; the loop continues until max_iters or a higher-scoring
  finish.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

