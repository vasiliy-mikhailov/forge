# `test_when_call_model_invoked_then_max_tokens_matches_legacy_budget`

Pins the `max_tokens` cap on chat-completions requests per
[hypothesis #7](../../../../docs/hypotheses_agent_loop_regression.md).
The [legacy loop](../../../../src/tier1/legacy_agent_loop.py) uses
`max_tokens=12288`; the active `agent_loop.py` was at 32768 before
this cycle, allowing the model to ramble in long code-only replies
instead of choosing concise iter+test+refine cycles.

Switching to 12288 caps each turn's output and (hypothesis) nudges
the model toward making decisive tool-call choices like `bash
dev_runner` rather than dumping multi-hundred-line code blocks.

- **Arrange**: monkeypatch `urllib.request.urlopen` so the test
  intercepts the HTTP POST request body and records the JSON.
- **Act**: call `agent_loop._call_model(url, key, messages)` with
  default kwargs.
- **Assert**: the captured payload has `max_tokens == 12288`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
