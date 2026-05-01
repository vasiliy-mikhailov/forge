# Collaboration: Kurpatov-wiki-team

ArchiMate construct: **Business Collaboration** (spec §4.1.2 —
"a collection of internal active structure elements that work
together to perform collective behaviour"). The full team
working on the [Kurpatov wiki product](../../products/kurpatov-wiki/),
modelled as one collaboration so a single Cowork session can
load the team's collective behaviour without spinning up five
sessions.

This is the **product team** for the Kurpatov wiki — the
broadest collaboration in forge today. Includes the
[Architect of record](../architect.md) at the steering level
and the four execution roles (Wiki PM / Auditor / Developer /
DevOps). One collaboration is enough — when only a subset of
roles is needed for a task (e.g. Developer + DevOps for a K2
run), load this file and use the role decision-rights matrix
below to scope the work; spawning sub-collaborations for every
2-3 role pair is over-modelling.

## Composition

Five aggregated roles:

| Role            | Function in the team                                                  | File                                               |
|-----------------|------------------------------------------------------------------------|----------------------------------------------------|
| **Architect**   | Decides what the architecture *is*; owns ADRs, trajectories, structural files; refuses to delegate the single-decision-maker scope. | [`../architect.md`](../architect.md)                 |
| **Wiki PM**     | Owns the requirements catalog for the Kurpatov wiki; runs the corpus walk; emits R-NN rows; authors Phase F R&D experiment specs.    | [`../wiki-pm.md`](../wiki-pm.md)                     |
| **Auditor**     | Walks `audit-process.md` predicates against the working tree; emits typed findings; surfaces violations *without* fixing them.        | [`../auditor.md`](../auditor.md)                     |
| **Developer**   | Implements code in wiki-bench / wiki-compiler / wiki-ingest against an active R-NN trajectory or experiment spec; pairs with TDD.    | [`../developer.md`](../developer.md)                 |
| **DevOps**      | Operates `mikhailov.tech` (Blackwell + RTX 5090); runs containers per [P3](../../../phase-preliminary/architecture-principles.md); appends to `operations.md` `## Operational log`. | [`../devops.md`](../devops.md)                       |

The team **does not** include external readers, sales, content
authors, or any human acting as Курпатов himself — this is the
*production team*, not the *audience* or the *original source*.

## Activates from

The active product file
[`../../products/kurpatov-wiki/`](../../products/kurpatov-wiki/)
(specifically `corpus-observations.md` for Wiki PM,
[`/phase-f-migration-planning/experiments/K2-compact-restore.md`](../../../phase-f-migration-planning/experiments/K2-compact-restore.md)
for Developer + DevOps), plus the standing `audit-process.md`
for the Auditor and the standing `architecture-principles.md`
for the Architect.

A single Cowork session loaded with this collaboration can
perform any combination of the five roles' behaviours in one
pass — bounded only by the **decision-rights matrix** below.

## Realises

All four forge-level capabilities, jointly:

- **R&D** — Wiki PM emits hypotheses, Architect approves them
  as Phase F experiments, Developer ships them, Auditor walks
  the result; jointly the team produces falsifiable knowledge.
- **Service operation** — DevOps keeps the host clean,
  Developer's code reaches a GPU, Auditor catches operational
  drift.
- **Product delivery** — Wiki PM ↔ Architect ↔ Developer chain
  ships the wiki; DevOps publishes via the wiki-ingest pusher
  pipeline.
- **Architecture knowledge management** — Architect owns the
  artefacts; Auditor checks them; Wiki PM consumes them when
  authoring R-NN rows; Developer cites them in commit messages
  (per DV-01).

## Decision rights (matrix)

The team's decision rights are **NOT a union** — they are
**partitioned** by role to prevent ambiguity:

| Action                                          | Decided by                        |
|--------------------------------------------------|------------------------------------|
| Open / withdraw / rewrite an ADR                | **Architect** (only)              |
| Promote a Level 2 trajectory → Level 1          | **Architect** (only)              |
| Approve a PROPOSED catalog row → ACTIVE         | **Architect** (only)              |
| Add a PROPOSED catalog row                      | **Wiki PM**                        |
| Author / re-walk a corpus walk (S1+S2 etc.)     | **Wiki PM**                        |
| Author a Phase F experiment spec                | **Wiki PM** (Architect approves) |
| Walk the audit predicates                       | **Auditor**                        |
| Emit a finding (FAIL / WARN / INFO)             | **Auditor**                        |
| Refuse to fix a finding                         | **Architect** (Auditor surfaces)  |
| Edit lab source code                            | **Developer**                      |
| Add a unit test                                 | **Developer**                      |
| Run a sweep / measure trip-quality              | **Developer**                      |
| Commit + push to `main`                         | **Developer** OR **DevOps** (per their commit-prefix conventions) |
| Build / restart a container on `mikhailov.tech` | **DevOps**                         |
| Edit `operations.md` `## Operational log`       | **DevOps**                         |
| GPU power-cap change (within ADR-allowed band)  | **DevOps**                         |
| GPU policy change (driver, HMM, persistence)    | **Architect** (DevOps proposes)   |

Conflicts are resolved by the Architect (P1 — single architect
of record).

## Capabilities (union, scoped to role decision rights above)

The collaboration inherits every capability listed in the five
component role files. The Cowork session loaded with this
collaboration must have **all** of them available simultaneously:

- Read+write to forge tree (Architect / Developer / DevOps).
- Read access to `kurpatov-wiki-raw` + `kurpatov-wiki-wiki`
  (Wiki PM / Developer).
- SSH to `mikhailov.tech` with the `kurpatov-wiki-vault` deploy
  key (DevOps).
- `docker compose` / `make` / `nvidia-smi` / `git` (Developer +
  DevOps).
- `pytest` and the per-runner CLIs (Developer; the Auditor uses
  the runners' output).
- The Wiki PM's LLM-as-judge harness for WP-07..14 (Wiki PM).

## Filled by (today)

A single Cowork session that has all the capabilities above.
The Architect slot is currently filled by `vasiliy-mikhailov`
(the human); the other four roles are filled by Claude (Cowork
desktop session) loaded with the relevant activation files.
Tomorrow: the architect slot may be filled by an LLM agent if
the *well-aligned single decision-maker* constraint of P1 is
satisfied; the other roles are already harness-agnostic.

## Tests

The collaboration does not get its own runner — its behaviour
is the disciplined union of the five role behaviours, and each
role's tests already cover its slice:

- Architect → audit-process predicates (transitive per ADR 0013
  dec 9).
- Wiki PM → `test-wiki-pm.md` (WP-01..14).
- Auditor → `test-auditor.md` (AU-01..11).
- Developer → `test-developer.md` (DV-01..06).
- DevOps → `test-devops.md` (DO-01..06).

Aggregate scores per role land in the audit's
`## Aggregate scores per agentic-md unit` table (P22 + AU-11).

## Motivation chain

Per [ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1, applied to a collaboration:

- **Driver**: Single architect of record (P1) doesn't scale to
  five concurrent role behaviours; without the collab model,
  the architect either context-switches between roles
  (slow + error-prone) or spawns five sessions (load + token
  cost). The collab model lets one session perform the team's
  behaviour, with the decision-rights matrix above keeping the
  partition honest.
- **Goal**: Architect-velocity (Phase A) + R&D throughput.
- **Outcome**: One Cowork session can complete an end-to-end
  product cycle for the Kurpatov wiki — Wiki PM identifies the
  R-NN gap, Architect approves, Developer ships, DevOps deploys,
  Auditor walks the result — without context-switch costs at
  the role boundaries (the collab loads all five activations
  at once).
- **Capability realised**: all four forge-level capabilities,
  jointly, end-to-end.
- **Function**: Operate-the-Kurpatov-wiki-product-team.
- **Collaboration**: Kurpatov-wiki-team (this file).

