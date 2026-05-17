# \`test_when_reply_inspected_then_contains_one_fenced_python_block\`
Pins parser layer L3.2: the model reply to the SKILL_tier1 prompt
contains at least one fenced Python code block.
- **Arrange**: session-scoped \`skill_tier1_reply\` fixture (one chat
 call to the lab vLLM with SKILL_tier1.md at max_tokens=32768).
- **Act**: call \`src.tier1.adapters.parser.has_fenced_python_block(reply)\`.
- **Assert**: returns True.
Test code: [\`tests/tier1/test_parser.py\`](../../tests/tier1/test_parser.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — pure-function tool-call parser; scale-invariant.

Test code: [`../../../../tests/tier1/adapters/test_parser.py`](../../../../tests/tier1/adapters/test_parser.py)::`test_when_reply_inspected_then_contains_one_fenced_python_block`.
