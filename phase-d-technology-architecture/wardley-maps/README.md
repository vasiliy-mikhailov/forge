# Wardley Maps — architecture decisions

Per [`product-development-approach.md` § 2](../../phase-preliminary/product-development-approach.md): forge uses Wardley Mapping for technology / build-vs-buy / component-evolution decisions. Maps live in this directory; one map per architecture decision.

## When to use Wardley Mapping

Use Wardley Maps for decisions where Maurya's framework is silent and the decision involves:
- Technology stack choice (e.g. transcription engine, vector DB, inference framework).
- Build-vs-buy / utility-vs-custom calls.
- Component evolution stage (Genesis / Custom-built / Product / Commodity).
- Strategic positioning of forge components vs the broader ecosystem.

NOT use Wardley Maps for:
- Customer-pain validation (use Discovery-stage interviews).
- Solution validation (use Solution-stage interviews).
- Goal-tracking (use OKR cascade).

## Map schema

Each map is a markdown file with:

```markdown
# Wardley Map — <decision name> — <YYYY-MM-DD>

- **Decision under test**: <one sentence>
- **Triggering event**: <what made us need this map>
- **Author**: <Wiki PM / Architect / Developer>

## User need (top of map)

The user-visible need this map serves. Cross-link to persona [Job statement](../../phase-b-business-architecture/roles/customers/) when applicable.

## Component anchors

Top-down list of components from user-visible to invisible:
- <Component A> — <evolution stage: Genesis / Custom / Product / Commodity>
- <Component B> — <evolution stage>
- ...

## Map (textual or image)

Either a textual rendering (component layered top-to-bottom, with evolution-stage column) OR a link to an image artifact at `./<decision>.png` if available.

## Strategic moves identified

What the map suggests:
- <move 1> — <rationale>
- <move 2> — <rationale>

## Decision

The chosen move with rationale citing the map.

## Cross-link

- Triggering ADR: <link if applicable>
- Phase F experiment closure feeding the decision: <link if applicable>
- Updates to MVP sketch / Lean Canvas: <links if applicable>

## Measurable motivation chain (per-instance pattern)
```

## Authoring rules

- One map per decision. Minor decisions don't warrant a map; reserve for decisions with cost-of-being-wrong > 1 architect-week of rework.
- Maps are dated. Old maps deleted per delete-on-promotion when the decision lands; the chosen-move-rationale is preserved as ADR.
- Maps are inputs to ADRs, not substitutes. The ADR is the durable artifact of record.

## Authoritative sources

- Simon Wardley's [`learnwardleymapping.com`](https://learnwardleymapping.com/).
- Wardley's *Wardley Maps* book (free online: [`https://medium.com/wardleymaps`](https://medium.com/wardleymaps)).

## Status

This directory exists as a **placeholder for future Wardley Maps**. No maps authored yet. First map will land when forge faces a technology decision big enough to warrant the discipline (queued candidates: K3 compress-by-redundancy architecture; transcription pipeline replacement post-Whisper-VAD-degeneration findings).

## Measurable motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: forge has technology decisions ahead (K3 compression, ETL hardening, validation-stage telemetry) where Wardley Mapping is more rigorous than ad-hoc reasoning.
- **Goal**: [Architect-velocity](../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Mapped decisions = clearer trade-offs = fewer architect interventions per decision.
- **Outcome**: this directory exists with a documented schema; future maps land here.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: complements Maurya's product-discovery framework with rigorous architecture-decision tooling per [approach § 2](../../phase-preliminary/product-development-approach.md).
- **Capability realised**: [Architecture knowledge management](../../phase-b-business-architecture/capabilities/forge-level.md).
- **Function**: Document-Wardley-Map-discipline.
- **Element**: this directory.
