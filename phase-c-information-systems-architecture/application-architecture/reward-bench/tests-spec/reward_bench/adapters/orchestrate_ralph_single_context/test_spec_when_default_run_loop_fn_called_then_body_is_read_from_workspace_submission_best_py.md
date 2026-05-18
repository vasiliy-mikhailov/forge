# `test_when_default_run_loop_fn_called_then_body_is_read_from_workspace_submission_best_py`

Pins the §7 ralph production binding per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
The `default_run_loop_fn` factory composes `run_loop_with_metrics`
with production defaults — the real `_body_reader` does
`Path(workspace) / 'submission.best.py'.read_text()`, lifting the
ralph loop's on-disk artifact into the result dict's `'body'` key.

- **Arrange**: tmp workspace dir; write `'class Solver: pass\n'`
  into `<tmp>/submission.best.py`; build `fn = default_run_loop_fn(
  _run_loop=fake_inner, _time_fn=lambda: 0.0)` (real default body
  reader, faked time + inner loop).
- **Act**: `fn(workspace=str(tmp))`.
- **Assert**: `result['body'] == 'class Solver: pass\n'`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_default_run_loop_fn_called_then_body_is_read_from_workspace_submission_best_py`.

## Model client injection point

- **Seam**: `_run_loop` and `_time_fn` faked; `_body_reader` runs at
  default (real Path read).
- **Mode**: **fake** for the inner loop and clock; **real** disk for
  the body reader against `tmp_path`.

## Runtime scope

> **Runtime scope**: unit only — production factory with two seams faked, one (disk read) exercised against tmp_path.
