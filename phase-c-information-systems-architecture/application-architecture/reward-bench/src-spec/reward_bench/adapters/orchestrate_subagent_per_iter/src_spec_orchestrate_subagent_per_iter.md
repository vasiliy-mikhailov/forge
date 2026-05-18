# `src_spec_orchestrate_subagent_per_iter`

[`../../../../src/reward_bench/adapters/orchestrate_subagent_per_iter.py`](../../../../src/reward_bench/adapters/orchestrate_subagent_per_iter.py)
is the §2 three-role orchestrator per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
Composes a `SolutionGenerator` (the LLM-side role) with a `Runner`
(the scoring role). Fresh `ContextSnapshot` per iter.

Constructor:

```python
OrchestrateSubagentPerIter(
    solution_generator: SolutionGenerator,
    runner: CanonicalScorerPort,
)
```

Method:

```python
def orchestrate(self, env: Env, cfg: BenchConfig) -> Iterable[Submission]:
    for _ in range(cfg.max_iters):
        snapshot = ContextSnapshot(env_spec=..., best_so_far=...,
                                   history_digest=..., iters_remaining=...,
                                   time_remaining_sec=..., budget_sec_per_seed=...)
        body  = self._solution_generator.generate(snapshot)
        attempt = self._runner.score_body(body, seeds, hard_wall_sec=...)
        yield Submission(body=body, score=attempt.mean_score,
                         walltime_sec=attempt.aggregate_walltime_sec)
```

The orchestrator holds NO model context. Its loop body is short
and self-evident: build snapshot → ask generator → score body →
yield. Cumulative state (best so far, history digest, remaining
budget) lives in process memory and feeds the next snapshot.
