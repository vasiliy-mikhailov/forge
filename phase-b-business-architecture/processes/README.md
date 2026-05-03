# Forge product-development processes

Per [`product-development-approach.md`](../../phase-preliminary/product-development-approach.md): the five stages of forge's product-development cycle. Each stage has its own directory of architecture documents (templates + protocols + READMEs).

| Stage | Purpose | Directory | Status |
|---|---|---|---|
| 1. Discovery | Validate that the customer has the pain we think | [`./discovery/`](./discovery/) | ✓ documented |
| 2. Solution | Validate that proposed solution solves validated problem | [`./solution/`](./solution/) | ✓ documented |
| 3. Build-Measure-Learn | Build minimal product; measure; learn | [`./build-measure-learn/`](./build-measure-learn/) | ✓ documented (cross-references existing Phase F experiments) |
| 4. Validation | Validate built product with real customers; willingness-to-pay; renewal | [`./validation/`](./validation/) | ✓ documented |
| 5. Pivot-or-persevere | Decide whether to keep iterating, change direction, or kill | [`./pivot-or-persevere/`](./pivot-or-persevere/) | ✓ documented |

The order is canonical for one product cycle: 1 → 2 → 3 → 4 → 5 (and back to 1, or 2, or kill — per stage-5 decision). Each stage's README specifies entry/exit criteria explicitly.

## Cross-cutting artifacts (used in multiple stages)

- [Lean Canvas](./discovery/lean-canvas-template.md) — authored in Discovery, revised after each pivot.
- [Persona files](../roles/customers/) — Discovery and Solution interviews target these.
- [Wardley Maps](../../phase-d-technology-architecture/wardley-maps/) — used during Solution and Build for architecture decisions.
- [Phase F experiments](../../phase-f-migration-planning/experiments/) — Build-Measure-Learn manifests as one experiment per learn-cycle.

## Per-product instances

This directory holds **architecture documents** (templates + protocols). Per-product instances live at `phase-b-business-architecture/products/<product>/<stage>/...`. Customer-derived assessment content (interview transcripts, validated-problem details) lives in the private `kurpatov-wiki-wiki/metadata/` per [ADR 0018 § 7](../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

## Measurable motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: forge's product-development discipline was implicit before [ADR 0027](../../phase-preliminary/adr/0027-product-development-approach.md). Without per-stage architecture documents, each product cycle re-invents the schemas.
- **Goal**: [Architect-velocity](../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Template-once / instance-many removes per-cycle methodology arguments.
- **Outcome**: 5 stage directories + cross-cutting artifacts; future product cycles cite stage READMEs and templates by section.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: this index is the entry point to forge's product-development discipline; the WHY lives in `phase-preliminary/`, the HOW per stage lives here.
- **Capability realised**: [Develop wiki product line](../capabilities/develop-wiki-product-line.md).
- **Function**: Index-product-development-stages.
- **Element**: this directory.
