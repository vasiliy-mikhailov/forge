# `src_spec_supervisor_port`

`src.reward_bench.use_cases.supervisor_port.SupervisorPort` is the
application-layer abstraction over [ADR 0005](
../../../../docs/adr/0005-plateau-detection-supervisor-via-llm-self-judgment.md)'s
plateau-detection step. Adapters under `src/reward_bench/adapters/`
implement this interface; the canonical adapter is `LlmSupervisor`
(cycle 32) which delegates to the bench LLM under test per ADR 0001.

Public method:

    def judge(self, sweep: Tuple[Sample, ...]) -> SupervisorDecision:
        '''Inspect recent dev_runner samples and return a frozen
        SupervisorDecision (cycle 30).'''

A `Sample` is a frozen tuple `(iter_no, mean_score, max_tile,
walltime_sec)` — the four signals ADR 0005 calls out as inputs to
plateau judgment. The port receives a TUPLE (not a list) to enforce
immutability across the boundary.

This file also ships `NullSupervisor` — the trivial implementation
that always returns `SupervisorDecision(plateau=False,
stop_recommended=False, reasoning='null supervisor: never stop')`.
This is:

1. The default when no supervisor is configured (so cycle 33 can
   wire agent_loop to a supervisor without changing behavior).
2. The test anchor for the protocol (lets us pin `isinstance(x,
   SupervisorPort) is True` for runtime-checkable correctness).

Allowed imports: `dataclasses`, `typing.Protocol`,
`typing.runtime_checkable`, `typing.Tuple`,
`src.reward_bench.entities.supervisor_decision`.
