# `test_when_run_loop_observes_new_best_dev_mean_then_snapshots_submission_for_restore_at_finish`

Pins the **best-snapshot + restore** seam in `run_loop`. The
loop tracks the best dev_runner MEAN seen so far, snapshots
`submission.py` to
`submission.best.py` when a new best is observed, and at `finish`
restores `submission.best.py` over `submission.py` so the scoring
phase sees the high-water mark — not whatever the model wrote last.
Our active `agent_loop.py` does not do this; mid-trial regressions in
the model's iteration cost real score on canonical eval.

The seam fires on dev_runner summary lines already parsed in cycle 34
(`MEAN=<float>  MEDIAN=...  max-tile-best=<int>`).

- **Arrange**: stub `_call_model` to emit a scripted sequence of
  tool calls across 5 turns:
    1. `execute_submission` body=`# A` (good iter)
    2. `bash dev_runner` — execute_tool stub returns dev_runner output
       with `MEAN=1000.0  MEDIAN=...  max-tile-best=256  (0.0s total)`
    3. `execute_submission` body=`# B` (regression)
    4. `bash dev_runner` — stub returns `MEAN=500.0 ... max-tile-best=128 (0.0s)`
    5. `finish`
  monkeypatch `execute_tool` to return a stub `<observation>` JSON when name=='execute_submission' (the active path snapshots the body to `submission.best.py` on a new best dev_mean)
  so we can inspect submission.py at the end, (b) return the scripted
  dev_runner observations on bash, (c) return ok on finish.
- **Act**: `run_loop(..., max_iters=10)`.
- **Assert**:
  - `result['finished'] is True`
  - `workspace/submission.py` text is `# A` (the best-MEAN snapshot)
    NOT `# B` (the latest write).
  - `workspace/submission.best.py` exists with text `# A`.
  - The new best-snapshot marker `[harness] new best dev MEAN=1000.0`
    appears in stdout (cycle 38 heartbeat extension).

Sibling test pins the no-regression path: a single dev_runner with
new best, no later regression. submission.py at end == latest written
== best snapshot.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
