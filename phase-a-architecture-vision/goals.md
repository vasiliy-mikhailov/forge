# Goals

Motivation-layer; quantified in Phase H trajectories.

- **TTS — Theoretical Time Saved.** Minutes saved per use,
  conditional on the product's quality dimensions holding.
- **PTS — Practical Time Saved.** Cumulative minutes saved across
  all users (= TTS × users × engagement).
- **EB — Economic Balance.** Revenue minus operational cost
  (GPU-hours + storage + architect-hours at shadow rate).
- **Architect-velocity.** Capability advances per architect-hour.
  Cross-cuts every other goal — speed of forge's own improvement.
- **Quality.** `pre_prod_share = pre_prod_catches / (pre_prod_catches +
  incidents)`, rolling 30-day window. Pre-prod catches = audit FAIL/WARN
  findings + test-runner failures pre-deploy. Incidents = entries in
  [`../phase-g-implementation-governance/postmortems.md`](../phase-g-implementation-governance/postmortems.md).
  Drives quality-assurance decisions (test-env-matches-prod,
  rebuild-before-launch, containers-only, completeness-over-availability,
  cheap-experiment, NFC/NFD discipline). Higher = better; trend matters
  more than absolute value. Per ADR 0021.


## Motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: every action choice must be evaluated against
  named Goals (P5); without a Goals catalog, "metric-driven
  action" has no metrics.
- **Goal**: meta — this file IS the Goals catalog.
- **Outcome**: P5 evaluable; P15 + P19 can walk Goals.
- **Measurement source**: audit-predicate: P19 (every Goal has ≥ 1 realising R-NN trajectory)
- **Capability realised**: Architecture knowledge management.
- **Function**: Catalogue-Phase-A-Goals.
- **Element**: this file (TTS, PTS, EB, Architect-velocity rows).
