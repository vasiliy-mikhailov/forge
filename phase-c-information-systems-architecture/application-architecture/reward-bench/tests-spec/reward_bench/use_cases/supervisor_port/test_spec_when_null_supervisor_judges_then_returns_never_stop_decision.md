# `test_when_null_supervisor_judges_then_returns_never_stop_decision`

Pins the [`NullSupervisor`](../../../../src-spec/reward_bench/use_cases/supervisor_port/src_spec_supervisor_port.md)
contract: it always returns a SupervisorDecision with `plateau=False`
and `stop_recommended=False`, regardless of the sweep contents. This
is the test anchor for the [SupervisorPort](
../../../../src-spec/reward_bench/use_cases/supervisor_port/src_spec_supervisor_port.md)
protocol and the default for cycle 33's agent_loop hook.

- **Arrange**: import `NullSupervisor`, `SupervisorPort`,
  `SupervisorDecision`. Build a sweep tuple with three samples
  showing clear plateau ([(1, 3000.0, 256, 1.0), (2, 3000.0, 256,
  1.0), (3, 3000.0, 256, 1.0)]).
- **Act**: `decision = NullSupervisor().judge(sweep)`.
- **Assert**:
  - `decision.plateau is False` (null supervisor doesn't see plateaus).
  - `decision.stop_recommended is False`.
  - `decision.reasoning` is a non-empty `str`.
  - `isinstance(NullSupervisor(), SupervisorPort)` — runtime-checkable
    protocol acceptance.

Test code: [`tests/reward_bench/use_cases/test_supervisor_port.py`](../../../../tests/reward_bench/use_cases/test_supervisor_port.py).
