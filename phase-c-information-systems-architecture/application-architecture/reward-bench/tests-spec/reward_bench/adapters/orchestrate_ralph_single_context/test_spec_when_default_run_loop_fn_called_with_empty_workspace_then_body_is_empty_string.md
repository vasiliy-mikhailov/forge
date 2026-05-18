# `test_when_default_run_loop_fn_called_with_empty_workspace_then_body_is_empty_string`

Pins the missing-file branch of the §7 ralph production binding per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
The default `_body_reader` must NOT raise when
`workspace/submission.best.py` is absent — it returns an empty
string. This matters because the ralph loop can finish without
ever writing a best-snapshot (instant solver_error, walltime
exceeded on every seed, etc.) and the bench-side
`Submission.body=''` is the honest signal.

- **Arrange**: empty tmp workspace dir (no `submission.best.py`).
  Build `fn = default_run_loop_fn(_run_loop=fake_inner,
  _time_fn=lambda: 0.0)` (real default body reader, faked time +
  inner loop).
- **Act**: `fn(workspace=str(tmp))`.
- **Assert**: `result['body'] == ''`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_default_run_loop_fn_called_with_empty_workspace_then_body_is_empty_string`.

## Model client injection point

- **Seam**: `_run_loop` and `_time_fn` faked; `_body_reader` runs at
  default (real Path check + read).

## Runtime scope

> **Runtime scope**: unit only — production factory's missing-file branch against an empty tmp_path.
