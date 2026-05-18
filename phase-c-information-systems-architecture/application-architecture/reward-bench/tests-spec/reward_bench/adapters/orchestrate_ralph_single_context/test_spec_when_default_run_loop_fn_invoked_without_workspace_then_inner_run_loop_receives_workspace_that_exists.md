# `test_when_default_run_loop_fn_invoked_without_workspace_then_inner_run_loop_receives_workspace_that_exists`

Pins the §7 wrapper's encapsulation of workspace per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
The architecture wants subagent/orchestrator → bench communication
to be structured data, not files. Workspaces still exist (Docker
bind-mount needs them), but the **bench-side API** does not. The
production wrapper owns the tempdir lifecycle; the adapter and
bench never see a workspace kwarg.

- **Arrange**: `fake_inner_run_loop` that captures its kwargs and
  whether `Path(workspace).exists()` at call time;
  `fn = default_run_loop_fn(_run_loop=fake, _time_fn=lambda: 0.0)`.
- **Act**: `fn()` (no workspace kwarg).
- **Assert**: `captured['workspace_exists_during_call'] is True`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_default_run_loop_fn_invoked_without_workspace_then_inner_run_loop_receives_workspace_that_exists`.

## Model client injection point

- **Seam**: `_run_loop` keyword (recording fake); workspace
  managed by the wrapper.
- **Mode**: **fake** for the inner loop; **real** tempfile for the
  workspace.

## Runtime scope

> **Runtime scope**: unit only — wrapper-owned tempdir lifecycle.
