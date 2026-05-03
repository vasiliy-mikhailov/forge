# Product development approach

This file documents forge's **product-development discipline** — the meta-method by which the team moves from "Plan A" (what we believe about a product) to "a Plan that works" (what we have validated). Sits parallel to [`architecture-method.md`](architecture-method.md) (which documents the architecture-documentation discipline).

Per [ADR 0027](adr/0027-product-development-approach.md): Maurya's *Running Lean* is the iterative base, complemented by Wardley Maps (architecture/strategy decisions), Jobs-to-be-Done (persona depth), and Teresa Torres' Opportunity Solution Trees (problem prioritization).

## 1. Base — Maurya's *Running Lean*

**Plan A → Plan that works.** A product begins as a set of beliefs (Plan A). Each belief is an assumption; the riskiest assumptions are tested first; results either confirm-and-proceed or pivot-and-revise. Iteration ends when remaining assumptions are not worth the cost of testing.

**Three interview stages**:

| Stage | Tests | Output |
|-------|-------|--------|
| **Problem interview** | Does the customer actually have the pain we think? | Validated problem list per persona |
| **Solution interview** | Does our proposed solution actually solve the validated problem? | Validated solution sketch |
| **Validation interview** | Does the customer hire the built MVP? Pay for it? Renew? | Pivot-or-persevere decision |

**Lean Canvas** — one-page strategic artifact per product. Nine cells: Problem · Solution · Key Metrics · Unique Value Proposition · Unfair Advantage · Channels · Customer Segments · Cost Structure · Revenue Streams. Forge uses the Lean Canvas template from [`../phase-b-business-architecture/processes/discovery/lean-canvas-template.md`](../phase-b-business-architecture/processes/discovery/lean-canvas-template.md).

