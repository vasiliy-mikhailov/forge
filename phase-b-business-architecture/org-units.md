# Organization units

Two categories of org-unit exist in forge today, and they do not
collapse into each other:

| Category | Plurality | What they do | Style |
|----------|-----------|--------------|-------|
| **Architect** | 1 | *Make the structure.* Design the TOGAF artefacts, decide trajectories, write requirements, author prompts, gate ADRs. Functional / declarative work. | architect of record |
| **Agents** | many | *Make the structure alive.* Execute within the structure the architect designed: run the requirements process, edit lab code under spec, drive the bench coordinator, push commits, etc. Operational / imperative work. | one file per agent in [`agents/`](agents/) |

The split exists because the work has two distinct shapes. The
architect produces durable artefacts the agents reference; agents
produce running outputs the architect reviews. An agent does not
edit the architecture (no committing into `phase-*/`); the
architect does not run the per-source pipeline (no per-claim
prompt orchestration). When a change blurs the line — an agent
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

## Agents

LLM agents that execute within the structure. Each is a Claude /
OpenHands / Codex session activated against a specific persona
file in [`agents/`](agents/). The persona file specifies the
agent's purpose, what it consumes, what it produces, and what it
may decide vs what it must escalate to the architect.

| Agent | Persona file | Activates from | Realises |
|-------|--------------|----------------|----------|
| Wiki PM | [`agents/wiki-pm.md`](agents/wiki-pm.md) | [`../phase-requirements-management/wiki-requirements-collection.md`](../phase-requirements-management/wiki-requirements-collection.md) | Requirement traceability dimension of the [`Develop wiki product line`](capabilities/develop-wiki-product-line.md) capability |

Other agents that operate today but aren't yet formalised as
persona files (when one of them produces a regression that
requires written decision rights, it gets a file):

- **Source-author / concept-curator** — internal Python
  coordinator now (per
  [`../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/)
  ADR 0013), no longer an external agent. Listed here for
  history; not in `agents/`.
- **Wiki-bench developer agent** — Cowork session that edits
  `wiki-bench` source under spec. Activates from the
  lab's `AGENTS.md`. Persona file pending — write one when an
  edit conflict requires explicit decision rights.

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
