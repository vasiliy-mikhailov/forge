# ADR 0027 — Adopt Lean Startup as product-development base; complement with Wardley Maps / JTBD / Opportunity Solution Trees

## Status

Accepted (2026-05-02). Active.

## Measurable motivation chain

Per [P7](../architecture-principles.md):

- **Driver**: Customer-Interview cycle (per [ADR 0016](0016-wiki-customers-as-roles.md)) shipped 220 simulated-reading pain ledgers + 34 cross-tabbed observations + 10 named problems, but is missing four product-development discipline pieces a real cycle needs: (1) PM hypothesis explicit, (2) interview script per persona, (3) interview protocol, (4) statistical analysis to pick 1-of-N. Current cycle is mis-named "interview" — it's actually a **simulated-reading walk**. Architect call: "approach should be described in architecture" — codify the methodology before applying it.
- **Goal**: [Architect-velocity](../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). A documented approach prevents re-litigating method choice each cycle; the Wiki PM and team know which tool to reach for without per-decision architect intervention.
- **Outcome**: forge documents the product-development approach in [`phase-preliminary/product-development-approach.md`](../product-development-approach.md) — Maurya's *Running Lean* as the iterative base, complemented by three specific tools for forge's specific gaps. Discovery-stage architecture documents in [`phase-b-business-architecture/processes/discovery/`](../../phase-b-business-architecture/processes/discovery/) operationalise the first stage.
- **Measurement source**: audit-predicate: P7 (universal motivation traceability — meta-method is itself measurable) + audit-predicate: P26 (every chain in scope cites a measurement source).
- **Contribution**: this ADR + the approach doc + 5 discovery-stage artifact templates land as a coherent meta-method addition; future cycles cite the approach instead of re-inventing it; reduces architect-velocity execution-failure count by removing per-cycle methodology arguments.
- **Capability realised**: [Architecture knowledge management](../../phase-b-business-architecture/capabilities/forge-level.md).
- **Function**: Adopt-and-document-product-development-approach.

## Context

Forge today has a strong **architecture-documentation discipline** (TOGAF + ArchiMate + RLVR + delete-on-promotion + OKR cascade + audit cycle). What it lacks until this ADR is an explicit **product-development discipline**.

The customer-interview cycle (ADR 0016) is honest about what it does but uses misleading terminology. The cycle is in fact a **simulated-reading walk + PM-solo synthesis** — useful for breadth coverage in stealth-mode iteration, but it is not customer-development in Steve Blank's or Ash Maurya's sense (no actual back-and-forth between PM and customer; no hypothesis-validation interviews; no formal problem prioritization).

The architect has been operating per Maurya's *Running Lean* "Plan A → Plan that works" frame intuitively but without architectural documentation. This ADR makes the choice explicit and adds three specific complements that fill known gaps in Maurya's coverage for forge's context.

## Decision

### 1. Adopt Maurya's *Running Lean* as the product-development base

