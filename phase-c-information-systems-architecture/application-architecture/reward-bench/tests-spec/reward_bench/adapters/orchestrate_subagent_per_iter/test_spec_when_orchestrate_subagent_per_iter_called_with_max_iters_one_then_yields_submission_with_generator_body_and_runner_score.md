# `test_when_orchestrate_subagent_per_iter_called_with_max_iters_one_then_yields_submission_with_generator_body_and_runner_score`

Pins the §2 `OrchestrateSubagentPerIter` adapter at minimal scope:
one iter, single yielded `Submission`. Calls
`SolutionGenerator.generate(snapshot)` for the body, calls
`Runner.score_body(body, seeds)` for the score. The Submission's
fields all come from these two role calls — no ralph-style
accumulating context.

- **Arrange**: `body = 'class Solver: pass\n'`;
  `FakeSolutionGenerator(body=body)`;
  `FakeCanonicalScorer(default_result=AttemptResult(mean_score=99.0,
  n_games=5, hard_wall_sec=...))`; minimal `Env`,
  `BenchConfig(max_iters=1)`.
- **Act**: `subs = list(adapter.orchestrate(env, cfg))`.
- **Assert**: `len(subs) == 1`; `subs[0].body == body`;
  `subs[0].score == 99.0`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_subagent_per_iter.py`](../../../../tests/reward_bench/adapters/test_orchestrate_subagent_per_iter.py)::`test_when_orchestrate_subagent_per_iter_called_with_max_iters_one_then_yields_submission_with_generator_body_and_runner_score`.

## Model client injection point

- **Seam**: constructor-injected `solution_generator` and `runner`.
- **Mode**: **fake** — both Fake adapters.

## Runtime scope

> **Runtime scope**: unit only — three-role composition with fake generator + fake runner.
