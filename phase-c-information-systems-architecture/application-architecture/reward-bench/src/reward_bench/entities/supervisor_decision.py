"""SupervisorDecision: frozen-entity return type of the supervisor."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SupervisorDecision:
    """Frozen result of one supervisor consultation.

    plateau: bool — classification of the recent sweep.
    stop_recommended: bool — distinct from plateau (conservative bias).
    reasoning: str — short free-text rationale surfaced into the
      finish note when stop_recommended fires.
    """

    plateau: bool
    stop_recommended: bool
    reasoning: str
