# `test_when_main_invoked_then_uses_ensure_serving_model_with_picked_target`
Pins the **model-target wiring** in [`main()`](../../../../src/reward_bench/frameworks/main.py):
when `main()` is invoked with a specific `model_id`, the lab vLLM
container is provisioned to serve THAT model — not the hardcoded
default.
**Real-world repro.** Before,
`main()` called the legacy
[`ensure_serving()`](../../../../src/tier1/inference.py). The cycle-42
[`ensure_serving_model(target)`](../../../../src/tier1/inference.py)
existed but was never wired through. Every parameterised smoke
invocation called `ensure_serving_model(target)` from the test
body, then `main()` called the legacy `ensure_serving()`, which
silently swapped the container BACK to AWQ. Result: all 22 smoke
parameters ran against `qwen3.6-27b-awq`. Uncovered when docker
inspect showed `--model cyankiwi/Qwen3.6-27B-AWQ-INT4` during the
`[qwen3.6-27b-fp8]` parametrise.
- **Arrange**: monkeypatch the inference functions in `main`'s
 namespace:
 - `ensure_serving` (the legacy one) → raises `AssertionError`
 ("main called the legacy ensure_serving — should call
 ensure_serving_model(target)"). If it fires, RED.
 - `ensure_serving_model` (the cycle-42 one) → records its
 `target` argument then raises a sentinel `RuntimeError` to
 short-circuit `main()` before it tries to call vLLM. The
 sentinel marks GREEN.
- **Act**: `main(model_id='qwen3.6-27b-fp8',
 config=BenchConfig(max_iters=1, n_trials=1))`.
- **Assert**:
 - `RuntimeError` containing `'test marker'` was raised
 (i.e. main reached the right call site).
 - The captured `target.id == 'qwen3.6-27b-fp8'`.
 - The captured `target.served_name == 'qwen3.6-27b-fp8'`.
 - The captured `target.hf_path == 'Qwen/Qwen3.6-27B-FP8'`
 (verifies `_pick_model` resolved to the right `ModelTarget`).
Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.
