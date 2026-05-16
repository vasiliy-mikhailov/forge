# `test_when_execute_submission_solver_init_raises_then_protocol_violation_names_exception`

Pins the **Solver-instantiation probe** added in cycle 100.

## Why

Cycle 99a live run found qwen3.6-27b-awq submits a Solver whose
`__init__` raises (e.g. uses `transitions=[(...), ...]` tuple form
that the `transitions` library rejects with `TypeError: ... argument
after ** must be a mapping, not tuple`). Pre-cycle-100 the bench
observation only surfaced
`per_seed[i].err = 'solver_error (Solver raised in __init__ or move)'`
without naming the actual exception. The model couldn't self-correct;
it iterated 30 times producing the same broken submission.

Cycle 100 adds a one-shot probe in `_execute_submission` after
protocol validation: it instantiates `Solver()` once and, if that
raises, surfaces `Solver instantiation failed: <ExcType>: <msg>` as
a protocol_violation so the model sees the actual error and can fix
the next iter.

## Contract

After `validate_submission_protocol` passes and before
`score_submission` runs, `_execute_submission` performs a one-shot
`module.Solver()` call. Three outcomes:

| Outcome | Result |
|---|---|
| `Solver()` returns | continue to `score_submission` (unchanged) |
| `Solver()` raises | observation has `protocol_violations = ['Solver instantiation failed: <ExcType>: <msg>']`; `per_seed = []`; `mean = 0.0` |

A `move()` exception is NOT caught by the probe — it still produces
per_seed `solver_error` sentinels via the canonical scorer (existing
behaviour, unchanged).

## Model client injection point

- **Seam**: `_execute_submission(body, workspace, tasks_dir)` is called
  by the autouse `_bind_model_client` fixture's `fake_execute_tool`,
  which returns a synthetic happy-path observation. The probe is NOT
  exercised in fake mode (no real Solver instantiation). To exercise
  the probe in fake mode the test calls `_execute_submission` directly
  with a hand-crafted body, bypassing the autouse glue.
- **Default**: `fake` — body is constructed in-test; no model client
  consulted. Live mode behaves identically since the body is
  in-test.

## Tests

### Probe surfaces TypeError when transitions misuse

- **Arrange**: a Solver body whose `__init__` calls `Machine` with
  `transitions=[('a', 's1', 's2')]` — tuple form that the library
  rejects.
- **Act**: `_execute_submission(body, workspace, tasks_dir)`.
- **Assert**:
  - Observation parses to JSON with non-empty `protocol_violations`.
  - One violation matches `Solver instantiation failed:` AND mentions
    the underlying exception type name (`TypeError`).
  - `per_seed == []` (canonical scorer didn't run).

### Probe is no-op for a valid Solver

- **Arrange**: a Solver body whose `__init__` succeeds.
- **Act**: `_execute_submission(body, ...)`.
- **Assert**: observation has empty `protocol_violations` AND non-empty
  `per_seed` (canonical scorer ran).

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

