# `src/reward_bench/entities/model_target.py`

`ModelTarget` is a frozen dataclass — a value object describing one
candidate model the bench can evaluate. It is the "model" half of the
bench's primary input (model + prompt).

## Fields

| Field              | Type | Meaning                                                            |
| ------------------ | ---- | ------------------------------------------------------------------ |
| `id`               | str  | Stable identifier; matches `wiki-compiler/configs/models.yml: id`. |
| `hf_path`          | str  | HuggingFace path; passed to vLLM `--model`.                        |
| `served_name`      | str  | OpenAI-compatible `/v1/models` id; passed to `--served-model-name`.|
| `tool_call_parser` | str  | vLLM tool-call parser id; passed to `--tool-call-parser`.          |
| `max_model_len`    | int  | Context window in tokens; passed to `--max-model-len`.             |

## Properties

- `ModelTarget` is **frozen** (immutable). Equality is by field value.
- All fields are required. Defaults are not provided — every model
  registered with the bench must declare each field explicitly.
- No methods. ModelTarget carries no behavior; it is pure data.

## Where it sits in clean architecture

ModelTarget lives in `src/reward_bench/entities/` because the
orchestrator module owns the question "which models do we evaluate?".
Tier modules (`tier1/`, future `tier2/`, ...) receive a ModelTarget
from the orchestrator; they never construct one themselves.

## Future fields

This entity captures the minimum needed for first-cycle tests. More
config from `models.yml` (rope_scaling, quantization, kv_cache_dtype,
gpu_memory_utilization, chat_template_kwargs, reasoning_parser,
tensor_parallel_size) will land as the tests that need them land.
Per the CATS rule: spec describes only what tests prove.
