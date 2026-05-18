# `test_when_run_loop_with_metrics_given_body_reader_then_result_body_equals_reader_output`

Pins the body-lifting seam of the §7 ralph production wrapper per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

The real `run_loop` does not return the final submission body — it
mutates `workspace/submission.best.py` on disk. The wrapper closes
this gap via an injected `_body_reader` callable that converts the
workspace into a body string.

- **Arrange**: a fake `_body_reader(workspace)` returning
  `'class Solver: pass\n'`; a fake `_time_fn` returning `0.0`; a
  minimal `fake_run_loop` returning a dict without `'body'`.
- **Act**: `run_loop_with_metrics(_run_loop=..., _time_fn=...,
  _body_reader=fake_body_reader, workspace='/tmp/ws')`.
- **Assert**: `result['body'] == 'class Solver: pass\n'`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_run_loop_with_metrics_given_body_reader_then_result_body_equals_reader_output`.

## Model client injection point

- **Seam**: `_body_reader` keyword parameter on the wrapper.
- **Mode**: **fake** (default) — caller-provided fake.
- **Override**: production binding supplies a reader that does
  `Path(workspace) / 'submission.best.py'.read_text()`.

## Runtime scope

> **Runtime scope**: unit only — wrapper DI seam with injected fakes; no disk IO.
