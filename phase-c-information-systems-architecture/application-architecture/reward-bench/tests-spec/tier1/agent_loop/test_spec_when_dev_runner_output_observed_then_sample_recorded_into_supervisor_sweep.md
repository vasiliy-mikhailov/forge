# `test_when_dev_runner_output_observed_then_sample_recorded_into_supervisor_sweep`
Pins the cycle-34 enrichment of the cycle-33 supervisor hook: when an
iteration's tool observation contains a `dev_runner` summary line
(format: `MEAN=<float> MEDIAN=<float> max-tile-best=<int>
(<walltime>s total)`), `run_loop` parses it into a `Sample` tuple
`(iter_n, mean_score, max_tile, walltime_sec)` and feeds the whole
accumulated tuple to `supervisor.judge(sweep)`.
This is the seam that lets the [LlmSupervisor](../../../../src-spec/reward_bench/adapters/llm_supervisor/src_spec_llm_supervisor.md)
see real numbers instead of zeros, which is what [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
requires for plateau recognition.
- **Arrange**: monkeypatch `_call_model` to emit a `bash` tool call
 whose observation will contain a dev_runner-shaped line. Monkeypatch
 `execute_tool` to return `"... MEAN=5000.0 MEDIAN=4800.0
 max-tile-best=512 (1.5s total)"` (the exact format dev_runner.py
 prints). Inject a stub supervisor that captures every sweep it sees.
- **Act**: `run_loop(..., max_iters=1, supervisor=stub,
 supervisor_every_k=1)`.
- **Assert**:
 - The stub supervisor was consulted exactly once.
 - The captured sweep has length 1.
 - Sample fields: `iter_no == 1`, `mean_score == 5000.0`,
 `max_tile == 512`, `walltime_sec == 1.5`.
A sibling test pins the no-match path: a `view` observation (no
dev_runner line) produces a zero-filled placeholder sample (preserves
n_samples == iter_count contract for the supervisor prompt).
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_dev_runner_output_observed_then_sample_recorded_into_supervisor_sweep`.
