# `test_when_run_loop_called_with_protocol_parser_then_extract_goes_through_port`

Pins the DI seam for `ProtocolParser`: when `run_loop(...,
protocol_parser=P)`, `P.extract()` decodes replies instead of the
module-level `parse_tool_calls`.

## Contract

- **Arrange**: a `RecordingParser(ProtocolParser)` that records each
  reply into `.calls` and always returns one `ToolCall(name='finish',
  args={'note': 'parsed'})`. `FakeModelClient` with arbitrary
  content (the parser ignores it).
- **Act**: `run_loop(..., model_client=fake_client,
  protocol_parser=parser, max_iters=3)`.
- **Assert**: `parser.calls` has at least one entry (the parser was
  consulted) AND the loop terminated via the synthetic `finish` call.

## Model client injection point

- **Seam**: `protocol_parser` constructor arg on `run_loop`.
- **Mode**: fake (recording parser explicitly injected).

Test code: [`../../tests/tier1/test_run_loop_di.py`](../../tests/tier1/test_run_loop_di.py)::`test_when_run_loop_called_with_protocol_parser_then_extract_goes_through_port`.

## Runtime scope

> **Runtime scope**: unit only.
