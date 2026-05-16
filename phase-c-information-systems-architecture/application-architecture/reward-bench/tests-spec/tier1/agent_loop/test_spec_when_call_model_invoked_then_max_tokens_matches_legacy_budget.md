# `test_when_call_model_invoked_then_max_tokens_matches_legacy_budget`

Pins the `max_tokens` cap on chat-completions requests at
`max_tokens=12288`. Tighter cap forces concise iter+test+refine cycles
instead of long code-only replies.

Switching to 12288 caps each turn's output and (hypothesis) nudges
the model toward making decisive tool-call choices like `bash
dev_runner` rather than dumping multi-hundred-line code blocks.

- **Arrange**: monkeypatch `urllib.request.urlopen` so the test
  intercepts the HTTP POST request body and records the JSON.
- **Act**: call `agent_loop._call_model(url, key, messages)` with
  default kwargs.
- **Assert**: the captured payload has `max_tokens == 12288`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

