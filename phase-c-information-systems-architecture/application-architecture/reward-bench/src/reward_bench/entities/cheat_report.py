"""CheatReport: per-attempt anti-cheat verdict envelope.

See src-spec/reward_bench/entities/cheat_report/."""
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

from src.reward_bench.entities.cheat_finding import CheatFinding


NetworkPolicy = Literal['none', 'vllm_only']
Verdict = Literal['clean', 'warning', 'rejected']


@dataclass(frozen=True)
class CheatReport:
    """Verdict envelope around AST + bandit findings."""

    findings: Tuple[CheatFinding, ...]
    network_policy: NetworkPolicy
    replay_score_match: Optional[bool]
    replay_tolerance_pct: float
    verdict: Verdict
    rejected_reason: Optional[str]
