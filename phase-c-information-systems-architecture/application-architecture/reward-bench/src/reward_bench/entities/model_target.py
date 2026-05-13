"""ModelTarget: a frozen value object describing one candidate model.

See src-spec/reward_bench/entities/model_target/src_spec_model_target.md.

Inputs to the bench (the "model" half of model + prompt) live here as
domain entities of the orchestrator module. Each registry entry in
wiki-compiler/configs/models.yml corresponds to one ModelTarget."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelTarget:
    """One candidate model the bench can evaluate.

    Fields are the minimum needed to (a) identify the model uniquely
    and (b) wire a vLLM container for it. More config (rope_scaling,
    quantization, etc.) is added as use cases require it; see CATS
    rule that spec grows only with tests."""

    id: str
    """Stable identifier (matches forge/.env: INFERENCE_ACTIVE_MODEL_ID)."""

    hf_path: str
    """HuggingFace model path passed to vLLM --model."""

    served_name: str
    """OpenAI-compatible /v1/models id (--served-model-name)."""

    max_model_len: int
    """Context window in tokens (--max-model-len)."""

    tool_call_parser: str
    """vLLM tool-call parser identifier (--tool-call-parser)."""
