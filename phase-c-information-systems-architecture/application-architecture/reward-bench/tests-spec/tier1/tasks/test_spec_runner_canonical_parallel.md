# `test_spec_runner_canonical_parallel`

Pins the **parallel-per-seed worker** in
[`tasks/2048/runner_canonical.py`](../../../../tasks/2048/runner_canonical.py)
introduced in cycle 105 sub-A per the
[ADR 0006 Layer 2 amendment](../../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md).

## Why

The container entrypoint pre-cycle-105 played seeds sequentially. With
the cycle-105 Docker contract giving the container `N` cores via
`--cpus=N`, the runner must parallelise across them — otherwise the
host's --cpus cap caps an idle container.

The runner now uses `multiprocessing.Pool(processes=cpu_count())`
where `cpu_count()` reads the cgroup quota that Docker imposed.

## Contract (worker-level)

`_play_one_collect_events((submission_path, seed, target, max_moves, stagnation_sec, hard_deadline_wall))`
runs in a worker process. Returns `(game_result_dict, list_of_event_dicts)`.

- Re-imports the submission for clean state.
- Catches Solver `__init__` exceptions → `final_state='solver_error'`
  with `error` field describing the exception.
- Catches `move()` exceptions → `final_state='solver_error'`,
  event recorded with the exception detail.
- Rejects non-WASD return values from `move()` →
  `final_state='invalid_action'`.
- Stagnation detector: `final_state='stagnated'` after
  `stagnation_sec` seconds without `score / max_tile` progress.
- Outer hard deadline: if `hard_deadline_wall` (absolute wall-clock
  seconds) is passed mid-game → `final_state='walltime_exceeded'`.

## Model client injection point

- **Seam**: `_play_one_collect_events` is a top-level function (must be
  pickle-able for multiprocessing). Tests call it directly with a
  hand-crafted submission file.
- **Default**: `fake` — tests construct synthetic Solver bodies inline.
- **Live override**: in production this runs inside the container as
  part of `multiprocessing.Pool.imap_unordered(...)`.

## Tests

### `test_when_solver_valid_then_game_result_returned`

- **Arrange**: tmp submission.py with a transitions-import + a Solver
  returning 'W'. Set up an `env_2048` shim importable from the test
  (sys.path injection).
- **Act**: `_play_one_collect_events((sub_path, 1, 2048, 100, 60, None))`.
- **Assert**: returned tuple's first element has `seed=1, score>=0,
  max_tile>=2, moves>0, final_state in {won, lost, max_moves}`.

### `test_when_solver_init_raises_then_solver_error_final_state`

- **Arrange**: submission whose `__init__` raises `RuntimeError`.
- **Assert**: `final_state == 'solver_error'`, `error` field mentions
  RuntimeError.

### `test_when_solver_move_raises_then_solver_error_with_event`

- **Arrange**: submission whose `move()` raises after the first call.
- **Assert**: `final_state == 'solver_error'`, events list contains a
  `solver_raised` entry.

### `test_when_solver_returns_invalid_action_then_invalid_action_final_state`

- **Arrange**: submission whose `move()` returns `'Q'` (not WASD).
- **Assert**: `final_state == 'invalid_action'`, events list contains
  `invalid_action`.

### `test_when_hard_deadline_passed_then_walltime_exceeded`

- **Arrange**: submission whose `move()` sleeps 10s. Call worker with
  `hard_deadline_wall = time.time()` (already past).
- **Assert**: `final_state == 'walltime_exceeded'`.

Test code: [`tests/tier1/tasks/test_runner_canonical.py`](../../../../tests/tier1/tasks/test_runner_canonical.py).

## Out of scope for unit tests (covered by integration / Docker tests)

- Full `multiprocessing.Pool` orchestration (covered by a smoke test
  that runs the runner directly via `python tasks/2048/runner_canonical.py`).
- Real Docker container spawn (cycle 106 candidate: live test against
  the built image).
