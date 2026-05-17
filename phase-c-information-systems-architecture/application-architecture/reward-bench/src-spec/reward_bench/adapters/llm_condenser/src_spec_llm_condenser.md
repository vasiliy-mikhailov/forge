# `src/reward_bench/adapters/llm_condenser.py`
`LlmCondenser` implements [`CondenserPort`](../../use_cases/condenser_port/src_spec_condenser_port.md)
by replacing older turns with a single summary message. The
summarisation call is delegated to an injected callable so the
adapter remains testable without a live LLM.
Per [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md),
the wiring layer supplies a callable backed by the bench-model vLLM
endpoint (same `ModelTarget` as the model under test).
## Constructor
 LlmCondenser(summarise: Callable[[tuple[dict,...]], str],
 model_id: str,)
`summarise(older_turns)` returns a single string summary. The adapter
wraps that string in a `{'role': 'system', 'content':...}` message
that replaces the older turns in the returned tuple. `model_id`
records which model produced the summary (for the leaderboard /
artifact provenance).
## `condense(messages, config) -> tuple[dict,...]`
Two paths:
1. **Pass-through** when `len(messages) <= 1 + config.keep_recent`
 — there are not enough older turns to compact. Returns
 `tuple(messages)` unchanged.
2. **Compact** when `len(messages) > 1 + config.keep_recent`:
 - `system = messages[0]` (preserved).
 - `recent = messages[-config.keep_recent:]` (preserved).
 - `older = messages[1:-config.keep_recent]` (compacted).
 - `summary = summarise(older)`.
 - Return `(system, {'role': 'system', 'content': f'[summary of
 N older turns] {summary}'}, *recent)`.
## Layer purity
`adapters/` may import `entities/` and `use_cases/`. `LlmCondenser`
imports `CondenserConfig` (entities) but does not import
`frameworks/` — the vLLM call lives behind the injected `summarise`
callable, which the wiring layer constructs.
