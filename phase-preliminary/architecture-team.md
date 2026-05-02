# Architecture team

The team that produces forge's architecture artefacts and decides
what changes.

## Today

**One person — the architect of record.** This is the same person
as the repo owner. They are the sole driver of trajectory changes,
the sole reviewer, and today the only consumer of every output.

There is **no committee, no formal review process** beyond the
AGENTS.md conventions. There is no Architecture Board, no
Architecture Review Board, no Change Advisory Board.

The architect's *future self* is treated as a real stakeholder
(see [`../phase-a-architecture-vision/stakeholders.md`](../phase-a-architecture-vision/stakeholders.md))
because most of what is written into the repo is for them.

## Implications

- **No PR review automation.** The convention is the AGENTS.md per
  location, not a tool gate.
- **One-line decisions can land directly.** If a change is small,
  reversible, and obviously consistent with the relevant phase's
  principles, it goes in. ADRs are reserved for *irreversible* or
  *layer-changing* decisions.
- **Velocity is a goal, not a side-effect.** Architect-velocity
  (capability advances per architect-hour) is a Phase A goal
  precisely because the team is one person. Anything
  that adds friction to the architect's edit-test loop is a
  candidate for removal.

## When this changes

Re-open the Preliminary Phase if:

- A second architect joins. Then governance becomes non-trivial
  and a written agreement on decision rights is needed.
- An external operator inherits the platform. Then the future-
  operator stakeholder ceases to be hypothetical and the team
  expands.
- An external consumer pays for output. Then governance has to
  represent the consumer's interest formally.

None of these is true today. Until one becomes true, the team
section is "one architect; no boards."


## Measurable motivation chain (OKRs)
Per [P7](architecture-principles.md):

- **Driver**: P1 (single architect of record) needs a
  team-composition declaration (today: one architect, several
  LLM-agent-filled roles).
- **Goal**: Architect-velocity (no implicit roles).
- **Outcome**: roles + actors enumerated; org-units.md cross-
  references this.
- **Measurement source**: n/a — declarative: roles + actors enumeration (org-units in Phase B carries the live activation pointer)
- **Capability realised**: Architecture knowledge management.
- **Function**: Define-the-architecture-team.
- **Element**: this file.
