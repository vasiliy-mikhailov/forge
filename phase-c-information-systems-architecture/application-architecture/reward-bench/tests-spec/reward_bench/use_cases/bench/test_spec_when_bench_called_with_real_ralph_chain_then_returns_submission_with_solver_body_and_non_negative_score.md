# `test_when_bench_called_with_real_ralph_chain_then_returns_submission_with_solver_body_and_non_negative_score`

End-to-end live test of the §7 ralph chain per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
Pins that the chain runs against real infra **and produces a
meaningful Submission** — not just a Submission-shaped no-op. The
prior weaker version (`...then_returns_submission`) passed on
`Submission(body='', score=None, walltime_sec=2.03)`; it proved
the chain could limp through 2 iters and construct an empty
object. That's a smoke for "no crash", not a vindication of the
refactor.

This spec demands the loop actually run long enough for the model
to write code, the canonical scorer to score it, and the wrapper
to lift a real body out of `workspace/submission.best.py`.

- **Arrange**: `Env(tasks_dir=<repo>/tasks, canonical_scorer=
  DockerCanonicalScorer(), model_client=VllmOpenAIClient(
  vllm_base_url, vllm_api_key, 'qwen3.6-27b-awq'))`;
  `cfg = BenchConfig(max_iters=30, hard_wall_sec=60.0)`;
  `adapter = OrchestrateRalphSingleContext(
  run_loop_fn=default_run_loop_fn())`.
- **Act**: `submission = bench(adapter, env, cfg)`.
- **Assert**: all five hold:
    - `isinstance(submission, Submission)` — shape.
    - `'class Solver' in submission.body` — SPEC.md requires
      a `Solver` class.
    - `'from transitions' in submission.body` — SPEC.md requires
      the `transitions` state-machine import.
    - `isinstance(submission.score, float) and submission.score >= 0`
      — the canonical scorer actually scored it; `None` or
      missing score means the loop never produced a scorable
      artifact.
    - `submission.walltime_sec > 1.0` — bench did real work, not
      a no-op short-circuit.

Test code: [`../../../../tests/reward_bench/use_cases/test_bench.py`](../../../../tests/reward_bench/use_cases/test_bench.py)::`test_when_bench_called_with_real_ralph_chain_then_returns_submission_with_solver_body_and_non_negative_score`.

## Model client injection point

- **Seam**: real `VllmOpenAIClient` against the live endpoint via
  the `vllm_base_url` / `vllm_api_key` fixtures.
- **Mode**: **live** — marked `@pytest.mark.live`; opt-in only.

## Runtime scope

> **Runtime scope**: live — real vLLM call (~5-10s per iter), real Docker scoring (~5-10s per execute_submission), real ralph loop. Realistic 5-15 minutes total for `max_iters=30`.
