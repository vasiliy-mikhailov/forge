# ADR 0017 — Motivation aspect spans every architecture layer (universal traceability principle)

## Status

Accepted (2026-05-02). Active.

## Measurable motivation chain (OKRs)
Per [ADR 0015](0015-verifiable-agent-rewards.md) decision point 1
+ [ADR 0016](0016-wiki-customers-as-roles.md) + the Phase H
audit cycle, forge has accumulated a working motivation
discipline:

- **P14** — role files have a `## Measurable motivation chain (OKRs)` section.
- **P15** — catalog rows cite Goal / Driver / closure in the Source cell.
- **P17** — test cases have a `### Reward` section.
- **P18** — Drivers `→ influences <Goal>` annotations.
- **P19** — Goals have ≥ 1 realising R-NN trajectory.
- **ADR 0015 dec 1** — measurable motivation chain (OKRs) required per role.
- **ADR 0016** — extended to consumer-side roles (Wiki Customer + 5 personas).

Each predicate was added retroactively when the audit caught a
gap in a specific artifact type. **No first principle states
that motivation traceability is universal**. So when a new
artifact type lands (a Phase D technology file; a Phase G
operations procedure; a Python script; a new ADR), the
discipline is forgotten until the audit later catches it and
yet another predicate gets bolted on.

