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
- **Legacy path** (deprecated; behind `--legacy-write-file`): `bash
  python3 /tasks/2048/dev_runner.py /workspace/submission.py` whose
  parsed stdout MEAN line updates `best_dev_mean`. The cycle-34
  parser already understands this format.

Both paths feed the same `best_dev_mean` accumulator and the same
finish-floor check.

- **Arrange**: stub `_call_model` to emit a scripted sequence under
  EITHER active or legacy tool:
    1. `finish` (no prior dev-mean — best unknown)
    2. dev-mean source returning `mean=100` (below floor)
    3. `finish` (best=100 < floor=200)
    4. dev-mean source returning `mean=500` (above floor)
    5. `finish` (best=500 > floor=200) — accepted.
- **Act**: `run_loop(..., max_iters=10, finish_floor=200.0)`.
- **Assert**:
  - `result['iterations'] == 5` (loop ran past 2 rejected finishes).
  - `result['finished'] is True` (the 3rd finish ABOVE floor was accepted).
  - At least one observation message contains `finish rejected` text.

Sibling test pins the default `finish_floor=0` keeps cycle-12 behaviour
(any finish accepted). No regression for existing tests.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
