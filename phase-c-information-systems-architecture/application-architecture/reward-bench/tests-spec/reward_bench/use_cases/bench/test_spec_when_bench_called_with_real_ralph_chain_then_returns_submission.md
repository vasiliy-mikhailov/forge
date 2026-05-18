# `test_when_bench_called_with_real_ralph_chain_then_returns_submission`

End-to-end live vindication of the §7 ralph chain per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
Wires the real `OrchestrateRalphSingleContext` with the production
`default_run_loop_fn`, a real `DockerCanonicalScorer`, a real
`VllmOpenAIClient` against the live vLLM endpoint, and a real
tasks dir; calls `bench(adapter, env, cfg)` with a tiny
`max_iters` and asserts a `Submission` comes back.

If this passes, the entire 163→190 refactor — Submission entity,
Orchestrator Port, Env, bench composition, ralph adapter, wrapper,
URL extraction, public attrs on VllmOpenAIClient — is structurally
sound against real infra.

- **Arrange**: `Env(tasks_dir=<repo>/tasks, canonical_scorer=
  DockerCanonicalScorer(), model_client=VllmOpenAIClient(
  vllm_base_url, vllm_api_key, 'qwen3.6-27b-awq'))`;
  `cfg = BenchConfig(max_iters=2, hard_wall_sec=60.0)`;
  `adapter = OrchestrateRalphSingleContext(
  run_loop_fn=default_run_loop_fn())`.
- **Act**: `bench(adapter, env, cfg)`.
- **Assert**: result is a `Submission` instance.

Test code: [`../../../../tests/reward_bench/use_cases/test_bench.py`](../../../../tests/reward_bench/use_cases/test_bench.py)::`test_when_bench_called_with_real_ralph_chain_then_returns_submission`.

## Model client injection point

- **Seam**: real `VllmOpenAIClient` against the live endpoint via
  the `vllm_base_url` / `vllm_api_key` fixtures.
- **Mode**: **live** — marked `@pytest.mark.live`; opt-in only.

## Runtime scope

> **Runtime scope**: live — real vLLM call, real Docker scoring, real ralph loop. Takes ~30-60s.