**Authoritative source**: Maurya, *Running Lean* (3rd ed., 2022); [`https://leanstack.com/`](https://leanstack.com/).

## 2. Complement — Wardley Maps for architecture / strategy decisions

When the decision is about technology stack, component build-vs-buy, or evolution stage, Maurya is silent and Wardley is rigorous.

**Use for**:
- ETL stack choices (Whisper-VAD vs alternatives).
- Compact-restore architecture (K2 / K3).
- Vector-retrieval / inference subsystem (R-D-* trajectory rows).
- Any "is this utility or custom-build?" decision.

**Output**: a Wardley Map per architecture decision; saved to the relevant phase directory (Phase D for technology, Phase C for application architecture).

**Authoritative source**: Wardley, *Wardley Maps* book; [`https://learnwardleymapping.com/`](https://learnwardleymapping.com/).

## 3. Complement — Jobs-to-be-Done for persona depth

Personas tell *who*; JTBD tells *what they hire the wiki to do*. The Job statement format: "When I [situation], I want to [motivation], so I can [outcome]."

**Use for**:
- Persona authoring + revision (every persona file should have an explicit Job statement).
- Pain-ledger framing (every pain becomes "this defeats the job").
- Forces of Progress check (Push, Pull, Anxieties, Habits) when assessing whether a customer would actually adopt a fix.

**Authoritative source**: Christensen, *Competing Against Luck* (2016); Klement, *When Coffee and Kale Compete*; Bob Moesta interviews.

## 4. Complement — Torres' Opportunity Solution Trees

When the team has N problems and bandwidth for fewer, OST gives an explicit visual structure: outcome at root → opportunities → solution candidates → experiments. Forge uses OST during the **prioritization step** of Discovery (between problem-list authoring and choosing-which-to-test).

**Output**: a single OST per discovery cycle; saved to `phase-b-business-architecture/products/<product>/discovery/opportunity-solution-tree.md`.

**Authoritative source**: Torres, *Continuous Discovery Habits* (2021); [`producttalk.org/opportunity-solution-tree/`](https://www.producttalk.org/opportunity-solution-tree/).

## 5. How this approach relates to forge's existing discipline

Two layers, complementary:

| Layer | What it is | Where documented |
|-------|------------|------------------|
| **Product-development discipline** | What product to build, for whom, validated by interviews and experiments. The discovery / solution / validation cycle. | THIS file + [`adr/0027-product-development-approach.md`](adr/0027-product-development-approach.md) |
| **Architecture-documentation discipline** | How decisions are recorded, audited, traced. ADRs, predicates, audit cycle, OKR cascade. | [`architecture-method.md`](architecture-method.md) + [`architecture-principles.md`](architecture-principles.md) + [audit-process.md](../phase-h-architecture-change-management/audit-process.md) |

Both are necessary. Lean tells you *what to build*; architecture tells you *how to remember and validate the decisions*.

## 6. Decision matrix — when to reach for which tool

| Question | Tool | Output artifact |
|----------|------|-----------------|
| What does the customer hire our product to do? | JTBD | Updated persona Job statement |
| What does Plan A claim about this product? | Lean Canvas | `phase-b/products/<product>/lean-canvas.md` |
| Is this problem real? Validated? | Problem interview (Maurya) | Interview transcript (private per [ADR 0018 § 7](adr/0018-privacy-boundary-public-vs-private-repos.md)) + summary |
| Out of N problems, which to work on? | Opportunity Solution Tree | `phase-b/products/<product>/discovery/opportunity-solution-tree.md` |
| Will this solution actually solve the problem? | Solution interview (Maurya) | Interview transcript + sketch |
| Should we build component utility or custom? | Wardley Map | `phase-d/wardley-maps/<decision>.md` (queued — directory not yet created) |
| Did the MVP work? | Validation interview + Build-Measure-Learn | Pivot-or-persevere decision artifact |
| Did the architecture decision land cleanly? | ADR + audit walk | `phase-preliminary/adr/<NNNN>-<slug>.md` |
| Did the goal advance? | OKR cascade | [`goals-report.py`](../scripts/test-runners/goals-report.py) output + chain Contribution bullet |

## 7. Stealth-mode caveat

Forge today operates with **simulated personas** (LLM agents activated against persona files), not real customers. Maurya is unambiguous: real validation requires real customers.

Operational rules in stealth mode:
- Plan-A iteration in stealth is fine for direction-finding (no other option exists pre-launch).
- The Customer-Interview cycle (per [ADR 0016](adr/0016-wiki-customers-as-roles.md)) is honest about being a **simulated-reading walk + PM-solo synthesis** — useful for breadth coverage; not a substitute for actual interviews.
- Product-market-fit claims require real users. Until forge has real users, all "validated learning" claims carry the implicit qualifier "in stealth mode against simulated personas."
- Once a real-user cohort exists (kurpatov-wiki commercial launch; future products), interview-based validation supersedes simulated-reading walks; ADR amendment will retire the stealth-mode language.

This caveat is the most important honest thing in this file — Maurya's framework misapplied claims more validation than has happened.

## 8. Stages mapped to forge artifact paths

| Stage | Architecture documents | Per-product instances |
|-------|------------------------|------------------------|
| **Discovery** | [`phase-b-business-architecture/processes/discovery/`](../phase-b-business-architecture/processes/discovery/) — README + 4 templates | `phase-b-business-architecture/products/<product>/discovery/` (instances) + `kurpatov-wiki-wiki/metadata/discovery/` (private transcripts) |
| **Solution** | (queued — to author when forge enters Solution stage) | (TBD) |
| **Validation** | (queued) | (TBD) |
| **Build / Measure / Learn** | Phase F experiments (existing) | `phase-f-migration-planning/experiments/<id>.md` |
| **Pivot-or-persevere** | (queued — could land as ADR template) | ADR per pivot decision |

## 9. Measurable motivation chain

Per [P7](architecture-principles.md):

- **Driver**: forge's product-development discipline was implicit before this commit. Each new product cycle re-litigated method choice (CI-2 framing as "interview" when actually a "walk"; no formal problem prioritization for 10-problems pick-1; Wardley not yet adopted for architecture decisions). Methodology drift is an architect-velocity hit.
- **Goal**: [Architect-velocity](../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Approach codified once eliminates per-cycle methodology arguments.
- **Outcome**: this file + [ADR 0027](adr/0027-product-development-approach.md) + 5 discovery-stage artifact templates land as a coherent meta-method addition; future cycles cite the approach instead of re-inventing it.
- **Measurement source**: audit-predicate: P26 (every chain has a Measurement source line — this file complies) + audit-predicate: P29 (every chain cites a named Goal — this file cites Architect-velocity).
- **Contribution**: this approach file is the canonical reference for the WHY of forge's product-development work. Each downstream artifact (Lean Canvas, interview script, OST) cites this file's section by number; the approach is queryable by tool name; methodology drift becomes auditable.
- **Capability realised**: [Architecture knowledge management](../phase-b-business-architecture/capabilities/forge-level.md) — the meta-capability of keeping forge's discipline internally consistent.
- **Function**: Document-product-development-approach.
- **Element**: this file.
