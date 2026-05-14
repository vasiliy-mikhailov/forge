"""SupervisorDecision: frozen-entity return type of the supervisor.

See src-spec/reward_bench/entities/supervisor_decision/src_spec_supervisor_decision.md.

Per ADR 0005, the supervisor watches sweep data (recent dev_runner
scores) and decides whether the agent loop should stop. This entity
is the only datum that crosses the supervisor port boundary back
into agent_loop.

Three fields, frozen, no IO:
- plateau: bool — supervisor's classification of the recent sweep.
- stop_recommended: bool — distinct from plateau (conservative bias
  per ADR 0005; a sweep may be a plateau but stopping not yet
  recommended).
- reasoning: str — short free-text rationale; surfaced into the
  finish note when stop_recommended fires."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SupervisorDecision:
    """Frozen result of one supervisor consultation. See ADR 0005."""

    plateau: bool
    stop_recommended: bool
    reasoning: str
