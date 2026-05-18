# `src_spec_best_score`

[`../../../../src/reward_bench/use_cases/best_score.py`](../../../../src/reward_bench/use_cases/best_score.py)
defines the §7 dominance-test primitive per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md):

    best_score env cfg t =
        max { score env s
            | s in orchestrate env cfg,
              submission_walltime s <= t }

Pure reduction:

```python
def best_score(
    submissions: Iterable[Submission],
    walltime_budget_sec: float,
) -> float: ...
```

Filters by `walltime_sec <= walltime_budget_sec`, returns the
argmax-by-score's `score`. No IO, no env — Submission already
carries its score and walltime; the orchestrator did that work.
