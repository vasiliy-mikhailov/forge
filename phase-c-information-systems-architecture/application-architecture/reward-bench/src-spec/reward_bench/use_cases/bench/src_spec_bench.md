# `src_spec_bench`

[`../../../../src/reward_bench/use_cases/bench.py`](../../../../src/reward_bench/use_cases/bench.py)
defines the top-level `bench` per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7:

    bench env cfg = argmaxBy (.score) (orchestrate env cfg)

Signature:

```python
def bench(
    orchestrator: Orchestrator,
    env: Env,
    cfg: BenchConfig,
) -> Submission: ...
```

Pure composition of `Orchestrator.orchestrate` (which produces
candidate Submissions under `env`/`cfg`) and `best_submission`
(which picks the argmax by score). No IO of its own — any IO
belongs to the orchestrator adapter.
