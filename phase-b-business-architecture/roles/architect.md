# Role: Architect (of record)

## Purpose

Decide what the architecture *is*. Open ADRs when an irreversible
or layer-changing decision is needed, edit the architecture
files (Phase A goals + Phase B capabilities + Phase D technology
+ Phase G governance), promote Level 2 to Level 1 when a Phase F
experiment closes its trajectory, and refuse to delegate
decisions that the *single architect of record* principle
([P1](../../phase-preliminary/architecture-principles.md)) reserves
to one decision-maker.

This role does not author wiki content (Wiki PM does the
requirements, Developer ships the code). It does not run audits
(Auditor does). It does not operate the host (DevOps does). It
makes structural decisions, owns the architecture artefacts, and
reviews the work the other roles produce.

## Activates from

[`../../phase-preliminary/architecture-principles.md`](../../phase-preliminary/architecture-principles.md)
+ [`../../phase-preliminary/architecture-method.md`](../../phase-preliminary/architecture-method.md)
+ the audit-trail under [`../../phase-h-architecture-change-management/`](../../phase-h-architecture-change-management/).
The role is active continuously — there is no per-task
activation; the architect is the standing decision-maker.

## Inputs

- The forge working tree at `HEAD` (read+write).
- Open audit findings (the Auditor surfaces; the architect
  decides whether to fix the artefact or revise the rule).
- Wiki PM's catalog rows (the architect approves PROPOSED rows
  before they become ACTIVE).
- K2 / Phase F experiment results from the Developer + DevOps
  collaboration.
- External context (literature, ArchiMate spec, TOGAF ADM,
  technology choices) that affects forge's structure.

## Outputs

- **ADRs** — the only role allowed to open / withdraw / rewrite
  ADRs (per the *delete-on-promotion* + *no Superseded by* rules
  in [`architecture-method.md`](../../phase-preliminary/architecture-method.md)).
- **Architecture files** — Phase A goals.md / drivers.md /
  principles.md; Phase B capabilities/ + roles/; Phase D
  architecture.md; Phase G policies.
- **Catalog row approvals** — PROPOSED → ACTIVE transitions on
  R-NN rows in `phase-requirements-management/catalog.md`.
- **Trajectory promotions** — Level 2 → Level 1 swings (with
  Level 1 deletion per the trajectory rule).
- **Predicate / process spec edits** — changes to
  `audit-process.md`, `wiki-requirements-collection.md`,
  `operations.md`'s runbook portion (the chronological
  `## Operational log` is DevOps's territory).

No code edits to lab source. No prompt edits. No deploys to
production. Those are Developer / Wiki PM / DevOps territory.

## Realises

- All four forge-level capabilities at the *steering* level —
  R&D, Service operation, Product delivery, Architecture
  knowledge management ([`../capabilities/forge-level.md`](../capabilities/forge-level.md)).
- The other roles realise these capabilities at the *execution*
  level; the architect realises them at the *what should we
  build* level.

## Decision rights

The role may decide, without consultation:

- Open / withdraw / rewrite any ADR.
- Approve / reject any PROPOSED catalog row.
- Promote a Level 2 trajectory to Level 1 (and delete the prior
  Level 1 description per the trajectory rule).
- Edit any file under `phase-preliminary/`, `phase-a-…/`,
  `phase-b-…/`, `phase-d-…/`, `phase-g-…/` (the architecture
  layers).
- Re-shape the role / collaboration model (this file's
  authority).
- Refuse to delegate any of the above.

## Escalates to

The role does not escalate. *Single architect of record* (P1)
means decisions stop here. The architect MAY consult the
literature, the ArchiMate spec, the TOGAF reference, or any
external advisor — but those produce *inputs*, not *decisions*.

When the architect is uncertain: the action is to *not act* and
to log the uncertainty (typically as an INFO finding via the
Auditor, or as a `Status: PROPOSED` catalog row pending more
evidence). The cheap-experiment principle ([P5](../../phase-preliminary/architecture-principles.md))
applies — author the smallest experiment that produces the
deciding signal.

## Capabilities (today)

- **Read+write access** to the entire forge tree.
- **ADR authorship** — the canonical naming, status block, and
  delete-on-promotion discipline.
- **Eye-read** as a reward signal — for cases where mechanical
  reward functions (per ADR 0015) are not enough, the architect's
  eye-read is the final verdict (e.g., voice preservation in K2).

The role does NOT have:

- Authority to bypass the Auditor's findings (the architect
  decides what to do about a finding, not whether the finding
  exists).
- Authority to skip the Wiki PM's R-NN process (every code
  change traces to an R-NN; the architect can ADD an R-NN, but
  cannot ship code without one).

## Filled by (today)

vasiliy-mikhailov (the single architect of record per P1).
Tomorrow: the role definition is harness-agnostic on purpose,
but the *single decision-maker* constraint means the architect
slot is filled by exactly one human or one well-aligned LLM
agent — not a committee.

## Tests

[`/tests/phase-b-business-architecture/roles/test-architect.md`](../../tests/phase-b-business-architecture/roles/test-architect.md)
— PENDING (transitively covered by audit-process per ADR 0013
dec 9). The Architect's outputs are evaluated by the Auditor:
- ADR rule conformance is P3 (containers-only), P7 (no
  Superseded by), P10 (ADR numbering monotonicity).
- Architecture-file consistency is P14, P15, P18, P19
  (measurable motivation chain (OKRs)).
- Trajectory discipline is P2, P19.
The test md exists as a placeholder for the day the auditor
needs case-level decomposition (today the predicate-level
coverage is sufficient).

**Transitive coverage** (per ADR 0013 dec 9). The audit-process
predicates listed above are the architect's behaviour test
suite; `audit-process.md` is exclusively activated by the
Auditor walking against the architect's outputs.

## Measurable motivation chain (OKRs)
Per [ADR 0015](../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1:

- **Driver**: Architect-velocity (a single decision-maker is the
  fastest decision path; committees are slower) +
  decision-quality (one well-informed decision-maker beats N
  partially-informed ones for the same wall-clock).
- **Goal**: Architect-velocity (Phase A) — the meta-Goal that
  the architect's own role realises.
- **Outcome**: ADRs land on the first try; trajectories close
  cleanly; the audit walks find ≤ a handful of WARN per pass;
  the Wiki PM / Developer / DevOps / Auditor roles each have a
  clear scope and don't bleed into each other's work.
- **Measurement source**: audit-predicate: P3 (Architect surfaces only via audit findings; latest walk = 0 FAIL)
- **Capability realised**: all four forge-level capabilities at
  the steering level.
- **Function**: Decide-and-own-the-architecture.
- **Role**: Architect (this file).
