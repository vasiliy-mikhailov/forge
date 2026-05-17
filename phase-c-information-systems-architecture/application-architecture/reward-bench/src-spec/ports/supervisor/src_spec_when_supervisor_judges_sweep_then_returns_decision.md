# `src_spec_when_supervisor_judges_sweep_then_returns_decision`
[`SupervisorPort`](../../../src/ports/supervisor.py) — the
runtime-boundary contract for plateau-detection per
[SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md).
Relocated from `src/reward_bench/use_cases/supervisor_port.py`
to comply with [SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md)'s
`src/ports/<name>.py` convention.
## Types
```python
# (iter_no, mean_score, max_tile, walltime_sec) — the four signals
# calls out as plateau-detection inputs.
Sample = Tuple[int, float, int, float]
```
## Contract
```python
@runtime_checkable
class SupervisorPort(Protocol):
 def judge(self, sweep: Tuple[Sample,...]) -> SupervisorDecision:...
```
Semantics:
- `sweep` is an immutable tuple of recent `Sample`s ordered oldest
 first. Adapters MUST NOT mutate or store the sweep beyond the
 scope of one `judge` call.
- Return is a frozen `SupervisorDecision` carrying `plateau` (bool),
 `stop_recommended` (bool), and `reasoning` (str). The agent loop
 acts on `stop_recommended` only.
### Liveness / failure semantics
- **MUST NOT raise.** Any internal failure (LLM unreachable, parse
 error, malformed input) degrades to a conservative
 `SupervisorDecision(plateau=False, stop_recommended=False,
 reasoning=...)`. The agent loop never sees an exception from the
 supervisor; a flaky supervisor never causes accidental early stop.
- **Idempotent and side-effect-free.** The Port itself; adapters
 composed with `ModelClient` are subject to ModelClient's own
 side-effect surface (already a runtime-boundary Port).
## Adapter manifest
- [`LlmSupervisor`](../../../src/reward_bench/adapters/llm_supervisor.py)
 — production adapter; delegates plateau judgment to the bench LLM
 under test. Renders a sweep prompt, parses JSON from
 the reply.
- [`NullSupervisor`](../../../src/reward_bench/adapters/null_supervisor.py)
 — trivial adapter; always returns `plateau=False, stop_recommended=False`.
 Default when no LLM supervisor is configured. Doubles as the
 Fake-equivalent for tests (no shared `src/adapters/fakes/` entry
 needed — the "do nothing" behaviour is real production semantics,
 not a test-only mock).
Enforcement:
[`test_when_runtime_boundary_port_inspected_then_protocol_exists[SupervisorPort]`](../../../tests/architecture/test_runtime_boundary_ports.py)
asserts the Protocol exists.
