# Pivot-or-persevere stage

The fifth stage of forge's product-development cycle. Per [`product-development-approach.md`](../../../phase-preliminary/product-development-approach.md). One artifact: the pivot-or-persevere decision document.

This stage is the cycle-close. Every Build-Measure-Learn loop ends with a decision: keep iterating Plan A (persevere), change Plan A in some dimension (pivot), or abandon the product (kill).

## Entry criteria

- Validation summary OR Build-Measure-Learn closure exists with measured-result data.
- Kill criteria from MVP sketch are evaluated against measured signal.

## Stage activities

1. **Author the decision document** per [the template](./pivot-decision-template.md) — enumerate the three options, choose explicitly, cite evidence.
2. **If Pivot**: author ADR landing the pivot (or amend existing product-strategy ADR).
3. **If Kill**: author postmortems entry; delete product-line files per delete-on-promotion.
4. **Update the Lean Canvas** to reflect the post-decision state.

## Exit criteria

- Decision document exists with explicit Persevere / Pivot / Kill chosen.
- ADR landed (Pivot or Kill).
- Lean Canvas updated.
- Next cycle's entry criteria are clear.

## Artifact catalog (this directory)

| Artifact | What it specifies |
|---|---|
| [README.md](./README.md) | This file. |
| [pivot-decision-template.md](./pivot-decision-template.md) | The decision schema: closure data + three options + chosen + Lean Canvas updates + handoff. |

## Per-product instances

`phase-b-business-architecture/products/<product>/pivot-or-persevere/<YYYY-MM-DD>-decision.md` — one per cycle close.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: cycle-close decisions drift into "persevere by default" without pre-committed discipline.
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling).
- **Outcome**: stage architecture documents in this directory.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: pivot/persevere/kill discipline enforced via template.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md) + [Architecture knowledge management](../../capabilities/forge-level.md).
- **Function**: Document-pivot-or-persevere-stage.
- **Element**: this directory.
