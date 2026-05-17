# `test_spec_run_loop_dependency_injection`
Pins the **run_loop port-DI seam** introduced proper per
[ step 2](../../../../SOLUTION-ARCHITECTURE.md).
## Why
After the three ports — `ModelClient`, `ToolRegistry`,
`ProtocolParser` — exist as adapters. But `run_loop` still reaches
into module-level functions (`_call_model`, `execute_tool`,
`parse_tool_calls`) to do its work. Tests had to monkeypatch those
to inject fakes — leaky, not DI.
makes `run_loop` accept the three ports as optional
parameters. When supplied, the loop calls through them directly.
When not, it falls back to the legacy module-level seams so pre-cycle-99
callers and monkeypatching tests stay green during the transition.
## Contract
`run_loop(*, model_client=None, tool_registry=None, protocol_parser=None,...)`
- `model_client` (`ModelClient` port): if non-None, `model_client.call(messages, tools,...)` replaces `_call_model(...)`.
- `tool_registry` (`ToolRegistry` port): if non-None, `tool_registry.dispatch(name, args, ctx)` replaces `execute_tool(...)`. Also supplies `schemas` when `model_client` needs tool advertisement.
- `protocol_parser` (`ProtocolParser` port): if non-None, `protocol_parser.extract(reply)` replaces `parse_tool_calls(...)`.
All three are independent: a test may inject only the parts it cares about and let the rest fall back to legacy.
## Model client injection point
- **Seam**: `run_loop(model_client=...)` directly.
- **Default**: when no `model_client` is passed, the legacy
 `_call_model` is invoked, allowing pre-cycle-99 tests'
 monkeypatching to continue working.
- **Live override**: any caller may pass a `VllmOpenAIClient`
 instance to bind to a real vLLM container, OR pass `FakeModelClient`
 for hermetic offline runs.
## Tests
### `test_when_run_loop_called_with_model_client_then_calls_pass_through_port`
- **Arrange**: a `FakeModelClient` scripted with a single `finish` reply.
- **Act**: `run_loop(..., model_client=fake)` with `max_iters=3`.
- **Assert**: `fake.calls` is non-empty (port was used). `result['finished']` is True. Tools were advertised on the call.
### `test_when_run_loop_called_with_tool_registry_then_dispatch_goes_through_port`
- **Arrange**: a recording `ToolRegistry` whose `dispatch` notes every call.
- **Act**: `run_loop(..., tool_registry=registry, model_client=fake)`.
- **Assert**: `registry.dispatched` contains the scripted `finish` call. `execute_tool` (module-level) was NOT consulted.
### `test_when_run_loop_called_with_protocol_parser_then_extract_goes_through_port`
- **Arrange**: a recording `ProtocolParser` returning a single `finish` call.
- **Act**: `run_loop(..., protocol_parser=parser)`.
- **Assert**: `parser.calls` contains at least one extracted reply. `parse_tool_calls` (module-level) was NOT consulted.
### `test_when_run_loop_called_without_ports_then_legacy_seams_used`
- **Arrange**: monkeypatch `agent_loop._call_model` to a counter.
- **Act**: `run_loop(...)` with NO port arguments.
- **Assert**: the counter increments (legacy seam invoked); the test proves back-compat for pre-cycle-99 callers.
Test code: [`tests/tier1/test_run_loop_di.py`](../../../../tests/tier1/test_run_loop_di.py).
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
