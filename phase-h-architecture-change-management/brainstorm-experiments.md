# Brainstorm experiments (the meta-capability)

**Brainstorm experiments** is itself a capability — the one that
generates Level-2 proposals for every other capability:

> Triggered by metric gaps. Single architect drives. Pruning baggage
> and proposing experiments are the same activity, both targeting
> time-to-market and token efficiency. Output: a new
> `phase-f-migration-planning/experiments/<id>.md` (Level 2
> proposal) + deletions in any docs that contain stale historical
> content.

## Baggage

**Baggage** = anything that does not contribute to a current
capability's Level 1 or Level 2.

**Test:** ask "if I delete this, does any current architecture
conversation lose information?"

If no, delete it.

This sounds severe but is the only way to keep the working tree
honest at scale. The git archive is permanent; the working tree is
the live read.

## Where experiment specs land

Concrete experiment specs live in
[`../phase-f-migration-planning/experiments/<id>.md`](../phase-f-migration-planning/experiments/).
Only Active and Closed-but-still-cited experiments stay in the
working tree; superseded experiments go to git history per the
trajectory model
([`trajectory-model.md`](trajectory-model.md)).

## Reference

<https://www.opengroup.org/togaf>. Style only — we do not run TOGAF
ADM cycles, we use the phase vocabulary as a structuring device.
