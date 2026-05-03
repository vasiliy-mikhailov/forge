# Lean Canvas — template

The one-page strategic summary per product, per [`product-development-approach.md` § 1](../../../phase-preliminary/product-development-approach.md). Per-product instances live at `phase-b-business-architecture/products/<product>/lean-canvas.md`.

Per Maurya's *Running Lean* (3rd ed., 2022) — Lean Canvas is Maurya's adaptation of Osterwalder's Business Model Canvas optimised for early-stage product discovery.

## Schema — 9 cells

Authored as 9 markdown sections in this order. Each cell is 1-3 bullet points; total artifact ≤ one printed page (~400 words).

### 1. Customer Segments

WHO is this for? Identify segments by their [Job to be Done](../../../phase-preliminary/product-development-approach.md#3-complement--jobs-to-be-done-for-persona-depth) — not by demographic. Cross-reference forge persona files in [`../../roles/customers/`](../../roles/customers/).

Format:
```
- <segment-name>: <Job statement> — When I [situation], I want to [motivation], so I can [outcome].
- (next segment)
```

Mark **early-adopter segment** explicitly — the segment most desperate for the solution; first interviews target this segment.

### 2. Problem

Top 3 problems the segment faces, ranked by pain magnitude. Each problem in customer's words (not solution language).

Format:
```
- (P1) <problem statement>
- (P2) <problem statement>
- (P3) <problem statement>

**Existing alternatives** the segment uses today:
- <alternative 1>
- <alternative 2>
- <alternative 3>
```

### 3. Unique Value Proposition (UVP)

A single declarative sentence explaining why this product is worth attention. Format borrowed from Maurya: *"\[Single result customer wants\] without \[their existing pain point\]."*

Optional: a **high-concept pitch** (one phrase). Borrowed-from-X-meets-Y is the canonical form.

### 4. Solution

Top 3 features that address the top 3 problems. Each feature → one problem. Don't elaborate; this is a pitch, not a spec.

### 5. Channels

How the product reaches the segment. **Cell deferred until commercialisation** for stealth-mode products (per [approach § 7 stealth-mode caveat](../../../phase-preliminary/product-development-approach.md#7-stealth-mode-caveat)).

### 6. Revenue Streams

How the product makes money. **Cell deferred until commercialisation** for stealth-mode products.

### 7. Cost Structure

Major cost drivers (compute, storage, content acquisition, architect-time at shadow rate, etc.). Sufficient to compute unit economics. Required for [EB Goal](../../../phase-a-architecture-vision/goals.md) (KR: unit_economics ≥ 1.0).

### 8. Key Metrics

The 1-3 numbers that tell us the product is working. Cross-reference forge's OKR cascade ([ADR 0023](../../../phase-preliminary/adr/0023-okr-cascade-numerical-targets.md)) — Key Metrics here should map to one of the 5 named Goals (TTS / PTS / EB / Architect-velocity / Quality).

### 9. Unfair Advantage

What we have that competitors can't easily copy. Honest if "none yet" — that's information for prioritisation. Maurya: "The only true unfair advantage is something you have but cannot be copied or bought."

## Authoring rules

- One canvas per product line. Major pivots get a new canvas with a date suffix; old canvas deleted per delete-on-promotion. Pivot rationale captured as ADR.
- Cell order matters: 1 → 2 → 3 → 4 (problem-first) before 5 → 6 → 7 (business-model side). Maurya's discipline: don't author Solution before Problem; don't author Channels before validated Customer Segments.
- Total length ≤ 400 words. If a cell needs more, that's a sign the canvas is hiding strategy weakness — split the product or sharpen the segment.
- Stealth-mode cells (5, 6, partially 9) are explicitly marked `**deferred — stealth mode**` instead of fabricated.

## Cross-link to forge artifacts

- Customer Segments cell → [`../../roles/customers/`](../../roles/customers/) persona files.
- Problem cell → [customer-problems.md](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/blob/main/metadata/customer-problems.md) when problems have been validated by interview / customer-walk.
- Solution cell → R-NN trajectory rows in [`catalog.md`](../../../phase-requirements-management/catalog.md).
- Key Metrics cell → [`phase-a/goals.md`](../../../phase-a-architecture-vision/goals.md) named Goal.
- Cost Structure → eb-report.py (queued per ADR 0023 follow-up #1).

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: per [`product-development-approach.md` § 1](../../../phase-preliminary/product-development-approach.md), Lean Canvas is the canonical strategic-summary artifact for each product. Without a template, each product line invents its own canvas schema; cross-product comparison breaks.
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Template-once / instance-many removes per-product canvas schema arguments.
- **Outcome**: this template is the canonical Lean Canvas schema for forge; per-product instances cite it; cross-product comparison reads cell-by-cell against the same schema.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: prevents schema drift across product canvases; one template, N instances.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Schema-Lean-Canvas.
- **Element**: this template file.
