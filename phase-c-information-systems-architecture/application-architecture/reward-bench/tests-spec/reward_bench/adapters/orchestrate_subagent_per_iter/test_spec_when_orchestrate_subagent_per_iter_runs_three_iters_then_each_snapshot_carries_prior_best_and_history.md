# `test_when_orchestrate_subagent_per_iter_runs_three_iters_then_each_snapshot_carries_prior_best_and_history`

Pins §2 (SOLUTION-ARCHITECTURE.md): the `ContextSnapshot` handed
to the `SolutionGenerator` on iter k reflects the orchestrator's
cumulative state from iters 1..k-1. Specifically:

- `best_so_far` is the highest-scored `Submission` yielded so far
  (the zero baseline on iter 1).
- `history_digest` is a tuple of prior submissions in iter order
  (empty on iter 1).

Without this, iter 2..N see exactly what iter 1 saw and the §2
architecture cannot deliver iterative refinement.

The test scripts three iters with scores `[10.0, 5.0, 20.0]`. A
recording `SolutionGenerator` captures the snapshot it receives
each iter and returns a unique body. A scripted runner returns
`AttemptResult`s with the scripted scores. After `list(orchestrate(...))`:

- iter 1 snapshot: `best_so_far.score == 0.0`, `history_digest == ()`
- iter 2 snapshot: `best_so_far.score == 10.0` (iter 1's),
  `history_digest` is a 1-tuple of iter 1's submission
- iter 3 snapshot: `best_so_far.score == 10.0` (iter 1 still beats
  iter 2's 5.0), `history_digest` is a 2-tuple of iter 1 + iter 2

- **Arrange**: a recording `SolutionGenerator`; a scripted runner;
  `Env(tasks_dir=tmp_path, canonical_scorer=...)`;
  `BenchConfig(max_iters=3)`.
- **Act**: `list(orch.orchestrate(env, cfg))`.
- **Assert**: per-iter snapshot fields per the table above.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_subagent_per_iter.py`](../../../../tests/reward_bench/adapters/test_orchestrate_subagent_per_iter.py)::`test_when_orchestrate_subagent_per_iter_runs_three_iters_then_each_snapshot_carries_prior_best_and_history`.

## Model client injection point

- **Seam**: recording `SolutionGenerator` + scripted runner; no
  model_client involved.
- **Mode**: **fake** — pure orchestration test.

## Runtime scope

> **Runtime scope**: unit only — three iters of pure dispatch, no
> Docker, no vLLM.
