# Solution stage — architecture documents

The second stage of forge's product-development cycle. Per [`product-development-approach.md` § 1](../../../phase-preliminary/product-development-approach.md). Goal: validate that a proposed solution actually solves the validated problem from Discovery — before committing engineering effort to building it.

## Entry criteria

- A Discovery summary exists (per [Discovery stage exit criteria](../discovery/README.md#exit-criteria)).
- A chosen problem is named with rationale in the Discovery summary.
- The Lean Canvas is updated with the validated problem (and pivots from Discovery, if any).

## Stage activities (in canonical order)

1. **Sketch solution candidates** — borrowed from Discovery's Opportunity Solution Tree leaf-nodes. Top 2-3 candidates per problem; not full specs, just enough to demo.
2. **Author per-persona [solution-interview scripts](./solution-interview-script-template.md)** — show-the-sketch + ask "does this solve your problem?" — open-ended.
3. **Run solution interviews** per [the protocol](./solution-interview-protocol.md). Multi-turn dialogue: persona reacts to sketch, identifies missing/wrong parts, surfaces concerns about adoption.
4. **Author [MVP sketches](./mvp-sketch-template.md)** for the surviving candidate(s) — minimal-viable-product spec; the smallest thing we'd build to test the hypothesis.
5. **Cross-tab solution-interview verdicts** across personas — same machinery as Discovery's CI-3.
6. **Author [solution summary](./solution-summary-template.md)** — exit artifact: chosen MVP scope + scope-out list + handoff to Build-Measure-Learn.

## Exit criteria

- A solution summary exists per [the template](./solution-summary-template.md).
- One MVP scope is named, sized, and traceable to interview evidence.
- Build-Measure-Learn stage is unblocked (Phase F experiment can be authored from the MVP sketch).

## Artifact catalog (this directory)

| Artifact | What it specifies |
|---|---|
| [README.md](./README.md) | This file. Stage overview + entry/exit + activity sequence. |
| [solution-interview-script-template.md](./solution-interview-script-template.md) | Per-persona script schema: sketch demo + adoption probes. |
| [solution-interview-protocol.md](./solution-interview-protocol.md) | How to run a solution interview: setup, demo discipline, transcript schema. |
| [mvp-sketch-template.md](./mvp-sketch-template.md) | MVP scope schema: in-scope / out-of-scope / kill criteria. |
| [solution-summary-template.md](./solution-summary-template.md) | Stage-exit artifact: chosen MVP + handoff to Build-Measure-Learn. |

## Per-product instances (NOT in this directory)

`phase-b-business-architecture/products/<product>/solution/{solution-interview-scripts/,mvp-sketches/,solution-summary.md}`. Transcripts go private per [ADR 0018 § 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: without Solution-stage architecture documents, the Wiki PM enters Solution with an undefined process — risk of jumping straight to Build (which Maurya warns is the most common failure mode).
- **Goal**: [Quality](../../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95). Validated solutions before Build = fewer post-build pivots = fewer audit findings.
- **Outcome**: 4 stage-architecture documents + this README; per-product instances follow.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: codifies stage between Discovery and Build; prevents premature engineering.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Document-solution-stage-artifacts.
- **Element**: this directory.
