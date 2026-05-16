# `src_spec_when_cpu_count_consulted_then_returns_visible_core_count`

[`CpuCountPort`](../../../src/ports/cpu_count.py) — the
runtime-boundary contract for "how many CPU cores does this process
get to use". Established by
[ADR 0006](../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
Layer 2.

Use-case modules (anything under `src/.../use_cases/`) cannot import
`os` per the clean-arch test in
[`tests/architecture/`](../../../tests/architecture/). Anywhere a
use-case needs `os.cpu_count()` or `len(os.sched_getaffinity(0))`, it
must take a `CpuCountPort` instead.

## Contract

```python
class CpuCountPort(Protocol):
    def cpu_count(self) -> int: ...
```

Semantics:

- Returns the **effective** core count for the current process —
  not the host's hardware total. Inside a `docker run --cpus=N`
  container the effective count is `N` (rounded per cgroup quota),
  not the host's 24.
- Always returns `>= 1`. Adapters that detect a 0/none result clamp
  to 1.
- Pure, idempotent, fast. May cache; MUST NOT depend on test
  ordering.

### Liveness / failure semantics

- **MUST NOT raise.** A failure to read cgroup files / `os.cpu_count`
  / `nproc` returns 1 instead of raising. The bench has no recovery
  path for "we don't know how many cores we have".

## Adapter manifest

- [`MultiprocessingCpuCount`](../../../src/adapters/multiprocessing_cpu_count.py)
  — production adapter; reads `multiprocessing.cpu_count()` which
  respects cgroup quota inside Docker. Its src_spec covers the cgroup
  details.
- Fakes: tests construct ad-hoc `FixedCpuCount(n)` instances inline
  (no shared fake module since the surface is one int).
