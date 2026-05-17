# `test_when_main_default_canonical_scorer_is_docker_canonical_scorer`

Pins the production default: when `canonical_scorer` is omitted, `main()` lazily constructs a `DockerCanonicalScorer`.

## Contract

- **Arrange**: Monkeypatch `DockerCanonicalScorer.__init__` and `.score` to record invocation flags into `captured`. Stub `ensure_serving_model`, `VLLM_API_KEY`, `run_loop` (writes a valid submission body).
- **Act**: `main(model_id='qwen3.6-27b-awq', config=BenchConfig(max_iters=1,...))` — no `canonical_scorer` kwarg.
- **Assert**: `captured['constructed'] is True` AND `captured['scored'] is True`.

## Model client injection point

- **Seam**: `DockerCanonicalScorer` class (monkeypatched).
- **Mode**: `@pytest.mark.no_fake`.

Test code: [`../../../tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../tests/reward_bench/frameworks/test_main_docker_scorer.py)::`test_when_main_default_canonical_scorer_is_docker_canonical_scorer`.

## Runtime scope

> **Runtime scope**: unit only.
