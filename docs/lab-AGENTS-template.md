# lab AGENTS.md — canonical template

Every directory in forge (lab or forge root) keeps its agent-context in
`AGENTS.md`, with `CLAUDE.md` as a symlink → `AGENTS.md` so every popular
agent tool finds it. The convention was unified on 2026-04-27 (forge root
used to invert it).

This file is the canonical template. New labs copy it; existing labs
must match the section ordering and wording below. If you change the
template, update every lab AGENTS.md in the same commit.

The Phase headers are the **classic TOGAF ADM** phase names. They are
identical at forge level and lab level — what differs is the *scope*
of the content within each phase, mentioned in the prose, not the
header.

| Phase | Header (used both at forge level and at every lab) |
|---|---|
| A   | `## Phase A — Architecture Vision` |
| B   | `## Phase B — Business Architecture` |
| C   | `## Phase C — Information Systems Architecture` |
| D   | `## Phase D — Technology Architecture` |
| E   | `## Phase E — Opportunities and Solutions` |
| F   | `## Phase F — Migration Planning` |
| G   | `## Phase G — Implementation Governance` |
| H   | `## Phase H — Architecture Change Management` |

(At forge level the file uses `### Phase X` because there's a
top-level `## Architecture` heading wrapping all of them; at lab level
they are `## Phase X` because they sit at the document's top heading
level. The header *text* is identical.)

Below is the canonical lab-level template — copy-paste this into a new
lab's `AGENTS.md` and fill in the `<...>` placeholders.

```markdown
# <lab-slug> — agent context

This file follows the canonical TOGAF ADM Phase A-H structure
(see `forge/docs/lab-AGENTS-template.md`). Read forge-level
`AGENTS.md` first for cross-cutting rules; this file is scoped to
the <lab-slug> lab.

## Phase A — Architecture Vision

Phase A answers *who* cares about this lab as an architecture, *why*
they care, and *what target state* the lab exists to reach. Products
and capability tables go in Phase B, not here.

**Lab role within forge.** <One paragraph: this lab is one of
forge's N org units. It realises the following forge-level
capabilities for the *<domain>* domain: <list of forge capabilities
the lab covers — see forge AGENTS.md Phase B labs table>. It does not
own *<excluded capabilities>* directly; those are realised through
<other labs>.>

**Vision (lab-scoped).** <One sentence: what this lab provides to
the forge mission "Forge builds AI tools that save human time on
cognitive work". A lab-scoped restatement of forge's R&D vision.>

**Lab-scoped stakeholders.** <Who cares about this lab specifically.
Cross-link to forge-level stakeholders (architect of record, future
operator) — don't duplicate them.>

**Lab-scoped drivers.** <What forces motivate the work in this lab.
Examples: GPU instability, transcription volume, single-architect
attention budget.>

**Lab-scoped goals.** <Measurable target states for this lab. These
roll up to forge-level Motivation goals (TTS, PTS, EB,
Architect-velocity).>

**Lab-scoped principles.** <Constraints specific to this lab's
operation. Cross-cutting principles like "containers-only" live in
forge-level Phase A — don't repeat them here.>

## Phase B — Business Architecture

<Subset of forge-level Phase B owned by THIS lab. The lab realises
the relevant rows of the forge-level capability tables. Same format:>

| Capability | Quality dimension |
|------------|-------------------|
| <cap 1>    | <how good is good>|
| <cap 2>    | <...>             |

## Phase C — Information Systems Architecture

<Data the lab produces / consumes / stores on disk: schemas, paths
under ${STORAGE_ROOT}, branch conventions, append-only invariants.
Also application-architecture aspects of the lab if relevant
(internal application components and how they exchange data).>

## Phase D — Technology Architecture

<For every technology service this lab PROVIDES, one block:>

**Service: <service name>** (forge-wide consumer / lab-local)

- Component: <name + version + key config>
- Component: <...>
- L1 (today): <current quality on each relevant dimension —
  throughput, latency, stability, cost>
- L2 (next): <target state, with metric delta>

<For services this lab CONSUMES (e.g. LLM inference for
kurpatov-wiki-bench), cross-link to the providing lab's AGENTS.md
or to forge-level Phase D — do not duplicate the spec here.>

## Phase E — Opportunities and Solutions

<Gap analysis for this lab — which capabilities are not yet at
Level 2. If a `STATE-OF-THE-LAB.md` exists, it is the canonical
gap audit and this section just points at it. Otherwise this
section enumerates the gaps directly.>

## Phase F — Migration Planning

<Sequenced work packages closing the gaps from Phase E.
References to active experiment specs at
`docs/experiments/<id>.md`. Only Active and Closed-but-still-cited
experiments are kept; superseded ones go to git history per
Phase H.>

## Phase G — Implementation Governance

<Bullet list of do / don't specific to THIS lab. Cross-cutting
rules (containers-only, persistence-aware GPU power management,
no secrets in git) live in forge-level AGENTS.md — don't duplicate
them here.>

## Phase H — Architecture Change Management

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| <cap 1>    | <as-is>         | <to-be>        | <expected delta in metric X> |
| <cap 2>    | ...             | ...            | ...                          |

When Level 2 is reached, it becomes the new Level 1; the prior
Level 1 description is **deleted from docs**. Git history keeps
every prior level — that is the archive.

## Cross-references

- Forge-level: `forge/CLAUDE.md` § <relevant phases>
- ADRs: `docs/adr/` (this lab) + `forge/docs/adr/` (cross-lab)
- Active experiment specs: `docs/experiments/<id>.md`
```

## Notes on filling each phase

- **Phase A** is one paragraph. If you can't say what the lab does
  in one paragraph, the lab is not coherent enough yet — split it
  or absorb it elsewhere.
- **Phase B** is a *subset* of forge-level Phase B. Each row in this
  table also appears in forge-level Phase B (or, for a new lab, must
  be added there in the same commit). Capabilities never exist
  *only* in a lab — they're always grounded at the product/strategy
  level upstairs.
- **Phase C** is data + application architecture in classic TOGAF.
  For most labs the data half dominates (schemas, paths, branch
  conventions); the application half is a brief note on internal
  components if any.
- **Phase D** is where ArchiMate vocabulary matters. **Capabilities
  live in Phase B; Technology Architecture is services + components.**
  A service is a *behavior* exposed by tech (what it does for
  consumers above). A component is the *artefact* (vLLM 0.19.1,
  OpenHands SDK 1.17.0, etc.). Trajectories attach to *service
  quality dimensions*, not to components. Replacing a component
  (vLLM 0.19 → 0.20) is the next step on the same trajectory.
- **Phase E vs Phase F.** E is "what gaps exist" (gap audit, often
  via STATE-OF-THE-LAB.md). F is "in what order will we close them"
  (the sequenced experiments). They are conceptually distinct but
  for small labs the F section is mostly a pointer at
  `docs/experiments/`.
- **Phase G** is do / don't, not philosophy. If the rule is
  "containers-only" it goes in forge-level G; if it's
  "GPU 0 hosts compiler OR rl-2048 not both" it goes in compiler's
  G or rl-2048's G (whoever first fails).
- **Phase H trajectories** must be falsifiable. "We will improve X"
  is not a trajectory; "We will move metric M from value V1 to V2
  by experiment E" is.
