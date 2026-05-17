# `test_spec_agent_loop_pure_helpers`

Pins the five pure helpers extracted from `run_loop`'s in-loop state
machine:

- `reject_finish_for_floor(finish_floor, best_dev_mean) -> str | None`
- `update_best_snapshot(current_best, new_mean) -> (new_best, snapshot_fires)`
- `sweep_sample(iter_n, parsed) -> (iter_n, mean, max_tile, walltime)`
- `should_smoke_stop(smoke_early_stop, best_dev_mean) -> bool`
- `promote_body_text(body) -> str`

The Haskell stance: the imperative `run_loop` becomes thin
orchestration over pure decisions. Each helper is a pure transition
— no I/O, no time, no globals — and gets its own unit tests.

## Tests

Pinned in `tests/tier1/test_agent_loop_helpers.py`. 16 tests in 5
groups, one per helper, covering:

- `reject_finish_for_floor`: floor=0, no dev yet, best below, best
  above, best equal (boundary).
- `update_best_snapshot`: None current, strictly above, strictly
  below, equal.
- `sweep_sample`: None parsed, valid tuple unpacked.
- `should_smoke_stop`: smoke off, smoke on with no dev, smoke on
  with zero dev, smoke on with positive dev.
- `promote_body_text`: missing trailing newline, already-present
  trailing newline.

## Model client injection point

- **Seam**: none — all helpers are pure functions over primitives.
- **Mode**: n/a.

Test code: [`../../../tests/tier1/test_agent_loop_helpers.py`](../../../tests/tier1/test_agent_loop_helpers.py)::`test_when_finish_floor_zero_then_no_rejection`.

## Runtime scope

> **Runtime scope**: unit only — pure helpers have no runtime
> dependency.
