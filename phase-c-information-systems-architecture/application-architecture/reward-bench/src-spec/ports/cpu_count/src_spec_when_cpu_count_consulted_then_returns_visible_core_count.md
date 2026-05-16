# `src_spec_when_cpu_count_consulted_then_returns_visible_core_count`

[`CpuCountPort`](../../../src/ports/cpu_count.py) — port returning the
number of CPU cores available to the current process. Established by
cycle 105 / [ADR 0006 Layer 2 amendment](../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md).

## Why

The clean-arch test forbids `import os` in `src/<m>/use_cases/`. Use
cases that need to know the host's CPU count (e.g. for sizing a
`docker run --cpus=N` cap) reach for this port instead. Tests inject
[`FixedCpuCount(n)`](../../../src/adapters/multiprocessing_cpu_count.py).

## Contract

`cpu_count() -> int` — returns the cgroup-visible logical CPU count.
On a host with no cgroup limit, this is the kernel's online-CPU count.
Inside a Docker container with `--cpus=N`, returns `N`.

Production binding:
[`MultiprocessingCpuCount`](../../../src/adapters/multiprocessing_cpu_count.py)
wrapping `multiprocessing.cpu_count()`.
