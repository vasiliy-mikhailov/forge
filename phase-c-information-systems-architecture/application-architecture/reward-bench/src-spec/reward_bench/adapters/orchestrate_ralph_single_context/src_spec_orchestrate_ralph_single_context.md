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

Field mapping from the `run_loop_fn` return dict to `Submission`:

    body          ← result['body']
    score         ← result['best_dev_mean']
    walltime_sec  ← result['walltime_sec']

The real `run_loop` does not currently produce `'body'` or
`'walltime_sec'`; a wrapper that lifts `workspace/submission.best.py`
and measures loop time supplies them.
