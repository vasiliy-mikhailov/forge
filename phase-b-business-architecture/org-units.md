# Organization units

Two categories of org-unit exist in forge today, and they do not
collapse into each other:

| Category | Plurality | What they do | Style |
|----------|-----------|--------------|-------|
| **Architect** | 1 | *Make the structure.* Design the TOGAF artefacts, decide trajectories, write requirements, author prompts, gate ADRs. Functional / declarative work. | architect of record |
| **Roles** | many | *Make the structure alive.* Execute within the structure the architect designed: run the requirements process, edit lab code under spec, drive the bench coordinator, push commits, etc. Operational / imperative work. | one file per role in [`roles/`](roles/), filled today by Claude / Cowork / Codex sessions (actors) |

The split exists because the work has two distinct shapes. The
architect produces durable artefacts the agents reference; agents
produce running outputs the architect reviews. A role-filling actor does not
edit the architecture (no committing into `phase-*/`); the
architect does not run the per-source pipeline (no per-claim
prompt orchestration). When a change blurs the line — an actor in a role
changing an ADR, the architect manually editing a single
source.md — that is a smell, not the convention.

## Architect

**Architect of record** — one human, the repo owner. Sole driver
of trajectory changes; sole reviewer; today the only consumer of
every output. See
[`../phase-a-architecture-vision/stakeholders.md`](../phase-a-architecture-vision/stakeholders.md)
and
[`../phase-preliminary/architecture-team.md`](../phase-preliminary/architecture-team.md)
for the full role definition and the conditions that would
re-open Preliminary (a second architect, an external operator, a
paying consumer).

## Roles

Functional responsibilities that execute within the structure.
In TOGAF metamodel terms, a **Role** is a function or set of
responsibilities; an **Actor** is the person or system that
fills it. Today most roles in [`roles/`](roles/) are filled by
LLM agents (Claude / Cowork / Codex sessions); the role file
describes the responsibility, not the actor.

| Role | Definition | Activates from | Realises |
|------|------------|----------------|----------|
| Wiki PM | [`roles/wiki-pm.md`](roles/wiki-pm.md) | [`../phase-requirements-management/wiki-requirements-collection.md`](../phase-requirements-management/wiki-requirements-collection.md) | Requirement traceability dimension of the [`Develop wiki product line`](capabilities/develop-wiki-product-line.md) capability |
| Auditor | [`roles/auditor.md`](roles/auditor.md) | [`../phase-h-architecture-change-management/audit-process.md`](../phase-h-architecture-change-management/audit-process.md) | Architecture Knowledge Management capability ([`capabilities/forge-level.md`](capabilities/forge-level.md)) — single source of truth + TOGAF-style doc threading dimensions |

Other roles that operate today but aren't yet formalised as
role files (when one of them produces a regression requiring
written decision rights, it gets a file):

- **Source-author / concept-curator** — internal Python
  coordinator now (per the wiki-bench `ADR 0013`,
  [`../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/)).
  No longer a separate role; subsumed into the lab.
- **Wiki-bench developer** — Cowork session that edits
  `wiki-bench` source under spec. Role file pending — write one
  when an edit conflict requires explicit decision rights.

## Why labs are not org-units

Restating the existing rule for clarity: the `wiki-*` and `rl-*`
labs are **application components in
[Phase C](../phase-c-information-systems-architecture/application-architecture/)**,
not org-units. A lab is *what runs*; an agent is *who runs it*; an
architect is *who designed what runs*.

In TOGAF terms, *capability* (what forge can do) and *organization
unit* (who does it) are independent. Each lab's own AGENTS.md
Phase B holds the *lab-scoped* capability subset (with quality
dimensions appropriate to that lab's domain).
