# `test_when_main_invoked_then_config_hard_wall_sec_passed_to_score_submission`

Pins the orchestrator-to-use-case wiring: `main()` reads
`config.hard_wall_sec` from the `BenchConfig` argument and passes it
through to `score_submission`. Without this wiring, cycle-23's cap
and cycle-24's input knob exist but never connect — a campaign with
`BenchConfig(hard_wall_sec=60)` would still hang because `main()`
would call `score_submission` without forwarding the knob.

This is the **glue** test pinning the channel between the
configuration entity and the application-layer cap.

- **Arrange**: monkeypatch `agent_loop.run_loop` to write a
  trivially-valid `submission.py` and `score_submission` to a
  recording stub that captures kwargs. Short-circuit
  `ensure_serving` to avoid the vLLM round-trip. Build
  `BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
  hard_wall_sec=42.0)`.
- **Act**: call `main(model_id='qwen3.6-27b-awq', config=config)`.
- **Assert**: the recording stub captured exactly one call whose
  kwargs include `hard_wall_sec == 42.0`.

This test uses a stub `score_submission` so it does NOT exercise the
cycle-23 cap behavior — that's already pinned in
`tests/tier1/use_cases/test_score_submission.py`. This cycle only
pins the WIRING.

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.

