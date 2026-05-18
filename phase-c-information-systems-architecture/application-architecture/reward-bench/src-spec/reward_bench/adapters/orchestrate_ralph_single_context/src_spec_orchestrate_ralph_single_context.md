# `src_spec_orchestrate_ralph_single_context`

[`../../../../src/reward_bench/adapters/orchestrate_ralph_single_context.py`](../../../../src/reward_bench/adapters/orchestrate_ralph_single_context.py)
is the first `Orchestrator` adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7. It wraps the long-running single-context ralph loop from
`src.tier1.agent_loop.run_loop` and re-shapes its dict return into
the `Submission` value object the bench composes over.

Constructor:

```python
OrchestrateRalphSingleContext(run_loop_fn=None)
```

`run_loop_fn` defaults to `src.tier1.agent_loop.run_loop`; tests
inject a stub for hermetic seam coverage.

Method:

```python
def orchestrate(self, env: Env, cfg: BenchConfig) -> Iterable[Submission]: ...
```

Calls `self._run_loop` with kwargs derived from `env`/`cfg`:

    tasks_dir          ← env.tasks_dir
    model_client       ← env.model_client
    max_iters          ← cfg.max_iters
    temperature        ← cfg.temperature
    finish_floor       ← cfg.finish_floor
    supervisor_every_k ← cfg.supervisor_every_k
    smoke_early_stop   ← cfg.smoke_early_stop
    dev_hard_wall_sec  ← cfg.hard_wall_sec

Field mapping from the `run_loop_fn` return dict to `Submission`:

    body          ← result['body']
    score         ← result['best_dev_mean']
    walltime_sec  ← result['walltime_sec']

## Production wrapper

```python
def run_loop_with_metrics(
    *,
    _run_loop=None,
    _time_fn=None,
    _body_reader=None,
    **kwargs,
) -> dict: ...
```

Closes the contract gap between the real `run_loop` and the adapter.

- Measures monotonic time around the inner-loop call and injects
  `walltime_sec` into the returned dict.
- When `_body_reader` is supplied, sets `result['body'] =
  _body_reader(kwargs['workspace'])`.

`_run_loop` defaults to `src.tier1.agent_loop.run_loop`; `_time_fn`
defaults to `time.monotonic`. `**kwargs` are forwarded to the
inner loop.

## Production factory

```python
def default_run_loop_fn(
    *,
    _run_loop=None,
    _time_fn=None,
    _body_reader=None,
) -> Callable[..., dict]: ...
```

Returns a callable suitable for `OrchestrateRalphSingleContext(
run_loop_fn=...)` with production defaults already bound. The
default `_body_reader` reads
`Path(workspace) / 'submission.best.py'` and returns its text
(empty string if the file is missing).

The returned callable owns the workspace tempdir lifecycle: when
invoked without a `workspace` kwarg, it creates a
`tempfile.TemporaryDirectory`, threads its path to the inner loop
and the body reader, and cleans up on exit. The adapter and bench
never see a workspace — they only see structured `Submission`
data, matching the §7 "code and execution results, not files"
principle. Tests that pass `workspace=` explicitly keep working;
the wrapper respects an explicit kwarg over its own tempdir.

The wrapper also derives `env_dir = Path(tasks_dir).parent` when
`tasks_dir` is supplied without an explicit `env_dir`. Mirrors the
existing `main.py` derivation; keeps the derivation out of the
adapter API.
