# `test_when_llm_supervisor_reply_unparseable_then_returns_conservative_fallback`
Pins the no-silent-fix surface for [`LlmSupervisor`](../../../../src-spec/reward_bench/adapters/llm_supervisor/src_spec_llm_supervisor.md):
when the model's reply does not contain a parseable JSON object, the
adapter returns a CONSERVATIVE fallback (`plateau=False,
stop_recommended=False`) with a `reasoning` that starts with
`supervisor parse-error:`. The agent loop NEVER sees an exception
from the supervisor.
Three failure shapes share this contract:
 - reply is not JSON at all
 - reply is JSON but missing required keys
 - `ask` itself raises
This test covers the first shape (most common). The other two are
sibling tests in the same file.
- **Arrange**: stub `ask` returns the string
 `"I think this is plateau but I'm not sure"` (no JSON).
- **Act**: `decision = LlmSupervisor(ask, 'qwen3.6-27b-awq').judge(sweep)`.
- **Assert**:
 - `decision.plateau is False` (conservative: don't stop on a
 parse error).
 - `decision.stop_recommended is False`.
 - `decision.reasoning.startswith('supervisor parse-error:')`.
Test code: [`tests/reward_bench/adapters/test_llm_supervisor.py`](../../../../tests/reward_bench/adapters/test_llm_supervisor.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — parser/fallback semantics over scripted replies; live model coverage is via run_loop @live tests.
