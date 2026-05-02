# Vision

This phase answers *who* cares about Forge as an architecture, *why*
they care, and *what target state* the architecture exists to reach.
The product portfolio (which products and their value streams) is not
here — that lives in Phase B.

**Vision statement.** Forge builds AI tools that save human time on
cognitive work — both consuming information and writing/optimizing
programs.


## Measurable motivation chain
Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: forge has no shared memory across architect-sessions
  without an explicit Vision artifact; without it, Phase A drift
  goes undetected.
- **Goal**: Architect-velocity (KR: ≤ 20 execution failures / 30-day).
- **Outcome**: a stable Vision the audit can grep for changes.
- **Measurement source**: audit-predicate: P14 (Vision drift = grep delta in audit walks; latest = stable)
- **Contribution**: declarative Phase A artifact; contributes to A-V KR by anchoring downstream cascade.
- **Capability realised**: Architecture knowledge management
  ([forge-level.md](../phase-b-business-architecture/capabilities/forge-level.md)).
- **Function**: Document-the-architecture-vision.
- **Element**: this file.
