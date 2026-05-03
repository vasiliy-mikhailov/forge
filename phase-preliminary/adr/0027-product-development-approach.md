# ADR 0027 — Customer-development discipline added on top of TOGAF/ArchiMate; nothing else

## Status

Accepted (2026-05-02). Active. Amended 2026-05-02 per architect call to simplify scope.

## Measurable motivation chain

Per [P7](../architecture-principles.md):

- **Driver**: forge's existing TOGAF + ArchiMate + RLVR + delete-on-promotion + OKR cascade discipline covers most of what a product team needs. The one piece that was genuinely missing: a **customer-interview discipline** to find real customer problems (forge had only the simulated-reading walk per [ADR 0016](0016-wiki-customers-as-roles.md), no actual interviews).
- **Goal**: [Architect-velocity](../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). The simplest possible customer-discovery addition that fits forge's existing discipline.
- **Outcome**: 2 new artifacts in `phase-requirements-management/` (customer-interview script template + protocol), JTBD Job statements added to existing persona files, customer-walk cycle file renamed for honesty. Nothing else added; no parallel methodology framework imported.
- **Measurement source**: audit-predicate: P26.
- **Contribution**: closes the customer-development gap surfaced by the audit cycle without importing Lean Canvas / MVP sketch / pivot-decision / Wardley-Maps scaffolding (all of which duplicate TOGAF/ArchiMate territory forge already covers).
- **Capability realised**: [Architecture knowledge management](../../phase-b-business-architecture/capabilities/forge-level.md) (single-source-of-truth for forge's discipline).
- **Function**: Add-customer-interview-discipline.

## Context

Original draft of this ADR (2026-05-02 morning) proposed adopting Maurya's *Running Lean* as a full product-development methodology base — Lean Canvas, MVP sketches, pivot-or-persevere templates, Wardley Maps for architecture decisions, Opportunity Solution Trees for prioritization. Auditor + Architect self-review identified the proposal as **massively over-engineered**:

- Lean Canvas duplicates Phase A goals + Phase B Capability + Phase B Product (cells we already have).
- MVP sketches duplicate Phase F experiment specs (the experiments ARE MVPs).
- Pivot-or-persevere templates duplicate the existing ADR-amendment + delete-on-promotion pattern.
- Solution / Validation / Build-Measure-Learn stages add vocabulary on top of TOGAF/ArchiMate without adding capability.
- Wardley Maps placeholder created without an actual decision needing one.

Architect call (2026-05-02): *"Yes, jobs to be done are good and you can incorporate it into personas. Yes, lean canvas is good — but do we really need one having togaf? I doubt it. Let's clean up a bit from unnecessary."*

This amended ADR records the simplification.

## Decision

### 1. Customer-interview discipline added (the one genuine gap)

Two new artifacts in [`../../phase-requirements-management/`](../../phase-requirements-management/):
- [`customer-interview-script-template.md`](../../phase-requirements-management/customer-interview-script-template.md) — per-persona schema for customer-interview questions (open-ended, JTBD-anchored, Forces-of-Progress probing).
- [`customer-interview-protocol.md`](../../phase-requirements-management/customer-interview-protocol.md) — multi-turn dialogue rules + transcript schema.

These complement (not replace) the existing customer-walk cycle in [`../../phase-requirements-management/wiki-customer-walk.md`](../../phase-requirements-management/wiki-customer-walk.md) (renamed in this commit from `wiki-customer-interview.md` per [ADR 0016 amendment](0016-wiki-customers-as-roles.md)). The customer-walk cycle = simulated-reading breadth coverage; customer-interviews = depth probing of specific hypotheses.

### 2. JTBD Job statements added to existing personas

Each of the 5 persona files in [`../../phase-b-business-architecture/roles/customers/`](../../phase-b-business-architecture/roles/customers/) gets a `## Job to be done` section with the format *"When I [situation], I want to [motivation], so I can [outcome]."* This is an **addition to** the existing persona files, NOT a parallel framework.

### 3. EXPLICITLY REJECTED — no Lean Canvas / MVP sketch / pivot-or-persevere / Wardley-Maps scaffolding in forge

Each rejection rationale:

- **Lean Canvas** rejected because Phase A `goals.md` + Phase B `<product>.md` + Phase B `capabilities/<capability>.md` already cover Problem / Solution / Customer Segments / Key Metrics / Cost / UVP / Channels / Revenue. Lean Canvas would duplicate the cells we already have in TOGAF-coherent form.
- **MVP sketch templates** rejected because Phase F experiments ARE MVPs ([`../../phase-f-migration-planning/experiments/`](../../phase-f-migration-planning/experiments/) — K1, K2, G1, G2, G3 are precedents).
- **Pivot-or-persevere decision template** rejected because forge handles pivots via ADR amendment + delete-on-promotion.
- **Wardley Maps directory placeholder** rejected because no actual decision needed one yet; rebuild when first decision warrants it (queued: K3 compress-by-redundancy decision).
- **Solution / Validation / Build-Measure-Learn stage scaffolding** rejected because TOGAF Phase B (Capabilities, Products) + Phase F (experiments) + Phase H (audit cycle) + ADR amendments already cover these.
- **Opportunity Solution Tree as a separate template** rejected because the prioritization work happens in [`../../phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md) (R-NN trajectory rows) and during the customer-walk cycle's CI-3..5 cross-tab — no separate OST artifact needed.

### 4. Wiring into existing forge artifacts

Existing artifacts that previously didn't reference the customer-development discipline get cross-references in the same commit:
- [`../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md`](../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md) cross-references customer-walk + interview discipline.
- [`../../phase-b-business-architecture/roles/wiki-pm.md`](../../phase-b-business-architecture/roles/wiki-pm.md) gets interview protocol added to responsibilities.
- [`../../phase-b-business-architecture/products/kurpatov-wiki.md`](../../phase-b-business-architecture/products/kurpatov-wiki.md) cross-references where customer-derived insights live (private repo).

Without this wiring, the customer-development discipline floats; with it, the discipline is part of the architecture.


### 8. Language-primary policy: customer-interview surface uses the customer's native language (NEW 2026-05-02)

Per architect call: customer-interview scripts and transcripts use the **customer's native language as primary**, not English. For kurpatov-wiki specifically:
- All 5 personas are Russian-speaking (Marina + Антон-PM are bilingual; Аня + Антон-designer + Анна work primarily in Russian).
- The Курпатов corpus is Russian.
- Therefore: scripts in `kurpatov-wiki-wiki/metadata/customer-interview-scripts/` are written in Russian; transcripts in `kurpatov-wiki-wiki/metadata/customer-interview-transcripts/` are Russian-primary with English code-switch only for technical terms where Russian is less precise (e.g. RCT, evidence-base, primary-source attribution).
- Schema labels (`**Severity**`, `**Affected personas**`, etc.) remain English because audit-cycle tooling parses them.

This rule generalises: a future product targeting English-speaking customers would have English-primary interview surface; a future product targeting French-speaking customers would have French-primary; etc. The customer's native language is non-negotiable for interviews; the architect's working language can differ.

The original 2026-05-02 morning interviews were run in English (mistake caught by architect call same day). Russian re-run produced the same verdicts (3 REFINED, 2 REFUTED) — validates that the methodology is robust to language choice, AND that the original run was a wasted hour of Cowork compute that the language-primary policy prevents in future.

## Consequences

- **Plus**: forge's discipline stays simple. TOGAF + ArchiMate + RLVR + OKR cascade + customer-interview-protocol + JTBD-in-personas. No parallel methodology layer.
- **Plus**: ~14 over-engineered files removed; ~3 genuinely-new artifacts added; existing 3-5 forge files updated to reference them. Net: leaner.
- **Plus**: future architects don't have to choose between "Lean stage" and "TOGAF phase" — there's only one structure.
- **Minus**: when forge enters a phase where Wardley Maps would help (real architecture decision with utility-vs-custom trade-off), we'll need to author that schema. That's a build-when-needed cost; cheaper than maintaining unused scaffolding.

## Invariants

- Customer-interview script + protocol live in `phase-requirements-management/` (where TOGAF Requirements Management activities live), NOT in a `processes/` subdirectory of Phase B.
- JTBD Job statements live INSIDE existing persona files, NOT as a separate framework directory.
- Pivots land as ADR amendments + delete-on-promotion, NOT as separate "pivot-decision" artifacts.
- Wardley Maps will be authored when an actual technology decision needs one, NOT as scaffolding.

## Alternatives considered

- **Original draft**: full Lean Startup adoption with 17 process documents. Rejected by self-audit + architect call as massive over-engineering.
- **Maurya's *Running Lean* as primary methodology base, TOGAF as documentation layer**. Rejected because TOGAF/ArchiMate IS the methodology base; Lean adds only customer-interview discipline beyond that.
- **Phase B `processes/` directory**. Rejected because the templates inside are schemas (Business Objects), not Business Processes; ArchiMate-typing was wrong.

## Follow-ups

- Author the worked example (apply customer-interview discipline to kurpatov-wiki) when ready. Per architect: "then we will proceed to wiki."
- Tighten P31 audit predicate to the new minimal scope (it currently references the deleted `processes/` directory tree).