The ArchiMate spec (§6 Motivation Layer) and the
[Visual Paradigm TOGAF + ArchiMate mapping article](https://archimate.visual-paradigm.com/2025/02/04/1289/)
make the rule explicit: **Motivation is an Aspect that spans
every Layer**. The matrix is:

|                              | Passive structure | Behavior | Active structure | **Motivation** |
|------------------------------|---|---|---|---|
| **Strategy**                 | • | • | • | **•** |
| **Business**                 | • | • | • | **•** |
| **Application**              | • | • | • | **•** |
| **Technology**               | • | • | • | **•** |
| **Physical**                 | • | • | • | **•** |
| **Implementation & Migration** | • | • | • | **•** |

The **Motivation column** is required for every layer's elements
— not just Roles, not just R-NN rows, not just tests. Every
Active Structure / Behavior / Passive Structure element CAN and
SHOULD have associated motivation: Stakeholder, Driver,
Assessment, Goal, Outcome, Principle, Requirement, Constraint
(per ArchiMate §6.2.1–6.2.10).

## Decision

### 1. Elevate to architecture principle P7

Add **P7** to
[`../architecture-principles.md`](../architecture-principles.md):

> **P7 — Universal motivation traceability.** Every architecture
> element (regardless of TOGAF phase, ArchiMate layer, or
> ArchiMate aspect) MUST cite a measurable motivation chain (OKRs) (Driver → Goal
> → Outcome → Capability → Function → Role / Component /
> Process) OR be transitively covered per ADR 0013 dec 9 with
> the abstract / parent named explicitly. Default = required;
> opt-out = transitive carve-out with documented rationale.

### 2. Universal predicate P24 added to `audit-process.md`

> **P24 — Universal motivation-chain coverage.** For every md
> artifact under `phase-a/`, `phase-b/`, `phase-c/`, `phase-d/`,
> `phase-e/`, `phase-f/`, `phase-g/`, `phase-preliminary/`
> (excluding READMEs, lab-internal scaffolding under
> `<lab>/.agents/`, and the carve-outs documented in P14):
> file contains either `## Measurable motivation chain (OKRs)` section OR a
> `Transitive coverage:` reference naming the parent artifact
> whose chain it inherits.

### 3. ADR template gains required Motivation section

Every NEW ADR (numbered 0017+) MUST include a `## Motivation`
section (this ADR is the first; future ADRs follow). Older
ADRs (0001 / 0009 / 0013 / 0014 / 0015 / 0016) are back-fit in
the gap-remediation commit landing alongside this ADR.

### 4. Phase-spanning gap remediation in the same commit

The fail-closed P24 walk would surface ~10 gap-rows on a
naked landing (no chain in `develop-wiki-product-line.md`,
`wiki-product-line.md`, `phase-d/architecture.md`,
`lab-AGENTS-template.md`, `phase-e/*.md`, `operations.md`
header sections, the 6 existing ADRs). All ten get a
Measurable motivation chain (OKRs) in the same commit so P24 lands clean.

### 5. Aspect-aware layer mapping recorded

ADR 0014 already adopted ArchiMate; this ADR sharpens the
TOGAF↔ArchiMate mapping per the Visual Paradigm matrix:

| TOGAF Phase                  | ArchiMate Layer                    | Aspect emphasis (today's forge content) |
|------------------------------|------------------------------------|------------------------------------------|
| Preliminary                  | **Motivation** (cross-cutting)     | Principles, Drivers, Goals, ADRs |
| A — Architecture Vision      | Strategy + Business                | Drivers, Goals, Stakeholders, Capability outline |
| B — Business Architecture    | Business (Active + Behavior)       | Roles, Capabilities, Products, Processes |
| C — Information Systems      | Application (Active + Behavior)    | Application Components (Labs), Services |
| D — Technology Architecture  | Technology (Active + Behavior)     | Nodes, Devices, System Software |
| E — Opportunities & Solutions | Implementation & Migration       | Plateaus, Gaps |
| F — Migration Planning       | Implementation & Migration         | Work Packages, Experiments |
| G — Implementation Governance | Implementation & Migration       | Operations, runbook |
| H — Architecture Change Management | Implementation & Migration   | Audits, predicates, trajectories |

Forge has no **Physical** layer (no facilities; the Blackwell
GPU is modelled as Technology Device per the spec — devices
are Technology, not Physical).

The Motivation column in the matrix is satisfied by the chain
in EACH non-Motivation cell — i.e., every artifact under any
phase has its own `## Measurable motivation chain (OKRs)` (P24) AND every
catalog-row (R-NN), Driver, Goal, Reward already cited in the
prior P14–P19 predicates.

## Consequences

- **Plus**: forge can never silently introduce a new artifact
  type that lacks motivation traceability. P24 fails closed; the
  default is "chain required".
- **Plus**: future architects (or LLM agents filling roles) read
  the principle once, not per-predicate. New artifact types
  inherit the discipline by default.
- **Plus**: ArchiMate-faithful — Motivation is treated as an
  aspect, not as a property of specific element types.
- **Minus**: more prose per artifact (the measurable motivation chain (OKRs) is
  ~10 lines per file). Mitigated by the transitive-coverage
  carve-out for instance/sub-artifacts with shared chains.
- **Minus**: P24 false-positives possible when an artifact
  legitimately has no motivation (e.g., a generated CSV). Mitigated
  by the carve-out list in the predicate definition; new carve-outs
  require an architect call.

## Invariants

- A new artifact type added to forge without a measurable motivation chain (OKRs)
  AND without a documented transitive-coverage rationale is a
  P24 FAIL on the next audit walk.
- The carve-out list inside P24 is single-source-of-truth for
  exclusions; ad-hoc skipping is forbidden.
- Existing ADRs back-fit in this commit are not exhaustive —
  any future amendment to an existing ADR triggers a P24 walk
  on that ADR.
- "Transitive coverage" per ADR 0013 dec 9 is the only legal
  way to skip a per-file chain; the abstract / parent must be
  named.

## Alternatives considered

- **Keep enforcing per-artifact-type with retroactive
  predicates.** Status quo. Falsified by the 10-gap finding
  in audit-2026-05-01s F2/F3 — the discipline silently fails
  on new artifact types until the auditor catches it weeks later.
- **Adopt P7 but skip the back-fit sweep for existing ADRs.**
  Rejected: P24 would FAIL on landing for the 6 existing ADRs;
  fixing-as-we-go is no different from the per-type bolt-on
  pattern this ADR is correcting.
- **Make Measurable motivation chain (OKRs) a per-file YAML frontmatter
  field instead of a prose section.** Considered. Rejected:
  YAML loses the narrative context that makes a chain
  understandable; prose with a strict heading + bullet
  structure (current shape) is more readable + still grep-able
  for P24's mechanical check.

## Measurable motivation chain (OKRs)
Per the principle this ADR introduces, this ADR cites its own
chain:

- **Driver**: Architect-velocity (every minute the architect
  spends bolting on a retroactive predicate is a minute not
  spent on the next experiment) + audit reliability (a
  fail-open enforcement model leaks gaps).
- **Goal**: Architect-velocity (Phase A); Audit reliability
  (transitive — the audit-process predicates ARE forge's
  reliability mechanism).
- **Outcome**: P24 walks clean post-this-commit; future
  artifact types inherit motivation discipline by default; no
  more retroactive bolt-on predicates for motivation
  traceability.
- **Measurement source**: audit-predicate: P24 (universal motivation-chain coverage; latest walk = 0 FAIL)
- **Capability realised**: Architecture knowledge management
  ([`../../phase-b-business-architecture/capabilities/forge-level.md`](../../phase-b-business-architecture/capabilities/forge-level.md))
  — the meta-capability of keeping forge's architecture
  internally consistent.
- **Function**: Elevate-motivation-to-first-principle.
- **Role / Element**: Architect-of-record (ADR-emission is an
  Architect-only authority per P1).

## Follow-ups

- ADR template artifact at `phase-preliminary/adr/_template.md`
  documenting the required structure + Motivation section. Today
  ADRs follow the implicit shape; codifying it is queued.
- A Phase E gap-catalogue process spec (today gaps are implicit
  in R-NN + audit findings). Once authored, P24 walks it.
- Per-phase READMEs (`phase-a/README.md`, etc.) — currently
  carved out from P24; revisit once Phase E catalogue lands.
