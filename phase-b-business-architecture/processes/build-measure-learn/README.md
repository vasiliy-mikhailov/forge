# Build-Measure-Learn stage — architecture documents

The third stage of forge's product-development cycle. Per [`product-development-approach.md`](../../../phase-preliminary/product-development-approach.md). Build the MVP, ship it, measure the riskiest-assumption signal, learn what to do next.

Forge already has a Build-Measure-Learn implementation that pre-dates this document: **Phase F experiments**. Each Phase F experiment IS one Build-Measure-Learn loop.

## Entry criteria

- A Solution summary exists with a chosen MVP sketch.
- MVP sketch has explicit in/out-of-scope, kill criteria, riskiest assumptions, build cost estimate.

## Stage activities (in canonical order)

1. **Author Phase F experiment file** at `phase-f-migration-planning/experiments/<id>.md`. The MVP sketch becomes the experiment's Spec section. Use the existing experiment format (K1, K2, G1, G2, G3 are precedents).
2. **Build the MVP** — Developer + DevOps team activates per [Kurpatov-wiki team collaboration](../../roles/collaborations/kurpatov-wiki-team.md). Build measured against MVP sketch's in-scope list (out-of-scope items may NOT slip in mid-build without ADR amendment).
3. **Measure the riskiest assumption** — per the kill criteria pre-committed in the MVP sketch. Falsifier-first per [P5](../../../phase-preliminary/architecture-principles.md): cheap measurement before expensive build (the K2-L2 probe-then-stop is the canonical example).
4. **Capture learnings** in the experiment's Closure section: what was built, what was measured, what the result was, what we learned.
5. **Hand off to Validation stage** if MVP shipped to real users, OR to **Pivot-or-persevere** if MVP failed kill-criteria.

## Exit criteria

- Phase F experiment Closure section is populated with measured-result data.
- Kill-criteria evaluated against measured signal — explicit pivot/persevere/kill verdict.
- Validation or Pivot-or-persevere stage is unblocked.

## Cross-link to existing experiment template

Phase F experiment files follow a stable format. Examples:
- [K1 — modules 000+001 source.md publication](../../../phase-f-migration-planning/experiments/K1-modules-000-001.md)
- [K2 — compact-restore](../../../phase-f-migration-planning/experiments/K2-compact-restore.md)
- [G1 — Blackwell stability](../../../phase-f-migration-planning/experiments/G1-blackwell-stability.md)
- [G2 — MoE faster inference](../../../phase-f-migration-planning/experiments/G2-MoE-faster-inference.md)
- [G3 — Gemma 4-31B](../../../phase-f-migration-planning/experiments/G3-gemma-4-31b.md)

Format: Spec / Build / Measurement / Closure / Pivot-trace.

A formal `experiment-template.md` derived from these examples is queued (not authored in this commit since the existing experiments serve as canonical precedents).

## Falsifier-first discipline

Per [P5](../../../phase-preliminary/architecture-principles.md) and the K2-L2 probe-then-stop precedent:

> Before committing to expensive build, measure the cheapest signal that could refute the riskiest assumption. If the signal is too weak to justify build, STOP and pivot.

This rule belongs to Build-Measure-Learn but is enforced from the MVP-sketch (which pre-commits the kill criteria). Falsifier-first = MVP-sketch's kill criteria + cheap-measurement-first sequencing inside the experiment.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: forge has Build-Measure-Learn implementation (Phase F experiments) but no architecture document positioning it inside the product-development cycle. Cross-cycle integration was implicit.
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Explicit stage placement removes the "where do experiments fit?" recurring question.
- **Outcome**: this README positions Phase F experiments as the Build-Measure-Learn implementation; cross-references existing experiments as precedents.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: integrates pre-existing experiment discipline into the documented product-development cycle without re-inventing the experiment format.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md) + [R&D capability](../../capabilities/forge-level.md).
- **Function**: Document-build-measure-learn-stage.
- **Element**: this directory.
