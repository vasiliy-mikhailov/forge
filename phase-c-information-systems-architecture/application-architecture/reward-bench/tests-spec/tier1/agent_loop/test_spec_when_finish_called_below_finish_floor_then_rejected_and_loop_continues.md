# `test_when_finish_called_below_finish_floor_then_rejected_and_loop_continues`

Pins the **finish-floor** seam in `run_loop`. The loop rejects
`finish` when `best_dev_mean < finish_floor` (default 7211 = the
reference_fsm baseline). When rejected, the tool observation is a
clear error
message and the loop CONTINUES — the model is forced to:

1. Actually obtain a dev MEAN signal before claiming done.
2. Iterate until its submission scores above the floor.

Cycle 49 discovered the active loop without this guardrail lets the
model write a Solver-less submission and call `finish` on turn 1,
which sentinels the trial. Cycle-48 best-snapshot can never fire
because the model never produced dev-mean data.

The data source for `best_dev_mean` depends on which tool the model
uses:

- **Active path** ([ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md)):
  `execute_submission` returns a structured JSON observation whose
  `mean` field updates `best_dev_mean`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

