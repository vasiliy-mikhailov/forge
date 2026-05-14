# `test_when_finish_called_below_finish_floor_then_rejected_and_loop_continues`

Pins the **finish-floor** seam in `run_loop`. Per [hypothesis #2](
../../../../docs/hypotheses_agent_loop_regression.md), the [legacy
loop](../../../../src/tier1/legacy_agent_loop.py) rejects `finish`
when `best_dev_mean < finish_floor` (default 7211 = the reference_fsm
baseline). When rejected, the tool observation is a clear error
message and the loop CONTINUES — the model is forced to:

1. Actually call `bash python3 /tasks/2048/dev_runner.py ...` before
   claiming done.
2. Iterate until its submission scores above the floor.

Cycle 49 discovered the active loop without this guardrail lets the
model write a Solver-less Gym-style submission and call finish on
turn 1, which sentinels the trial. Cycle-48 best-snapshot can never
fire because the model never ran dev_runner.

- **Arrange**: stub `_call_model` to emit a scripted sequence:
    1. `finish` (no prior dev_runner — best_dev_mean unknown)
    2. `bash dev_runner` returning `MEAN=100`
    3. `finish` (best_dev_mean=100 < floor=200)
    4. `bash dev_runner` returning `MEAN=500`
    5. `finish` (best_dev_mean=500 > floor=200) — accepted.
  monkeypatch `execute_tool` to return dev_runner outputs on bash and
  ok on write/finish.
- **Act**: `run_loop(..., max_iters=10, finish_floor=200.0)`.
- **Assert**:
  - `result['iterations'] == 5` (loop ran past 2 rejected finishes).
  - `result['finished'] is True` (the 3rd finish ABOVE floor was accepted).
  - At least one observation message contains `finish rejected` text.

Sibling test pins the default `finish_floor=0` keeps cycle-12 behaviour
(any finish accepted). No regression for existing tests.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
