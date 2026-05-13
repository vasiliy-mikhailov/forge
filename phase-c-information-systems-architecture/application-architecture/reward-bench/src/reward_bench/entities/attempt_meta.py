"""AttemptMeta: one bench attempt's identity record.

See src-spec/reward_bench/entities/attempt_meta/."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


TaskId = Literal['2048']


@dataclass(frozen=True)
class AttemptMeta:
    """Identity + provenance of one bench attempt. Mirrors SPEC.md."""

    run_id: str               # e.g. "2026-05-04-180423-qwen36-27b-fp8-tier1"
    model_id: str             # from models.yml
    served_model_name: str    # what vLLM advertises
    task_id: TaskId           # currently only "2048"
    tier: int                 # 1..4
    started_at: datetime
    image_digest: str         # sha256 of sandbox image
    forge_commit: str         # forge git rev at attempt time
