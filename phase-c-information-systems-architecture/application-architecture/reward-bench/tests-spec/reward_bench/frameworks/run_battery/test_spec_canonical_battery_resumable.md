# `test_spec_canonical_battery_resumable`
Pins the **`run_canonical_battery`** function added.
## Why
Per [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
the canonical campaign is `max_iters=500, n_trials=10, T=0.7` across
every model in `MODEL_REGISTRY` whose registry entry has
`bench_skip != true`. A single sweep takes 24-48 hours on the lab
hardware. The operator must be able to interrupt overnight (Ctrl-C)
and resume the next evening without losing completed work.
## Contract
`run_canonical_battery(n_trials=10, max_iters=500, temperature=0.7, seeds=None, registry_path=None, filter_regex=None, experiments_root=None, runner=None)`
- Reads the registry, filters `bench_skip != true`, optionally narrows
 with `filter_regex`.
- For each (model, trial) pair:
 - Builds the artifact path
 `experiments/YYYY-MM-DD-bench-{model_id}-trial{N}.json`
 where YYYY-MM-DD is the date at the **start** of the sweep (so a
 cross-midnight resume still hits the same filename).
 - If the artifact exists, the (model, trial) is **skipped**; the
 runner is NOT invoked.
 - Otherwise, the runner is invoked. On success, the runner's return
 dict is serialised as the artifact.
 - If the runner raises `KeyboardInterrupt`, no artifact is written
 for that (model, trial); the exception propagates so the operator
 sees the halt. Re-running picks up at the interrupted trial.
`runner` defaults to a closure that calls
`reward_bench.frameworks.main.main(model_id, seeds, config)` with the
 canonical `BenchConfig`. Tests inject a recorder.
## Model client injection point
- **Seam**: the `runner` callable. Default binding constructs
 `VllmOpenAIClient` (via `main()` -> `ensure_serving_model` -> live
 vLLM). Tests inject an in-memory recorder.
- **Default**: `live` — canonical bench is by definition a live
 campaign.
- **Live override**: not applicable — pass a fake `runner` to make
 the test fast.
## Tests
[`tests/reward_bench/frameworks/test_canonical_battery.py`](../../../../tests/reward_bench/frameworks/test_canonical_battery.py)
— 5 contract tests:
1. No artifacts present → runner invoked for every (model, trial)
 in order.
2. Some artifacts present → those (model, trial) skipped.
3. Runner raises `KeyboardInterrupt` → no artifact written; exception
 propagates.
4. Runner completes a trial → artifact serialised to disk.
5. `filter_regex` → only matching model ids run.
## Operator runbook
```
# Start (or resume) the sweep:
cd reward-bench && python3 -c "from src.reward_bench.frameworks.run_battery \
 import run_canonical_battery; run_canonical_battery()"
# Pause: Ctrl-C in the terminal. The current trial is abandoned;
# all previously-completed trials are saved.
# Resume: re-run the same command. The driver scans existing
# artifacts and starts at the first (model, trial) without one.
# Inspect progress:
ls experiments/$(date +%Y-%m-%d)-bench-*.json | wc -l
# /22 models × 10 trials = 220 total artifacts at full completion.
```
## Runtime scope
> **Runtime scope**: unit only — canonical-battery driver; production-runtime IS this driver invoked end-to-end during operational sweeps.

Test code: [`../../../../tests/reward_bench/frameworks/test_canonical_battery.py`](../../../../tests/reward_bench/frameworks/test_canonical_battery.py)::`test_when_canonical_battery_runs_with_no_artifacts_then_runner_invoked_per_trial`.
