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

Fitness:
- `'class Solver' in submission.body`
- `len(submission.body) >= 200` — agent emitted real code, not a stub
- `submission.score is a non-negative float` — scorer ran; a 0
  score is valid (crashing solver gets 0)

`from transitions` is NOT asserted — the SKILL spec recommends it
but doesn't enforce it; a working non-FSM solver still validates
the chain.

`submission.walltime_sec` is NOT asserted — it's
`aggregate_walltime_sec` from the canonical scorer (sum of
per-game runtimes). A crashing solver aggregates to ~0; that's
correct semantics for a broken submission, not a chain failure.

- **Arrange**: `MODEL_REGISTRY['qwen3.6-27b-awq']`;
  `BenchConfig(max_iters=1, hard_wall_sec=60.0,
  smoke_early_stop=False)`; `VLLM_API_KEY` monkeypatched from the
  `vllm_api_key` fixture.
- **Act**: `submission = bench_main(target, cfg)`.
- **Assert**: per the fitness list above.

Test code: [`../../../../tests/reward_bench/frameworks/test_bench_main_live.py`](../../../../tests/reward_bench/frameworks/test_bench_main_live.py)::`test_when_bench_main_called_with_real_chain_then_returns_submission_with_solver_body_and_non_negative_score`.

## Model client injection point

- **Seam**: `bench_main`'s default `env_factory` builds
  `VllmOpenAIClient` from the lab serving model + env API key.
- **Mode**: **live** — real SDK, real vLLM, real Docker.

## Runtime scope

> **Runtime scope**: live — full chain end-to-end. ~60-120s
> realistic (one OpenHands run + one canonical score).
