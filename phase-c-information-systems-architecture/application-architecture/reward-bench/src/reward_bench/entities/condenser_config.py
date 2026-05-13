"""CondenserConfig: orchestrator-side configuration for the context-compaction
step described in SPEC.md.

See src-spec/reward_bench/entities/condenser_config/."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CondenserConfig:
    """Frozen configuration for the agent-loop's context-compaction layer."""

    trigger_tokens: int
    keep_recent: int
    model_id: str
