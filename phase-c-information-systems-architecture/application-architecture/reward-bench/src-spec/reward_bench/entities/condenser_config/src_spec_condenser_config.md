# `src/reward_bench/entities/condenser_config.py`
`CondenserConfig` is a frozen dataclass — the orchestrator
configuration for the context-compaction step described in
[`SPEC.md`](../../../../SPEC.md): when prompt + reserved output
tokens exceed the model's max_model_len budget, a separate (usually
smaller) model summarises older turns so the agent loop can keep
making progress.
## Fields
| Field | Type | Meaning |
| ---------------- | ------ | -------------------------------------------------------------------------------------- |
| `trigger_tokens` | `int` | Run the condenser when total prompt tokens exceed this. Default in legacy: `40000`. |
| `keep_recent` | `int` | Number of most-recent turns to keep verbatim (NOT summarised). Default in legacy: `8`. |
| `model_id` | `str` | Identifier of the model to use for summarisation; should map to a `ModelTarget.id`. |
## Properties
Frozen, no methods. Pure data.
Behavior (the condenser adapter that consumes this config) is pinned
in a later cycle.
