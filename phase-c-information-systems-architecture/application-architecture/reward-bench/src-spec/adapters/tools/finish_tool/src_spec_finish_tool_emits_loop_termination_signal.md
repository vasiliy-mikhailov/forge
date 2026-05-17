# `src_spec_finish_tool_emits_loop_termination_signal`
[`FinishTool`](../../../../src/adapters/tools/finish_tool.py) — the
[`Tool`](../../../../src/ports/tool.py) adapter that signals end of
agent loop. The returned string format IS the loop-termination
protocol — the agent loop parses it to set `finished=True`.
The Port contract is in
[the Tool Port src_spec](../../../../src-spec/ports/tool/src_spec_when_tool_dispatched_with_args_then_returns_observation_string.md).
This file documents FinishTool's added surface: the termination
string format.
## Adapter-own surface
### Termination string
`FinishTool.dispatch({'note': note}, ctx)` returns:
```
<finish>{note}</finish>
```
The agent loop in
[`run_loop`](../../../../src/tier1/agent_loop.py) parses observation
strings and, when an observation begins with `<finish>`, sets
`finished=True` and exits the loop. The note inside the tags is
discarded for loop logic — it serves only as a human-readable trace
in logs.
### Missing or empty note
If `args` omits `note`, `args.get('note', '')` returns empty string;
the dispatch returns `<finish></finish>`. The loop still terminates
— note content is irrelevant to termination, only the tag wrapping.
### Args contract
| key | required | meaning |
|--------|----------|--------------------------------------------------|
| `note` | no | Optional reasoning string for the trace log. |
FinishTool never raises — it just emits the tag-wrapped string.
## Test coverage
- [`test_when_finish_dispatched_then_returns_finish_signal`](../../../../tests/adapters/test_tier1_tool_registry.py)
- [`test_when_finish_dispatched_without_note_then_empty_finish`](../../../../tests/adapters/test_tier1_tool_registry.py)
