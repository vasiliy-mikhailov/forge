# Roles

Role definitions for the responsibilities that operate within
the structure forge's architect designed. In TOGAF metamodel
terms, a **Role** is a function or set of responsibilities; an
**Actor** is the person or system that fills it. Today most roles
in this folder are filled by LLM agents (Claude / Cowork / Codex
sessions), but a role file describes the *responsibility*, not
the actor — when a human takes over a role, the same file
applies.

The split between architect and roles is described in
[`../org-units.md`](../org-units.md). Short version: architect
makes the structure (functional, declarative); roles execute
within it (operational, imperative). This folder is the roles
side.

## Roles formalised today

| Role | File | Tests | One-line purpose |
|------|------|-------|------------------|
| Architect | [`architect.md`](architect.md) | (transitive — covered by audit-process predicates per ADR 0013 dec 9) | Decide what the architecture *is*. Open ADRs, promote trajectories, approve catalog rows, refuse to delegate the single-decision-maker scope (P1). |
| Wiki PM   | [`wiki-pm.md`](wiki-pm.md)     | [`/tests/phase-b-business-architecture/roles/test-wiki-pm.md`](../../tests/phase-b-business-architecture/roles/test-wiki-pm.md)     | Own the requirements catalog for every product on the [Wiki product line](../products/wiki-product-line.md). |
| Auditor   | [`auditor.md`](auditor.md)     | [`/tests/phase-b-business-architecture/roles/test-auditor.md`](../../tests/phase-b-business-architecture/roles/test-auditor.md)     | Periodically check forge's working tree for conformance to its declared architectural rules; produce typed findings per [`audit-process.md`](../../phase-h-architecture-change-management/audit-process.md). |
| Developer | [`developer.md`](developer.md) | [`/tests/phase-b-business-architecture/roles/test-developer.md`](../../tests/phase-b-business-architecture/roles/test-developer.md) | Implement production code in the labs against an active R-NN trajectory or Phase F R&D experiment; pair with TDD tests; ship diffs that close hypotheses. |
| DevOps    | [`devops.md`](devops.md)       | [`/tests/phase-b-business-architecture/roles/test-devops.md`](../../tests/phase-b-business-architecture/roles/test-devops.md)       | Operate the single-host deployment (mikhailov.tech): apply deploys, restart containers, allocate GPU power-caps, rotate keys, keep [`operations.md`](../../phase-g-implementation-governance/operations.md) current. |

## Collaborations formalised today

Per ArchiMate 4 §4.1.2 (Business Collaboration), one Actor (a
Cowork session, a CI runner, or the architect) can fill multiple
Roles via a Collaboration. Today's collaborations:

| Collaboration | File | Roles aggregated | Use |
|---------------|------|------------------|-----|
| Kurpatov-wiki-team | [`collaborations/kurpatov-wiki-team.md`](collaborations/kurpatov-wiki-team.md) | Architect + Wiki PM + Auditor + Developer + DevOps | Full product team for the Kurpatov wiki; load when any cycle that may need the team's collective behaviour starts. The role decision-rights matrix scopes any subset of roles for a given task — no separate sub-collaboration needed. |

## When to add a new role file

A new file lands here when *any* of these is true:

- A role's decision rights become non-obvious — its actions
  routinely affect artefacts it doesn't own (e.g. a developer
  role that edits prompts referenced by ADRs).
- A regression traces to absent guidance for the role — the
  fix is to write the role definition, not to patch the prompt
  that failed.
- A new role is being introduced to forge for the first time
  and the architect wants its scope spelled out before whoever
  fills it produces output.

Roles that are still informal — covered by lab `AGENTS.md` or
ad-hoc instructions — stay informal until one of the triggers
above hits.

## Role file shape

Every file in this folder uses the same headers:

- **Purpose** — what the role is for, in one paragraph.
- **Activates from** — the canonical document that defines the
  role's working method (a process spec, a skill file, etc.).
- **Inputs** — what the role consumes per session.
- **Outputs** — what the role produces per session, where they
  land in the repo.
- **Realises** — which Phase B capability dimension(s) the
  role's output realises.
- **Decision rights** — what the role may decide on its own.
- **Escalates to architect** — what the role must NOT decide.
- **Filled by (today)** — which actor currently fills the role
  (Cowork session loaded with this file as persona, a human, or
  both).
- **Tests** — link to `tests/phase-b-business-architecture/roles/test-<role>.md`.
- **References** — cross-links.

Match these headers when adding a file.

## Tests

Role tests live under the top-level [`/tests/`](../../tests/)
folder, mirroring the source path of the role they cover. The
file is prefixed `test-`:

```
forge/tests/<source-path-of-role>/test-<role>.md
   →  forge/tests/phase-b-business-architecture/roles/test-wiki-pm.md
```

This matches the unit-test convention. Inside the test file,
multiple test scenarios appear as `## T-<role-abbrev>-NN` H2
sections. The convention for an individual test (Scenario,
Fixture, Acceptance, Run, Status, Coverage map; lifecycle
RED → GREEN → STALE) is described in the test file's own
header.

A role with no test file is at *coverage L0* (informal); a role
with ≥ 1 test scenario is at L1; full coverage levels are
defined in the test file itself.
