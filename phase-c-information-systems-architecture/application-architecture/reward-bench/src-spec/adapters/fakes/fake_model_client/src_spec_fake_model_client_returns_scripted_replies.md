# `src_spec_fake_model_client_returns_scripted_replies`

[`FakeModelClient`](../../../src/adapters/fakes/fake_model_client.py) is
a test [`ModelClient`](../../../src/ports/model_client.py) returning
pre-scripted replies. See [ADR 0012](../../../docs/adr/0012-light-speed-offline-testing-via-injectable-fake-model-client.md).

## Contract

Constructed with `(script: tuple[AssistantReply, ...], *, repeat_last=True)`.

`call(messages, *, tools, temperature, max_tokens, model_id)`:

- Records the call onto `self.calls` (a list of dicts capturing all
  kwargs). Tests assert on these to verify the agent loop sent the
  expected payload.
- Returns the next reply from the script. After exhaustion:
  - `repeat_last=True` (default): returns the last reply forever (loop
    stalls cleanly rather than crashing).
  - `repeat_last=False`: raises `IndexError` (lets tests assert exact
    iter count).
- Normalises `content` to empty string and `tool_calls` to empty list
  on missing keys.

Used by the conftest autouse `_bind_model_client` fixture as the
default-bound model client so the whole test suite runs without GPU.
