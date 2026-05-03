# Discovery stage — architecture documents

This directory contains the **canonical artifact schemas** for the Discovery stage of forge's [product-development approach](../../../phase-preliminary/product-development-approach.md). Per-product instances of these artifacts live under `phase-b-business-architecture/products/<product>/discovery/`; interview transcripts (containing customer-derived assessments per [ADR 0018 § 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md)) live in the private repo.

## What the Discovery stage is

The first stage of forge's product-development cycle, per [ADR 0027](../../../phase-preliminary/adr/0027-product-development-approach.md). Goal: validate that the customer has the pain we think they have, before committing engineering effort to a solution.

## Entry criteria

- A product line exists in [`../../products/`](../../products/).
- Personas exist for the target customer segment in [`../../roles/customers/`](../../roles/customers/) (Job-to-be-Done framed per [JTBD § 3 of the approach](../../../phase-preliminary/product-development-approach.md)).
- A Plan A is articulable (i.e. team has explicit beliefs about Problem / Solution / Customer Segments worth validating).

## Stage activities (in canonical order)

1. **Author Plan A** as a [Lean Canvas](./lean-canvas-template.md) — Problem / Solution / Key Metrics / UVP / Channels / Customer Segments / Cost / Revenue / Unfair Advantage. Some cells deferred until commercialisation per § 7 (stealth-mode caveat).
2. **Identify riskiest assumptions** — typically Problem cell + Customer Segments fit. Order by "if wrong, how much do we lose?" descending.
3. **Author per-persona [problem-interview scripts](./problem-interview-script-template.md)** — open-ended questions per persona's Job statement.
4. **Run problem interviews** per [the protocol](./problem-interview-protocol.md) — multi-turn dialogue between PM and persona-agent (or real customer when not in stealth). Save transcripts to private repo.
5. **Cross-tab observations** across personas — same machinery as [Customer-Interview cycle CI-3](../../../phase-requirements-management/wiki-customer-interview.md).
6. **Prioritize problems** via [Opportunity Solution Tree](../../../phase-preliminary/product-development-approach.md#4-complement--torres-opportunity-solution-trees) — outcome at root → opportunities → solution candidates. Pick 1-of-N to take into Solution stage.
7. **Author [discovery summary](./discovery-summary-template.md)** — exit artifact: validated-problems list, chosen-problem rationale, hand-off to Solution stage.

## Exit criteria

- A discovery-summary artifact exists per the template at [`./discovery-summary-template.md`](./discovery-summary-template.md).
- The chosen problem is named, rationalised, and traceable to per-persona interview evidence.
- Solution stage is unblocked (ready for Solution-interview architecture documents — queued to author when forge enters Solution stage).

## Artifact catalog (this directory)

| Artifact | What it specifies |
|---|---|
| [README.md](./README.md) | This file. Stage overview + entry/exit + activity sequence. |
| [lean-canvas-template.md](./lean-canvas-template.md) | One-page strategic summary schema (9 cells) per product. |
| [problem-interview-script-template.md](./problem-interview-script-template.md) | Per-persona interview-question schema. Open-ended, JTBD-anchored, Forces-of-Progress-checking. |
| [problem-interview-protocol.md](./problem-interview-protocol.md) | How to run an interview: setup, multi-turn dialogue rules, listening discipline, transcript schema. |
| [discovery-summary-template.md](./discovery-summary-template.md) | Stage-exit artifact schema: validated problems + chosen problem + rationale + hand-off. |

## Per-product instances (NOT in this directory)

Per-product Discovery artifacts live at:
- `phase-b-business-architecture/products/<product>/discovery/lean-canvas.md`
- `phase-b-business-architecture/products/<product>/discovery/problem-interview-scripts/<persona>.md`
- `phase-b-business-architecture/products/<product>/discovery/opportunity-solution-tree.md`
- `phase-b-business-architecture/products/<product>/discovery/discovery-summary.md`

Interview transcripts (private per [ADR 0018 § 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md)):
- `kurpatov-wiki-wiki/metadata/discovery/interview-transcripts/<persona>/<date>.md`

## Relationship to the Customer-Interview cycle ([ADR 0016](../../../phase-preliminary/adr/0016-wiki-customers-as-roles.md))

The Customer-Interview cycle (CI-1..7) is one tool used during Discovery — specifically, the simulated-reading walk that produces breadth-of-coverage pain ledgers. It does NOT replace Problem interviews. Discovery uses BOTH:
- **Customer-walk (existing)** for breadth — every persona reads every lecture; simulated; produces 220 ledgers.
- **Problem interview (NEW)** for depth — PM probes specific hypotheses through multi-turn dialogue with persona-agents; produces 5-15 transcripts per cycle.

Future amendment to ADR 0016 will rename CI-1..7 to "Customer-walk cycle" and explicitly position it inside the Discovery stage of this approach.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: Discovery stage's first artifact attempt (Customer-Interview cycle per ADR 0016) was incomplete — it captured breadth-coverage but skipped Problem interviews + formal prioritization. Stage-architecture documents codify the missing pieces so future cycles are complete.
- **Goal**: [Quality](../../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95). Better-disciplined Discovery = fewer wrong-direction experiments = fewer post-hoc audit findings = higher pre_prod_share.
- **Outcome**: 5 Discovery-stage architecture documents land here. Per-product instances will follow per the template-once / instance-many pattern.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: codifies the Discovery stage so the Wiki PM (and any future product owner) reaches Discovery with templates instead of re-inventing schemas; reduces audit FAIL rate on product-development methodology drift.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Document-discovery-stage-artifacts.
- **Element**: this directory + 4 template files.
