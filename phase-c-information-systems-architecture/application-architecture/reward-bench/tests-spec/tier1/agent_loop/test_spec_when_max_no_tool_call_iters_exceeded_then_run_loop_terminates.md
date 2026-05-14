# `test_when_max_no_tool_call_iters_exceeded_then_run_loop_terminates`

Pins the cycle-38 stall-detection knob `max_no_tool_call_iters`. When
K consecutive `run_loop` iterations produce no parseable tool call
(model emitting prose only), the loop breaks early with `finished=False`
and the iteration counter at K.

Without this knob the cycle-22 hang shape could re-emerge — a model
generating long prose with no `bash`/`view`/`finish` tool block runs
for the full `max_iters` budget producing nothing useful.

- **Arrange**: stub `_call_model` to return a plain prose string (no
  tool block) on every call. `max_no_tool_call_iters=3`.
- **Act**: `run_loop(..., max_iters=100,
  max_no_tool_call_iters=3)`.
- **Assert**:
  - `result['iterations'] == 3` (stops at K, not 100).
  - `result['finished'] is False`.
  - `_call_model` was invoked exactly 3 times.

Default `max_no_tool_call_iters=0` keeps cycle-12 behavior (never
abort on no-tool-call streaks).

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
