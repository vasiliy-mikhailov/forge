# `src_spec_fake_vllm_server_handles_v1_endpoints`
[`FakeVllmServer`](../../../src/adapters/fakes/fake_vllm_server.py) —
in-process responder to vLLM's two HTTP paths. See [SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md).
## Contract
Constructed with `(served_name, max_model_len, chat_replies=None, default_reply=None)`.
`urlopen(req, timeout=600)`:
- Routes by `req.full_url` suffix:
 - `/v1/models` → returns a canned `{data: [{id, max_model_len}]}`
 catalog matching the constructor args.
 - `/v1/chat/completions` → returns `{choices: [{message: <next-reply>}]}`
 drawing from `chat_replies` then `default_reply` on exhaustion.
 - any other URL → returns `{error:...}` with HTTP 404 status.
- Records each call into `self.calls` for test assertions.
- Returns a context-manager response object quacking like
 `urllib.request.urlopen`'s return (`.read()`, `.status`, `__enter__/__exit__`).
Installed by the conftest autouse `_bind_model_client` fixture as a
`urllib.request.urlopen` monkeypatch so test_inference.py and the
session-scoped reply fixtures run offline.
