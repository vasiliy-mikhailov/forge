"""TierSpec: one row of the 4-tier ladder from SPEC.md.

See src-spec/reward_bench/entities/tier_spec/."""
from dataclasses import dataclass
from typing import Literal


NetworkPolicy = Literal['none', 'vllm_only']


@dataclass(frozen=True)
class TierSpec:
    """Description of one bench tier."""

    tier: int                  # 1..4
    image: str                 # docker image, e.g. "reward-bench-tier1:${VERSION}"
    network_policy: NetworkPolicy
    submission_shape: str      # short description of the submission interface
    reward_n: int              # number of games scored per attempt
    replay_tolerance_pct: float
