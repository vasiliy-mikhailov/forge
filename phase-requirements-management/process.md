# Requirements process

How a requirement enters the catalog, gets routed to a Phase F
experiment, and exits.

## Lifecycle

```
   stakeholder need / metric gap / experiment side-effect
                     │
                     ▼
        emitted at Phase A / B / D / F-closure
                     │
                     ▼
        added to phase-requirements-management/catalog.md
                     │
                     ▼
   routed to a Phase B / D quality-dim trajectory (L1 → L2)
                     │
                     ▼
        Phase F experiment opened with closure criteria
                     │
                     ▼
        experiment runs; PASS or FAIL recorded in spec
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
   PASS:                       FAIL:
   - L2 becomes new L1         - requirement stays open
   - prior L1 deleted from     - sub-requirements emitted
     phase-B / phase-D doc       (added to catalog)
   - row deleted from catalog  - retry as a new Phase F
                                 experiment id, or change
                                 the requirement
```

## Where requirements come from

- **Phase A goals.** TTS / PTS / EB / Architect-velocity — every
  Phase B / D quality-dim trajectory must roll up to one of
  these. New goals open Preliminary (rare).
- **Phase E gap analyses.** Per-lab `STATE-OF-THE-LAB.md` files
  enumerate what isn't at Level 2 yet. Each open gap becomes a
  Phase B or Phase D row.
- **Phase F closures (success or failure).** A closed-falsified
  experiment often emits new sub-requirements (e.g. G3 surfaced
  R-D-contract-prewrite + R-D-contract-xreflint).
- **External events.** A new product (Tarasov Wiki) opens a
  whole product-line worth of requirements. New hardware or
  vendor changes do too.

## Where requirements go to die

A requirement leaves the catalog when:

- **Promoted.** Level 2 reached → Level 2 becomes new Level 1 in
  the phase-B / phase-D file → the corresponding catalog row is
  deleted. Git history is the archive.
- **Falsified at gate-1 (cheap).** Microbench shows the
  hypothesis can't be reached → catalog row updated with the
  short reason and the next attempt's req id; original req
  itself stays open until a different attempt closes it.
- **Replaced.** A different formulation supersedes (e.g. "make
  decode faster" replaced by "reduce per-claim overhead" after
  G2/G3). The original row is deleted; the replacement is added.
- **Deferred indefinitely.** Stakeholder-conditional requirements
  (e.g. R-A-PTS — needs > 1 user) stay in the catalog with an
  explicit blocker note until the blocker clears.

## Authority

The architect of record (see
[`../phase-preliminary/architecture-team.md`](../phase-preliminary/architecture-team.md))
owns the catalog. Adds and deletions land directly in the working
tree without review automation; the convention is the AGENTS.md
chain.

## Anti-patterns explicitly rejected

- **No hierarchical req IDs** (R-1.2.3.4). Flat IDs with phase
  prefix only.
- **No status-flag accumulation.** A row in the catalog is open;
  not-in-the-catalog is closed-or-never-existed. No `Withdrawn`
  / `Deprecated` / `Closed` flags here either, consistent with
  the architecture method.
- **No requirements-tracker tooling.** A markdown table is
  enough at single-architect scale. If catalog grows past ~50
  rows, that's the trigger to revisit (Phase F experiment to
  introduce something — would itself be a req).
- **No requirement without an owner phase.** Every row says
  which phase will address it. Orphan rows get assigned or
  deleted at the next sweep.
