# `src_spec_best_submission`

[`../../../../src/reward_bench/use_cases/best_submission.py`](../../../../src/reward_bench/use_cases/best_submission.py)
defines `best_submission` — the pure `argmax_by_score` primitive that
the bench composes with an `Orchestrator` per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7:

    bench env cfg = argmaxBy (.score) (orchestrate env cfg)

Signature:

```python
def best_submission(submissions: Iterable[Submission]) -> Submission: ...
```

Pure: no IO, no env. Score lives on the `Submission` value object
— the orchestrator computes the score during enumeration and the
bench just picks. Returns the same-identity instance, not a copy.

Allowed imports (kept minimal — pure reduction):

    typing
    src.tier1.entities.submission
