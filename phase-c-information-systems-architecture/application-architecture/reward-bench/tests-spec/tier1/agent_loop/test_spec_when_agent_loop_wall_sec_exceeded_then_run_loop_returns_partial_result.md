# `test_when_agent_loop_wall_sec_exceeded_then_run_loop_returns_partial_result`

Pins the cycle-38 stall-detection knob `agent_loop_wall_sec`. When
the total wall time of `run_loop` exceeds this budget (BETWEEN
iterations — checked after each iter completes), the loop terminates
with `finished=False`.

Mirrors `score_submission.hard_wall_sec` (ADR 0006 layer 1) but for
the AGENT LOOP rather than the SCORING phase. Together with cycle 27's
per-game preemption, this gives end-to-end wall-time bounds for a
trial.

- **Arrange**: stub `_call_model` to return a valid `view` tool call
  but also `time.sleep(0.3)` per call to consume wall time.
  `agent_loop_wall_sec=0.5`, `max_iters=100`.
- **Act**: `run_loop(..., max_iters=100,
  agent_loop_wall_sec=0.5)`.
- **Assert**:
  - `result['iterations'] >= 1` (made some progress).
  - `result['iterations'] < 100` (did NOT run the full budget).
  - `result['finished'] is False`.

Default `agent_loop_wall_sec=0.0` keeps cycle-12 behavior (unbounded).

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
