# `test_when_bench_main_called_with_real_chain_then_returns_submission_with_solver_body_and_non_negative_score`

§4 live meta-test. The first measurement against real
infrastructure of the new §2/§4 architecture per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

Drives the full default chain:

```
bench_main
  → _default_env_factory (compose_env_spec: task + harness + budget)
  → OrchestrateSubagentPerIter
       → OpenHandsSolutionGenerator
            → real OpenHands SDK
                 → real vLLM (qwen3.6-27b-awq)
                 → agent's TerminalTool runs dev harness inside docker
                 → final fenced python block in last assistant message
            → extract_fenced_python → body
       → DockerCanonicalScorer.score_body → AttemptResult
  → Submission(body, score, walltime)
```

If this passes, the §4 cutover is complete end-to-end.

- **Arrange**: `MODEL_REGISTRY['qwen3.6-27b-awq']`;
  `BenchConfig(max_iters=1, hard_wall_sec=60.0,
  smoke_early_stop=False)`; `VLLM_API_KEY` monkeypatched from the
  `vllm_api_key` fixture.
- **Act**: `submission = bench_main(target, cfg)`.
- **Assert**:
  `'class Solver' in submission.body`;
  `submission.score is a non-negative float`;
  `submission.walltime_sec > 1.0`.

`from transitions` is NOT asserted — the SKILL spec recommends
it strongly but doesn't enforce it; a working non-FSM solver is
still a successful chain run. The §4 cutover passes if the agent
emits any working Solver class.

Test code: [`../../../../tests/reward_bench/frameworks/test_bench_main_live.py`](../../../../tests/reward_bench/frameworks/test_bench_main_live.py)::`test_when_bench_main_called_with_real_chain_then_returns_submission_with_solver_body_and_non_negative_score`.

## Model client injection point

- **Seam**: `bench_main`'s default `env_factory` builds
  `VllmOpenAIClient` from the lab serving model + env API key.
- **Mode**: **live** — real SDK, real vLLM, real Docker.

## Runtime scope

> **Runtime scope**: live — full chain end-to-end. ~60-120s
> realistic (one OpenHands run + one canonical score).
