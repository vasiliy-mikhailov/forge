# `test_spec_when_null_supervisor_judges_then_returns_never_stop_decision`
Pins the trivial-supervisor contract: every call to
[`NullSupervisor`](../../../../src/reward_bench/adapters/null_supervisor.py).`judge(sweep)`
returns a `SupervisorDecision(plateau=False, stop_recommended=False)`
regardless of input. Also pins `isinstance(NullSupervisor(),
SupervisorPort) is True` — the test anchor for runtime-checkable
[Protocol conformance](../../../../src/ports/supervisor.py).
Relocated from
`tests-spec/reward_bench/use_cases/supervisor_port/` to mirror the
adapter's new location under `src/reward_bench/adapters/`.
## Contract
- **Arrange**: build a 3-row plateau-flat sweep
 `((1, 3000.0, 256, 1.0), (2, 3000.0, 256, 1.0), (3, 3000.0, 256, 1.0))`
 and instantiate `NullSupervisor()`.
- **Act**: call `supervisor.judge(sweep)`.
- **Assert**:
 - return is a `SupervisorDecision`
 - `decision.plateau is False`
 - `decision.stop_recommended is False`
 - `decision.reasoning` is a non-empty `str`
 - `isinstance(supervisor, SupervisorPort) is True`
Test code: [`../../../../tests/reward_bench/adapters/test_null_supervisor.py`](../../../../tests/reward_bench/adapters/test_null_supervisor.py)::`test_when_null_supervisor_judges_then_returns_never_stop_decision`.
## Model client injection point
- **Seam**: not applicable — NullSupervisor takes no model client.
- **Mode**: pure-Python; runs under the default autouse fake binding.
## Runtime scope
> **Runtime scope**: unit only — trivial Port-conformant implementation; no runtime boundary to live-test.
