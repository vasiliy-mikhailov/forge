# `src_spec_multiprocessing_cpu_count_reads_cgroup_quota`
[`MultiprocessingCpuCount`](../../../src/adapters/multiprocessing_cpu_count.py)
is the production [`CpuCountPort`](../../../src/ports/cpu_count.py)
binding. See [SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md) Layer 2.
## Contract
`MultiprocessingCpuCount().cpu_count()` returns
`multiprocessing.cpu_count()`. Defensively returns 1 when the platform
raises `NotImplementedError`. No `os` import (keeps the use-cases
layer's transitive surface clean).
`FixedCpuCount(n)` is a test fixture: `cpu_count() -> n`. Lets tests
assert `--cpus=N/2` math without depending on the host's actual core
count.
