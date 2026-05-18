# `src_spec_dominates_at_budget`

[`../../../../src/reward_bench/use_cases/dominates_at_budget.py`](../../../../src/reward_bench/use_cases/dominates_at_budget.py)
defines the §7 dominance harness primitive per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

```python
def dominates_at_budget(
    strong: Orchestrator,
    weak: Orchestrator,
    env: Env,
    cfg: BenchConfig,
    walltime_budget_sec: float,
) -> bool: ...
```

Returns `True` iff `best_score(strong.orchestrate(env, cfg), t)`
exceeds `best_score(weak.orchestrate(env, cfg), t)`. Pure
composition over `Orchestrator.orchestrate` and `best_score`; any
IO is the orchestrators'.

The §7 fitness test asserts this returns `True` for
`(strong=orchestrate_subagent_per_iter, weak=orchestrate_ralph_single_context)`
across `MODEL_REGISTRY` at a fixed walltime budget.
