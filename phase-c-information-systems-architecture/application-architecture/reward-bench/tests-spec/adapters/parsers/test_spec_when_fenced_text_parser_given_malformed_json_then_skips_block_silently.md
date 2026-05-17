# `test_when_fenced_text_parser_given_malformed_json_then_skips_block_silently`
## Behaviour
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_fenced_text_parser_given_malformed_json_then_skips_block_silently`.
## Runtime scope
> **Runtime scope**: unit only — pure function over `AssistantReply`; no runtime boundary.
