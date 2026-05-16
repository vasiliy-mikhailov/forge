# `src_spec_when_canonical_scorer_score_called_then_returns_attempt_result`

[`CanonicalScorerPort`](../../../src/ports/canonical_scorer.py) — the
runtime-boundary contract for "play a submission against seeds and
return the aggregated result". Established by
[ADR 0018](../../../docs/adr/0018-runtime-boundary-dependencies-port-fake-autouse.md).

The Docker production binding's `--cpus` + image-tag knobs live in
[ADR 0006](../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md);
they are not part of the Port contract.

## Contract

```python
class CanonicalScorerPort(Protocol):
    def score(
        self,
        submission_path: str | Path,
        seeds: Iterable[int],
        *,
        hard_wall_sec: float = 0.0,
        reports_root: str | Path | None = None,
    ) -> AttemptResult: ...
```

Semantics:

- `submission_path` is the path to a submission `.py` file (may be
  hostile / syntactically broken / runtime-unsafe — the adapter
  isolates execution).
- `seeds` is the deterministic seed set for the 2048 trial battery;
  the adapter plays one game per seed.
- `hard_wall_sec` is the aggregate cap across all seeds (per ADR 0006
  Layer 2 + [ADR 0015](../../../docs/adr/0015-canonical-bench-hard-wall-sec-300.md)).
  `0.0` means no cap. Exceeded → per-seed `walltime_exceeded` sentinels
  fill out the result; the port does NOT raise.
- `reports_root` (optional) is where per-game event logs land. `None`
  means the adapter chooses a default temp area.

Return: a single `AttemptResult` aggregating per-seed games via
`AttemptResult.from_games(...)`. Always returns an `AttemptResult`
(never `None`).

### Liveness / failure semantics

- **MUST NOT raise on hostile submissions.** Bad submission code
  (syntax errors, invalid actions, infinite loops, deliberate
  `sys.exit`) surfaces as per-seed sentinel `final_state` in the
  returned `AttemptResult` (`solver_error`, `invalid_action`,
  `walltime_exceeded`, `stagnated`, `protocol_violation`).
- **MUST honour `hard_wall_sec`.** Any seed still running past the
  aggregate deadline is recorded as `walltime_exceeded`. The adapter
  is free to kill processes / containers to enforce this.
- **MAY raise on infrastructure failure** (Docker unavailable, image
  missing, disk full). Those are bench bugs, not submission bugs,
  and shouldn't be silently turned into `solver_error`.

## Adapter manifest

- [`FakeCanonicalScorer`](../../../src/adapters/fakes/fake_canonical_scorer.py)
  — scripted `AttemptResult` queue + `.calls` recording surface (its
  own src_spec covers the recording surface).
- [`InProcessCanonicalScorer`](../../../src/adapters/in_process_canonical_scorer.py)
  — wraps `score_submission` for fast hermetic seam tests.
- [`DockerCanonicalScorer`](../../../src/tier1/adapters/docker_canonical_scorer.py)
  — Layer 2 production binding. See ADR 0006 for image/runner
  contract.

The autouse `_bind_canonical_scorer` fixture in
[`tests/conftest.py`](../../../tests/conftest.py) binds
`FakeCanonicalScorer` as the default test binding; production callers
in `reward_bench/frameworks/main.py` use the
`_default_canonical_scorer()` factory that resolves to
`DockerCanonicalScorer`.

Enforcement:
[`test_when_runtime_boundary_port_inspected_then_protocol_exists`](../../../tests/architecture/test_runtime_boundary_ports.py)
asserts the Protocol exists; DI tests in
[`test_canonical_scorer_di.py`](../../../tests/adapters/test_canonical_scorer_di.py)
assert every named adapter implements it.
