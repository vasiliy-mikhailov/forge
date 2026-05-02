# lab AGENTS.md — canonical template

Every directory in forge (lab or forge root) keeps its agent-context
in `AGENTS.md`, with `CLAUDE.md` as a symlink → `AGENTS.md` so every
popular agent tool finds it. The convention was unified on 2026-04-27
(forge root used to invert it).

This file is the canonical template. New labs copy it; existing labs
must match the section ordering and wording below. If you change the
template, update every lab AGENTS.md in the same commit.

The Phase headers are the **classic TOGAF ADM** phase names. They
are identical at forge level and lab level — what differs is the
*scope* of the content within each phase, mentioned in the prose,
not the header.

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
top-level `## Architecture` heading wrapping all of them; at lab
level they are `## Phase X` because they sit at the document's top
heading level. The header *text* is identical.)

## Where ADRs live

ADRs are scoped to the phase whose decision they capture. Each phase
section in a lab AGENTS.md lists the ADRs whose decision belongs to
that phase, with a relative link.

- Lab-scoped ADRs live in the lab folder under either
  `<lab>/docs/adr/NNNN-*.md` or `<lab>/adr/NNNN-*.md`. Either path
  is legal as long as the AGENTS.md links to the actual file.
- Forge-level ADRs live in `forge/phase-<x>-…/adr/NNNN-*.md`.
  Cross-link from a lab Phase section when the forge-level ADR is
  relevant to that lab.

There is no `forge/docs/adr/` — that path is *historical*. Anything
referenced under that name in older docs is stale and should be
updated to `forge/phase-<x>/adr/`.

Below is the canonical lab-level template — copy-paste this into a
new lab's `AGENTS.md` and fill in the `<...>` placeholders.

```markdown
# <lab-slug> — agent context

This file follows the canonical TOGAF ADM Phase A-H structure
(see `forge/phase-g-implementation-governance/lab-AGENTS-template.md`).
Read forge-level `AGENTS.md` first for cross-cutting rules; this
file is scoped to the <lab-slug> lab.

## Phase A — Architecture Vision

Phase A answers *who* cares about this lab as an architecture,
*why* they care, and *what target state* the lab exists to reach.
Products and capability tables go in Phase B, not here.

**Lab role within forge.** <One paragraph: this lab is one of
forge's N application components. It realises the following
forge-level capabilities for the *<domain>* domain: <list of forge
capabilities the lab covers — see forge AGENTS.md Phase B
capabilities table>. It does not own *<excluded capabilities>*
directly; those are realised through <other labs>.>

**Vision (lab-scoped).** <One sentence: what this lab provides to
the forge mission "Forge builds AI tools that save human time on
cognitive work". A lab-scoped restatement of forge's R&D vision.>

**Lab-scoped stakeholders.** <Who cares about this lab specifically.
Cross-link to forge-level stakeholders (architect of record, future
operator) — don't duplicate them.>

**Lab-scoped drivers.** <What forces motivate the work in this lab.
Examples: GPU instability, transcription volume, single-architect
attention budget.>

**Lab-scoped goals.** <Measurable target states for this lab.
These roll up to forge-level Motivation goals (TTS, PTS, EB,
Architect-velocity).>

**Lab-scoped principles.** <Constraints specific to this lab's
operation. Cross-cutting principles like "containers-only" live in
forge-level Phase A — don't repeat them here.>

**ADRs (Phase A scope).** <Bulleted list of this lab's ADRs whose
decision belongs to Phase A — vision-level scope changes. Often
empty. Cross-link forge-level Phase A ADRs from
`forge/phase-a-architecture-vision/adr/` if any apply.>

## Phase B — Business Architecture

<Subset of forge-level Phase B owned by THIS lab. The lab realises
the relevant rows of the forge-level capability tables. Same
format:>

| Capability | Quality dimension |
|------------|-------------------|
| <cap 1>    | <how good is good>|
| <cap 2>    | <...>             |

**ADRs (Phase B scope).** <Lab ADRs about *what* the lab can do —
new product / capability decisions. Cross-link
`forge/phase-b-business-architecture/adr/` if any forge-level
business-arch ADR applies.>

## Phase C — Information Systems Architecture

<Data the lab produces / consumes / stores on disk: schemas, paths
under `${STORAGE_ROOT}`, branch conventions, append-only
invariants. Also application-architecture aspects of the lab if
relevant (internal application components and how they exchange
data).>

**ADRs (Phase C scope).** <Lab ADRs about data shape, on-disk
layout, branch conventions, internal application-architecture
splits. Cross-link
`forge/phase-c-information-systems-architecture/adr/` if any.>

## Phase D — Technology Architecture

<For every technology service this lab PROVIDES, one block:>

**Service: <service name>** (forge-wide consumer / lab-local)

- Component: <name + version + key config>
- Component: <...>
- L1 (today): <current quality on each relevant dimension —
  throughput, latency, stability, cost>
- L2 (next): <target state, with metric delta>

<For services this lab CONSUMES (e.g. LLM inference for
wiki-bench), cross-link to the providing lab's AGENTS.md or to
forge-level Phase D — do not duplicate the spec here.>

**ADRs (Phase D scope).** <Lab ADRs about technology choices,
component versions, vendor selection. This is usually the largest
ADR list in a lab. Cross-link
`forge/phase-d-technology-architecture/adr/` for forge-wide tech
decisions that apply.>

## Phase E — Opportunities and Solutions

<Gap analysis for this lab — which capabilities are not yet at
Level 2. If a `STATE-OF-THE-LAB.md` exists, it is the canonical
gap audit and this section just points at it. Otherwise this
section enumerates the gaps directly.>

**ADRs (Phase E scope).** <Lab ADRs about gap-prioritisation
methodology, if any. Most labs have none here.>

## Phase F — Migration Planning

<Sequenced work packages closing the gaps from Phase E.
References to active experiment specs at
`<lab>/docs/experiments/<id>.md` (or `<lab>/experiments/<id>.md`
if that flatter layout is used). Only Active and
Closed-but-still-cited experiments are kept; superseded ones go to
git history per Phase H.>

**ADRs (Phase F scope).** <Lab ADRs about migration sequencing /
experiment-design conventions. Cross-link
`forge/phase-f-migration-planning/adr/` if any forge-level migration
ADR applies.>

## Phase G — Implementation Governance

<Bullet list of do / don't specific to THIS lab. Cross-cutting
rules (containers-only, persistence-aware GPU power management,
no secrets in git) live in forge-level AGENTS.md — don't
duplicate them here.>

**ADRs (Phase G scope).** <Lab ADRs about local rules, dispatcher
conventions, per-lab Make/CI shape. Cross-link
`forge/phase-g-implementation-governance/adr/` for forge-wide
governance ADRs.>

## Phase H — Architecture Change Management

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| <cap 1>    | <as-is>         | <to-be>        | <expected delta in metric X> |
| <cap 2>    | ...             | ...            | ...                          |

When Level 2 is reached, it becomes the new Level 1; the prior
Level 1 description is **deleted from docs**. Git history keeps
every prior level — that is the archive.

**ADRs (Phase H scope).** <Lab ADRs about how this lab manages
trajectory promotion / deletion. Most labs have none here; the
forge-level Phase H is the source of truth.>

## Cross-references

- Forge-level: [`forge/AGENTS.md`](../../../../AGENTS.md) §
  <relevant phases>.
- Forge-level Phase folders:
  [`phase-a`](../../../../phase-a-architecture-vision/),
  [`phase-b`](../../../../phase-b-business-architecture/),
  [`phase-c`](../../../../phase-c-information-systems-architecture/),
  [`phase-d`](../../../../phase-d-technology-architecture/),
  [`phase-e`](../../../../phase-e-opportunities-and-solutions/),
  [`phase-f`](../../../../phase-f-migration-planning/),
  [`phase-g`](../../../../phase-g-implementation-governance/),
  [`phase-h`](../../../../phase-h-architecture-change-management/).
- Active experiment specs: `<lab>/docs/experiments/<id>.md`
  (or `<lab>/experiments/<id>.md` if flatter).
```

