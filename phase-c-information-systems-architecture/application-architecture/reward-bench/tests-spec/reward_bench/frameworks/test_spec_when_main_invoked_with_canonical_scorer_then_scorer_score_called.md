# `test_when_main_invoked_with_canonical_scorer_then_scorer_score_called`

Pins that the injected `canonical_scorer.score()` is what `main()` calls for canonical scoring (instead of constructing a `DockerCanonicalScorer`).

## Contract

- **Arrange**: Stub `ensure_serving_model`, `VLLM_API_KEY`, and `run_loop` so `main()` reaches the scorer step. A `RecordingScorer` whose `score()` records its args and returns a synthetic `AttemptResult`.
- **Act**: `main(model_id='qwen3.6-27b-awq', config=BenchConfig(max_iters=1,...), canonical_scorer=recorder)`.
- **Assert**: the recorder's `calls` list contains one entry with the submission path and the configured seed range.

## Model client injection point

- **Seam**: `canonical_scorer` DI parameter on `main()`.
- **Mode**: `@pytest.mark.no_fake`.

Test code: [`../../../tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../tests/reward_bench/frameworks/test_main_docker_scorer.py)::`test_when_main_invoked_with_canonical_scorer_then_scorer_score_called`.

## Runtime scope

> **Runtime scope**: unit only.
