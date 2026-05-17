# `test_when_main_invoked_then_config_supervisor_every_k_passed_to_run_loop`
Pins the orchestrator-to-agent_loop wiring for the supervisor: `main()`
constructs an [`LlmSupervisor`](../../../../src-spec/reward_bench/adapters/llm_supervisor/src_spec_llm_supervisor.md)
backed by the bench vLLM endpoint (per [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md), same
model as bench + condenser) and forwards both `supervisor=` and
`supervisor_every_k=config.supervisor_every_k` to `run_loop`.
Without this wiring, the supervisor stack is wired but cold — main()
calls run_loop without the new kwargs and the supervisor never sees
real bench traffic.
- **Arrange**: monkeypatch `ensure_serving`, `score_submission`, and
 `run_loop` to a recording stub that captures kwargs. Build
 `BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
 hard_wall_sec=0.0, supervisor_every_k=7)`.
- **Act**: `main(model_id='qwen3.6-27b-awq', config=config)`.
- **Assert**:
 - `run_loop` captured kwargs include `supervisor_every_k == 7`.
 - The `supervisor` kwarg implements `SupervisorPort`
 (`isinstance(captured['supervisor'], SupervisorPort)`).
Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.
