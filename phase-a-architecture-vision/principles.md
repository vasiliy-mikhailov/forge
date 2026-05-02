# Principles (Phase A scope)

The forge-wide architecture principles — single architect of
record, capability trajectories (Level 1 / Level 2 with
delete-on-promotion), containers-only execution, single-server
deployment — are **meta-principles**, not Phase-A-scoped. They sit
in the Preliminary Phase because they constrain every phase
equally.

See [`../phase-preliminary/architecture-principles.md`](../phase-preliminary/architecture-principles.md)
for the canonical list and the rationale for each.

This file exists for completeness — Phase A in TOGAF can carry
*iteration-scoped* principles (principles specific to the current
ADM iteration's vision). Forge's vision has been stable since
2026-04-25 and no Phase-A-scoped principles apply today. If the
Architecture Vision is re-opened (new product, new domain), this
is where iteration-specific principles would land.


## Measurable motivation chain
Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: Phase A allows iteration-scoped principles; this
  file holds them (or notes their absence).
- **Goal**: Architect-velocity (KR: ≤ 20 execution failures / 30-day).
- **Outcome**: P14 walks (transitive — covered by parent
  meta-principle file).
- **Measurement source**: n/a — declarative: iteration-scoped principles registry (today empty; populated by ADR-emitting predicates as P-NN principles land)
- **Contribution**: declarative Phase A artifact; contributes to A-V KR by anchoring downstream cascade.
- **Capability realised**: Architecture knowledge management.
- **Function**: Hold-Phase-A-iteration-principles.
- **Element**: this file (today empty — Vision stable since
  2026-04-25 per the file's own note).