**What forge takes from Maurya:**
- "Plan A → Plan that works" iterative discipline (matches K1 / K2 / K3 experiment trajectory).
- Three-stage interview model: Problem interview → Solution interview → Validation interview.
- Lean Canvas as the one-page strategic artifact per product (matches Architect-velocity ≤ 20-interventions-per-30-day discipline).
- Pivot framework — explicit pivot-or-persevere criteria after each Build-Measure-Learn loop. Compatible with delete-on-promotion (a pivot is explicit deletion of a Plan A assumption).
- Falsifier-first / cheap-experiment-first (matches forge's [P5](../architecture-principles.md)).

**What forge does NOT take from Maurya:**
- Lean Canvas's "Channels", "Revenue Streams", "Cost Structure", "Unfair Advantage" cells are weak when the product is in stealth mode and customers are simulated. These cells stay in the Lean Canvas template but are explicitly marked **deferred until commercialisation** for the kurpatov-wiki and tarasov-wiki product lines today.

### 2. Complement with Wardley Maps for architecture / strategy decisions

When the decision is about technology stack, component build-vs-buy, or evolution-stage, Maurya is silent and Wardley is rigorous. Use Wardley Maps for:
- ETL stack choices (Whisper-VAD vs alternatives, etc.).
- Compact-restore architecture (K2 / K3).
- Vector-retrieval / inference subsystem decisions.
- Any "is this utility or custom-build?" call.

Authoritative source: [`https://learnwardleymapping.com/`](https://learnwardleymapping.com/) and Simon Wardley's *Wardley Maps* book.

### 3. Complement with Jobs-to-be-Done for persona depth

Personas tell *who*; JTBD tells *what they hire the wiki to do*. Use JTBD for:
- Persona authoring + revision (richer than persona-as-archetype).
- Pain-ledger framing (every pain becomes "this defeats the job").
- Forces of Progress check (Push, Pull, Anxieties, Habits) when assessing whether a customer would actually adopt.

Authoritative source: Christensen, *Competing Against Luck* (2016); Klement, *When Coffee and Kale Compete*; Bob Moesta interview series.

### 4. Complement with Teresa Torres' Opportunity Solution Trees

Maurya prioritization is implicit; OST is explicit and visual. Use OST for:
- Picking 1-of-N opportunities for the next iteration (current state: 10 problems, no formal pick).
- Mapping opportunities to outcomes (top-level Goal at root).
- Surfacing solution candidates per opportunity for systematic exploration.

Authoritative source: Torres, *Continuous Discovery Habits* (2021); [`producttalk.org`](https://www.producttalk.org/opportunity-solution-tree/).

### 5. Keep TOGAF + ArchiMate + RLVR + OKR as the architecture-documentation layer

Maurya covers product discovery; it does NOT replace architecture documentation. Forge keeps:
- ADRs (architecture decisions).
- ArchiMate-typed artifacts per phase.
- Audit cycle (P1..P30) for enforcement.
- OKR cascade (ADR 0023).

Two layers, complementary — discovery / product on top, architecture / documentation underneath.

### 6. Stealth-mode caveat documented

Forge today operates with simulated personas, not real customers. Maurya is unambiguous: real validation requires real customers. Plan-A iteration in stealth is fine for direction-finding; product-market-fit claims require real users. Recorded in [`product-development-approach.md`](../product-development-approach.md) § 7 and queued as an amendment to [`phase-a-architecture-vision/vision.md`](../../phase-a-architecture-vision/vision.md).

### 7. ADR 0016's customer-interview cycle relationship

ADR 0016's cycle stays as-written. It implements one specific moment (the simulated-reading walk and ledger synthesis). It is not the entire product-development approach — it is one tool within Discovery. The relationship is documented in the new approach file's § 6.

## Consequences

- **Plus**: methodology choice is explicit, ADR-traceable, single-source-of-truth.
- **Plus**: discovery-stage architecture documents (templates + protocols) operationalise the approach without re-inventing per cycle.
- **Plus**: future ADRs about product strategy can cite the approach by name + section.
- **Plus**: when a tool is missing from forge's toolbox, the gap is explicit (e.g. "no Validation-stage protocol yet" — visible from approach file).
- **Minus**: documentation cost — ~6 new artifacts in this commit. Mitigated by template-once / instance-many pattern.
- **Minus**: methodology drift — if the team uses tools outside the documented approach without ADR amendment, the approach becomes de-facto false. Mitigated by predicate (queued: P31 — "every product-discovery decision artifact cites a tool from `product-development-approach.md`").

## Invariants

- Future product-development methodology additions land as ADR amendments to this ADR or new ADRs that explicitly cite this one.
- Discovery-stage artifact templates in [`phase-b-business-architecture/processes/discovery/`](../../phase-b-business-architecture/processes/discovery/) are the canonical schemas; per-product instances live in `phase-b-business-architecture/products/<product>/discovery/` (private path for transcripts per [ADR 0018 § 7](0018-privacy-boundary-public-vs-private-repos.md)).
- The Lean Canvas template is the canonical product strategic-summary format; per-product Lean Canvas lives in `phase-b-business-architecture/products/<product>/lean-canvas.md`.

## Alternatives considered

- **Cagan's *Inspired* / *Empowered* product-trio model.** Rejected: assumes an established product team (PM + designer + engineer) with empowered organisation. Forge is solo-architect-of-record per [P1](../architecture-principles.md).
- **Pure Steve Blank Customer Development (4-step model: Discovery → Validation → Creation → Building).** Considered. Rejected as base because Maurya is Blank's distillation with the Lean Canvas one-page artifact added; equivalent rigor with better tooling. Cite Blank as Maurya's progenitor.
- **Design Sprint (Knapp / Google Ventures).** Rejected as base: time-boxed (5-day) sprint is tactical, not strategic. Could be adopted as a Validation-stage tool later if useful.
- **OKR-only discovery (Doerr / Wodtke).** Rejected as base: OKRs frame outcomes but don't specify how to discover problems. Already adopted at the goal-cascade layer (ADR 0023); insufficient as a discovery method.

## Follow-ups

- Author the four discovery-stage artifact templates in this commit.
- Author the Solution-stage and Validation-stage architecture documents in a future ADR amendment when forge enters those stages.
- Predicate P31 (queued) — every product-discovery decision artifact cites a tool from `product-development-approach.md`.
- Apply the approach to the 10 outstanding problems (the worked example) — separate commit after architect review.
