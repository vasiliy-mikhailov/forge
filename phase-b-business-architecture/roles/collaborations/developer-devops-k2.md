# Collaboration: Developer + DevOps for K2 execution

ArchiMate construct: **Business Collaboration** (spec §4.1.2 —
"a collection of internal active structure elements that work
together to perform collective behaviour"). One actor (a Cowork
session, a CI runner, or the architect) loads this collaboration
and performs the aggregated behaviour of both
[Developer](developer.md) and [DevOps](devops.md) — without
having to spin up two sessions.

The earlier framing — "Developer in one Cowork session, DevOps
in another" — was an over-strict reading of role separation.
TOGAF and ArchiMate both model multi-role aggregation: a single
Actor fills a Collaboration that aggregates two Roles, the
collaboration's behaviour combines the role behaviours, and the
audit's role-test predicates fire against whichever role the
audited artefact belongs to.

## Composition

This Collaboration aggregates exactly two roles:

- [Developer](developer.md) — implements / sweeps / measures /
  commits algorithm code.
- [DevOps](devops.md) — runs the container on
  `mikhailov.tech`, appends to `operations.md` `## Operational log`,
  rolls back on smoke fail.

The Architect / Wiki PM / Auditor roles are NOT in this
sub-collaboration — they have separate accountabilities
(structural decisions, requirements emission, audit-walking)
that would conflict with execution duties.

This collaboration is a **sub-collaboration of**
[Kurpatov-wiki-team](kurpatov-wiki-team.md) — the broader
product team containing all five roles. When K2 execution is
in flight, this 2-role collab is the executor; when an
architect decision or audit walk is needed, the parent collab
takes over.

## Activates from

[`/phase-f-migration-planning/experiments/K2-compact-restore.md`](../../phase-f-migration-planning/experiments/K2-compact-restore.md)
— specifically the Day 3-6 sequenced-work entries (run
K2-R1..R4 against real lecture A on the Blackwell). The
collaboration is the *executor* of those entries.

## Realises

- Both roles' Realises lists, jointly: **Service operation**
  (host stays clean; deploy is one container; logs are
  observable) + **R&D** (algorithm runs against real data; trip-
  quality numbers populate the Execution log).

## Decision rights (union)

- Developer's decision rights apply when the action touches
  algorithm / test code.
- DevOps's decision rights apply when the action touches the
  host / container / operations.md.
- A single command that does both (e.g. `docker compose run
  k2-sweep`) is decided at the **DevOps** level (it's a host
  action) but its arguments are decided at the **Developer**
  level (it's algorithm parameter selection). The
  collaboration internalises this hand-off — no architect
  approval needed for the routine case.

## Escalates to architect

Union of both roles' escalations. Specifically:

- Schema changes to the K2 compact-form output → Wiki PM (then
  architect).
- Cross-lab edits in the algorithm code → architect.
- ADR-level deploy decisions (new container topology, GPU
  policy) → architect.
- A K2 run whose trip-quality FALSIFIES the L1 hypothesis gate
  (≥ 0.20) → flagged to the architect; collaboration does NOT
  decide whether to chase V5 / move to L2 / weaken the gate.

## Capabilities (union)

| Capability                       | From role |
|----------------------------------|-----------|
| OpenHands SDK                    | Developer |
| Git (commit / push to main)      | Developer |
| pytest / unit-test runners       | Developer |
| Sweep CLIs (`compact_restore/sweep.py`) | Developer |
| --log-scores discipline           | Developer |
| SSH to mikhailov.tech            | DevOps    |
| `docker compose` per-lab         | DevOps    |
| `make` per-lab targets           | DevOps    |
| `nvidia-smi` GPU inspection      | DevOps    |
| `operations.md` ## Operational log edits | DevOps |
| `tests/smoke.sh` post-deploy     | DevOps    |

## Filled by (today)

A Cowork session that has:

- read+write access to the forge tree at `~/forge`,
- read access to `kurpatov-wiki-raw` (mounted at
  `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/` on the host),
- SSH to mikhailov.tech (`~/.ssh/kurpatov-wiki-vault` deploy key),
- `docker compose` available.

The collaboration MAY also be filled by a CI runner that has
the same capabilities; the role definition is harness-agnostic.

## Tests

Both [`test-developer.md`](../../tests/phase-b-business-architecture/roles/test-developer.md)
(DV-NN) and [`test-devops.md`](../../tests/phase-b-business-architecture/roles/test-devops.md)
(DO-NN) apply. The collaboration does not get its own runner — its
behaviour is the union of the two role behaviours, and each
behaviour is already covered by its role's runner.

The audit's P14 (motivation chain) walks against this file too;
the motivation chain below satisfies it.

## Motivation chain

Per [ADR 0015](../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1, applied to a collaboration:

- **Driver**: Architect-velocity (a single Cowork session
  finishes a K2 run in one pass; loading two sessions doubles
  context-switch cost) + R&D throughput (more falsifiable
  hypotheses closed per week).
- **Goal**: Architect-velocity + R&D throughput (Phase A).
- **Outcome**: Each K2-Rn ships a row in the Execution log + a
  dated entry in operations.md `## Operational log`, in one
  commit, under one author, without architect attention beyond
  reviewing the verdict.
- **Capability realised**: Service operation + R&D
  ([`../capabilities/forge-level.md`](../capabilities/forge-level.md)).
- **Function**: Run-experiment-end-to-end-against-real-data.
- **Collaboration**: Developer + DevOps (this file).

## When to add another collaboration here

When a recurring task crosses ≥ 2 role boundaries cleanly. Examples
that would qualify in the future:

- *Wiki PM + Developer* — when an R-NN trajectory needs both
  a requirements rewrite AND a code change in the same commit.
- *Auditor + DevOps* — when an audit finding requires an
  operational rollback (e.g., a container rolled out under a
  superseded ADR).

Today only the Developer + DevOps pair is formalised.
