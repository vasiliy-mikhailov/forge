# `src_spec_run_battery_drives_sweep`
[`src/reward_bench/frameworks/run_battery.py`](../../../../src/reward_bench/frameworks/run_battery.py)
hosts the / sweep driver. Two public entry points:
## `run_battery(tier, task, filter_regex, registry_path, runner)`
Iterates models.yml × the `make reward-bench` invocation.
Skips entries with `bench_skip: true`; optional `filter_regex` narrows
by id.
## `run_canonical_battery(n_trials, max_iters, temperature, canonical_hard_wall_sec, seeds, registry_path, filter_regex, experiments_root, runner)`
+ 104. canonical campaign (max_iters=500 × n_trials=10
× temperature=0.7) × canonical hard_wall_sec=300 default.
Resume semantics:
- Each (model, trial) writes `experiments/YYYY-MM-DD-bench-{id}-trial{N}.json`
 on success.
- Re-running the function scans existing artifacts and skips already-done
 (model, trial) pairs.
- The date stamp is cached at first invocation (cross-midnight resume
 hits the same filename).
- On `KeyboardInterrupt`, the in-flight (model, trial) does NOT write
 an artifact; the exception propagates. Re-running picks up at the
 interrupted trial.
Default `runner` closure constructs `BenchConfig(max_iters,
n_trials=1, temperature, hard_wall_sec=canonical_hard_wall_sec)` and
calls `main(model_id, seeds, config)`. Tests inject a recorder.
