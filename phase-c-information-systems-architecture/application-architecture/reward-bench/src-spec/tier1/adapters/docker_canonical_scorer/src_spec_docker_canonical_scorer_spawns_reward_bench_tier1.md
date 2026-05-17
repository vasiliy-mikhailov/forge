# `src_spec_docker_canonical_scorer_spawns_reward_bench_tier1`

[`DockerCanonicalScorer`](../../../../src/tier1/adapters/docker_canonical_scorer.py) —
cycle 105 / [ADR 0006 Layer 2](../../../../SOLUTION-ARCHITECTURE.md)
implementation. Spawns the `reward-bench-tier1:0.4` container per attempt.

## Contract

Constructed with:
- `image` (default `reward-bench-tier1:0.4`)
- `cpus` (default `cpu_count_port.cpu_count() / 2` — ADR 0006 host-side cap)
- `cpu_count_port` (default `MultiprocessingCpuCount()`)
- `memory` (default `"2g"`), `pids_limit` (default 256)
- `env_path` (path to `tasks/2048/env.py`)
- `stagnation_sec` (default 60)
- `docker_bin` (default `"docker"`)

`score(submission_path, seeds, *, hard_wall_sec=0.0, reports_root=None) -> AttemptResult`:

1. Spawns `docker run --rm --network=none --memory=2g --pids-limit=256
   --cpus=N -v submission.py:/workspace/submission.py:ro
   -v env_2048.py:/env/env_2048.py:ro -v reports:/reports
   -e REWARD_BENCH_NUM_GAMES=N -e REWARD_BENCH_SEED_BASE=S
   -e REWARD_BENCH_HARD_WALL_SEC=H -e REWARD_BENCH_STAGNATION_SEC=K
   reward-bench-tier1:TAG`.
2. Outer subprocess timeout = `hard_wall_sec + 30s grace`. On
   `TimeoutExpired`, all seeds get `walltime_exceeded` sentinels.
3. Reads `/reports/result.json`. If missing or unparseable, all seeds
   get sentinels (walltime_exceeded / solver_error).
4. Maps the JSON game list to `GameResult` entities preserving input
   seed order (missing seeds get walltime_exceeded sentinels).
5. Returns an aggregated `AttemptResult`.

The container's own `runner_canonical.py` parallelises across the
cgroup-allocated CPUs via `multiprocessing.Pool(cpu_count())`, so the
host's `--cpus=N` cap directly bounds inside-container parallelism
(see runner spec at [`tasks/2048/runner_canonical.py`](../../../../tasks/2048/runner_canonical.py)).
