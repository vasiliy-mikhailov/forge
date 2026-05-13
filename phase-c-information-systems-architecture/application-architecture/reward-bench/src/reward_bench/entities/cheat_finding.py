"""CheatFinding: one row of the anti-cheat report.

See src-spec/reward_bench/entities/cheat_finding/."""
from dataclasses import dataclass
from typing import Literal


Layer = Literal['ast', 'bandit']
Severity = Literal['info', 'warning', 'rejected']


@dataclass(frozen=True)
class CheatFinding:
    """One finding emitted by the AST or bandit anti-cheat scanner."""

    layer: Layer
    severity: Severity
    rule: str
    line: int
    code: str