## Notes on filling each phase

- **Phase A** is one paragraph. If you can't say what the lab does
  in one paragraph, the lab is not coherent enough yet — split it
  or absorb it elsewhere.
- **Phase B** is a *subset* of forge-level Phase B. Each row in
  this table also appears in forge-level Phase B (or, for a new
  lab, must be added there in the same commit). Capabilities
  never exist *only* in a lab — they're always grounded at the
  product/strategy level upstairs.
- **Phase C** is data + application architecture in classic TOGAF.
  For most labs the data half dominates (schemas, paths, branch
  conventions); the application half is a brief note on internal
  components if any.
- **Phase D** is where ArchiMate vocabulary matters.
  **Capabilities live in Phase B; Technology Architecture is
  services + components.** A service is a *behavior* exposed by
  tech (what it does for consumers above). A component is the
  *artefact* (vLLM 0.19.1, OpenHands SDK 1.17.0, etc.).
  Trajectories attach to *service quality dimensions*, not to
  components. Replacing a component (vLLM 0.19 → 0.20) is the next
  step on the same trajectory.
- **Phase E vs Phase F.** E is "what gaps exist" (gap audit,
  often via STATE-OF-THE-LAB.md). F is "in what order will we
  close them" (the sequenced experiments). They are conceptually
  distinct but for small labs the F section is mostly a pointer
  at the lab's experiments folder.
- **Phase G** is do / don't, not philosophy. If the rule is
  "containers-only" it goes in forge-level G; if it's
  "GPU 0 hosts compiler OR rl-2048 not both" it goes in compiler's
  G or rl-2048's G (whoever first fails).
- **Phase H trajectories** must be falsifiable. "We will improve
  X" is not a trajectory; "We will move metric M from value V1 to
  V2 by experiment E" is.

## Notes on ADR placement

- **One ADR captures one decision.** It belongs to the phase
  whose layer the decision changes. Examples:
  - "Switch from cron to a fanotify watcher for ingest" — Phase D
    (technology choice).
  - "Append-only `raw.json` shape with whisper segments" — Phase C
    (data architecture).
  - "Two-layer vault: separate transcribe + push" — Phase D
    (component split).
  - "Per-lab Makefile dispatcher" — Phase G (governance /
    convention).
  - "vLLM as the public OpenAI-compatible endpoint" — Phase D
    (technology service realisation).
- **An ADR can be cross-listed** in two phases if it spans
  layers, but pick the *primary* phase (the layer the decision
  most strongly changes) and cite it from the other phase as a
  link rather than duplicating.
- **Numbering is per scope.** Lab ADRs number from 0001 within
  the lab; forge-level ADRs number from 0001 across all forge
  phases (the existing 0001-0009 series).


## Motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: every lab AGENTS.md must follow the same
  Phase A-H structure; the template enforces uniformity.
- **Goal**: Architect-velocity (lab onboarding) + audit
  reliability (P9 walks lab AGENTS.md headers).
- **Outcome**: 4 lab AGENTS.md (rl-2048, wiki-bench,
  wiki-compiler, wiki-ingest) all present + audit-walked.
- **Capability realised**: Architecture knowledge management.
- **Function**: Define-lab-AGENTS-md-structure.
- **Element**: this file.
