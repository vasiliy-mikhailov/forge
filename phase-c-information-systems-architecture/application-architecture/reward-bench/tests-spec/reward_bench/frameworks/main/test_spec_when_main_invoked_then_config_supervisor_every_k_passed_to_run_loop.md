# `test_when_main_invoked_then_config_supervisor_every_k_passed_to_run_loop`

Pins the orchestrator-to-agent_loop wiring for the supervisor: `main()`
constructs an [`LlmSupervisor`](
../../../../src-spec/reward_bench/adapters/llm_supervisor/src_spec_llm_supervisor.md)
backed by the bench vLLM endpoint (per [ADR 0001](
../../../../docs/adr/0001-condenser-uses-same-model-as-bench.md), same
model as bench + condenser) and forwards both `supervisor=` and
`supervisor_every_k=config.supervisor_every_k` to `run_loop`.

Without this wiring, cycles 30-34 are a wired-but-cold stack — main()
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
