# `src_spec_extract_fenced_python`

[`../../../../src/reward_bench/adapters/extract_fenced_python.py`](../../../../src/reward_bench/adapters/extract_fenced_python.py)
is the §4 boundary helper per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

Per §4 binding: the OpenHands agent emits its final Solver code
as a fenced ```` ```python ... ``` ```` (or bare ```` ``` ... ``` ````)
block in its last assistant message. `OpenHandsSolutionGenerator`
calls this helper to lift the body out as a string.

```python
def extract_fenced_python(msg: str) -> str: ...
```

Pure function over strings. Returns the inner text of the *last*
fenced block (agents may show iterations; the final block is the
answer). Returns `''` when no fence is present — the orchestrator
continues, the Runner scores the empty body (it will score 0),
the loop advances.

This is the single point where the OpenHands → bench boundary
parses a string. No file IO, no SDK calls.
