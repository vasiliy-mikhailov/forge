# `src_spec_supervisor_decision`

`src.reward_bench.entities.supervisor_decision.SupervisorDecision`
is the frozen-entity return type of the supervisor (see [ADR 0005](
../../../../docs/adr/0005-plateau-detection-supervisor-via-llm-self-judgment.md)).

The supervisor watches sweep data — a sequence of dev_runner scores
over recent iterations — and decides whether the bench has plateaued
and whether the agent loop should be told to stop.

This entity is the ONLY datum that crosses the supervisor port
boundary back into `agent_loop`. By keeping it frozen we make the
hook easy to test: the hook reads three fields and acts.

Fields:

- `plateau: bool` — supervisor's classification of the recent sweep.
- `stop_recommended: bool` — distinct from `plateau` because per
  ADR 0005 conservative-bias the supervisor may classify the sweep
  as a plateau but still not recommend stopping (e.g. early in the
  run when the floor hasn't been explored yet).
- `reasoning: str` — short free-text rationale. Surfaced into the
  finish `note` when `stop_recommended` fires.

Allowed imports: `dataclasses` only. Pure entity, no IO.
