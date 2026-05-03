# Validation stage — architecture documents

The fourth stage of forge's product-development cycle. Per [`product-development-approach.md`](../../../phase-preliminary/product-development-approach.md). Goal: validate that the BUILT product (not a sketch) actually delivers value to real customers; willingness-to-pay; renewal intent.

## Stealth-mode caveat (load-bearing)

Forge today operates in stealth mode with simulated personas. **Validation in the Maurya sense requires real customers** — willingness-to-pay is a behaviour, not an aspiration; renewal is a fact, not a forecast. Until forge has a real-user cohort, the Validation stage is mostly aspirational.

What forge CAN do in stealth:
- Validation-quality assessment via [Wiki PM](../../roles/wiki-pm.md) walking the built product against the MVP-sketch in-scope list — did we build what we promised?
- Cross-persona simulated re-walk to detect quality regressions vs the Discovery / Solution baseline.

What forge CANNOT do in stealth:
- Real willingness-to-pay measurement.
- Real renewal-intent measurement.
- Product-market-fit declaration.

This stage's templates are authored to be ready for the day forge has real users; in stealth they're partial.

## Entry criteria

- Build-Measure-Learn closure verdict is "ship to validation" (not "kill" or "pivot").
- The built MVP is reachable by the target persona (real-customer access OR simulated-persona walk).

## Stage activities (in canonical order)

1. **Author per-persona [validation-interview scripts](./validation-interview-script-template.md)** — usage-pattern probes + willingness-to-pay (when real customers; deferred in stealth).
2. **Run validation interviews** per [the protocol](./validation-interview-protocol.md) — multi-turn dialogue post-usage.
3. **Cross-tab usage signals** — what feature actually got used; what got ignored.
4. **Author [validation summary](./validation-summary-template.md)** — exit artifact: validated-feature-set + retention-signal + product-market-fit verdict (or stealth-mode equivalent).

## Exit criteria

- Validation summary exists per [the template](./validation-summary-template.md).
- Either: real customers showed retention + willingness-to-pay (=> ship at scale), OR: pivot decision based on usage data, OR: kill.
- Pivot-or-persevere stage is unblocked.

## Artifact catalog (this directory)

| Artifact | What it specifies |
|---|---|
| [README.md](./README.md) | This file. |
| [validation-interview-script-template.md](./validation-interview-script-template.md) | Per-persona script schema: usage probes + payment-intent + retention. |
| [validation-interview-protocol.md](./validation-interview-protocol.md) | Multi-turn dialogue; usage-data triangulation; transcript schema. |
| [validation-summary-template.md](./validation-summary-template.md) | Stage-exit artifact: validated-feature-set + retention + PMF verdict. |

## Per-product instances

`phase-b-business-architecture/products/<product>/validation/{validation-interview-scripts/, validation-summary.md}`. Transcripts go private per [ADR 0018 § 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: forge needs a Validation-stage architecture spec ready for the day real users exist; without it, the team scrambles when commercialisation arrives.
- **Goal**: [PTS](../../../phase-a-architecture-vision/goals.md) (KR: pts_share ≥ 0.30 rolling 30-day) — validation feeds practical-time-saved measurement.
- **Outcome**: 4 Validation-stage architecture documents land; per-product instances follow when ready.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: prepares forge for post-stealth product-market-fit measurement.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Document-validation-stage-artifacts.
- **Element**: this directory.
