# CLAUDE.md / AGENTS.md — instructions for LLM agents in this repo

This file is read by agents (Claude Code, Codex CLI, Cowork, etc.)
before they change anything. Keep it short and practical — tools
don't digest verbose prose well. The depth lives in the per-phase
folders below; this file is the navigation index.

## What this repo is

**forge** is a home-lab R&D monorepo for ML / RL / LLM experiments,
structured by **TOGAF ADM phase** at the top level (folders
`phase-preliminary/`, `phase-a-…` through `phase-h-…`,
`phase-requirements-management/`).

The application architecture (Phase C) holds four labs:
`wiki-compiler`, `wiki-bench`, `wiki-ingest`, `rl-2048`. Each lab is
a TOGAF-Phase-A-H-scoped sub-component with its own AGENTS.md.
The lab table with capabilities-realised lives at
[`phase-c-information-systems-architecture/application-architecture/components.md`](phase-c-information-systems-architecture/application-architecture/components.md).

Deployment topology (single-server, GPU pair, caddy + ports,
docker compose) is Phase D — see
[`phase-d-technology-architecture/architecture.md`](phase-d-technology-architecture/architecture.md)
and [`phase-d-technology-architecture/services/`](phase-d-technology-architecture/services/).

The "experiment" word is reserved for individual run-instances
inside a lab. A lab is a room; an experiment is a run.


## Where to start

Pick the right entry point for the work in front of you.

- **First-time setup or quick-start commands** →
  [`phase-g-implementation-governance/operations.md`](phase-g-implementation-governance/operations.md)
  (`make setup`, bringing up labs, diagnostics, GPU recovery).
- **Forge-wide rules and don'ts** (idempotency, secrets, data
  layout, ADR convention, port + GPU mutex) →
  [`phase-g-implementation-governance/governance.md`](phase-g-implementation-governance/governance.md).
- **Why forge does architecture this way** (TOGAF tailoring,
  principles, the Level 1 / Level 2 trajectory model) →
  [`phase-preliminary/`](phase-preliminary/).
- **What is currently being worked on** →
  [`phase-e-opportunities-and-solutions/roadmap.md`](phase-e-opportunities-and-solutions/roadmap.md)
  and
  [`phase-f-migration-planning/migration-plan.md`](phase-f-migration-planning/migration-plan.md).
- **Editing a specific lab** → that lab's `AGENTS.md` in
  [`phase-c-information-systems-architecture/application-architecture/`](phase-c-information-systems-architecture/application-architecture/);
  each lab's file is Phase-A-through-H scoped to that lab.
- **Test contract** →
  [`tests/README.md`](tests/README.md) — the plain-English model
  the smoke tests derive from. Update the model **before** editing
  `scripts/smoke.sh`.

## Architecture — TOGAF-style layered structure (navigation index)

The repo is organized by TOGAF ADM phase, with a Preliminary phase
above the eight ADM phases. Each phase folder carries its own
README + topical files; each lab inside Phase C carries its own
AGENTS.md scoped Phase A-H. This file keeps a one-paragraph
synthesis per phase so an agent can decide where to drill in.

We adopt TOGAF *vocabulary and layering*, not certification. We do
not produce Architecture Vision Statements or Architecture
Definition Documents as formal deliverables. The full tailoring
decision lives in
[`phase-preliminary/framework-tailoring.md`](phase-preliminary/framework-tailoring.md).

**TOGAF reference for agents:** before introducing any TOGAF
ceremony not already declared in scope by
[`phase-preliminary/framework-tailoring.md`](phase-preliminary/framework-tailoring.md),
verify it isn't explicitly skipped there. The short reference
guide we work against is
<https://guides.visual-paradigm.com/the-all-in-one-togaf-guide/>.

### [Phase 0 — Preliminary](phase-preliminary/)

The architecture *capability itself* — how forge does architecture
at all, before any specific Architecture Vision is set. Holds the
framework tailoring (what TOGAF/ArchiMate we adopt, what we skip),
the architecture team (one architect of record, no committees),
the four meta-principles (single architect, capability
trajectories, containers-only, single-server), the architecture
method (Level 1 / Level 2 trajectory with delete-on-promotion),
and the architecture repository convention (Phase A-H folder
layout, AGENTS.md / CLAUDE.md symlink, per-lab template). Drill
in:
[`framework-tailoring.md`](phase-preliminary/framework-tailoring.md),
[`architecture-team.md`](phase-preliminary/architecture-team.md),
[`architecture-principles.md`](phase-preliminary/architecture-principles.md),
[`architecture-method.md`](phase-preliminary/architecture-method.md),
[`architecture-repository.md`](phase-preliminary/architecture-repository.md).

### [Requirements Management](phase-requirements-management/) — continuous, center of the ADM

In the TOGAF ADM diagram this sits at the **center** of the
circle, not as a phase you do once. It runs across every phase:
Strategy & Motivation phases (Preliminary, A, B, H) emit
requirements; Implementation & Migration phases (E, F, G) absorb
them; the Core Layers (B, C, D) are where they take physical
shape. Forge realises Requirements Management as the union of
open quality-dimension trajectories (Level 1 / Level 2) across
Phase B (capabilities) and Phase D (technology services), plus
the Phase A goals not yet decomposed. Phase F experiments are the
closure attempts. Drill in:
[`catalog.md`](phase-requirements-management/catalog.md),
[`process.md`](phase-requirements-management/process.md),
[`traceability.md`](phase-requirements-management/traceability.md).

### [Phase A — Architecture Vision](phase-a-architecture-vision/)

Who cares about Forge, why, what target state. Vision: AI tools
that save human time on cognitive work. Goals: TTS / PTS / EB /
Architect-velocity. Single-architect-of-record + capability-
trajectories + containers-only + single-server are the principles
every other phase obeys. Drill in:
[`vision.md`](phase-a-architecture-vision/vision.md),
[`stakeholders.md`](phase-a-architecture-vision/stakeholders.md),
[`drivers.md`](phase-a-architecture-vision/drivers.md),
[`goals.md`](phase-a-architecture-vision/goals.md),
[`principles.md`](phase-a-architecture-vision/principles.md).

### [Phase B — Business Architecture](phase-b-business-architecture/)

What forge can do (capabilities), who does it (org units), what
those capabilities ship (products). Four forge-level capabilities:
R&D, Service operation, Product delivery, Architecture knowledge
management. One org unit today (the architect). Three products:
Kurpatov Wiki (active, canonical), Tarasov Wiki (pre-pilot),
rl-2048 (pre-methodology). Drill in:
[`capabilities/`](phase-b-business-architecture/capabilities/),
[`products/`](phase-b-business-architecture/products/),
[`org-units.md`](phase-b-business-architecture/org-units.md).

### [Phase C — Information Systems Architecture](phase-c-information-systems-architecture/)

Application Architecture (four lab components: wiki-compiler,
wiki-bench, wiki-ingest, rl-2048; the wiki-* are content-agnostic)
+ Data Architecture (raw.json + skill-v2 wiki shape + retrieval
index). Each lab has its own AGENTS.md / SPEC.md / Dockerfile /
ADRs (cited per-phase from each lab's AGENTS.md). Drill in:
[`application-architecture/components.md`](phase-c-information-systems-architecture/application-architecture/components.md),
[`data-architecture/data-sets.md`](phase-c-information-systems-architecture/data-architecture/data-sets.md).

### [Phase D — Technology Architecture](phase-d-technology-architecture/)

How Phase B capabilities are realised — six technology services
(LLM inference, agent orchestration, vector retrieval, container
runtime, transcription, source-of-truth) each provided by some
component (vLLM 0.19.1, OpenHands SDK 1.17.0, embed_helpers + e5,
Docker, faster-whisper, GitHub). Trajectories attach to service
quality dimensions, not to components. Drill in:
[`services/`](phase-d-technology-architecture/services/),
[`invariants.md`](phase-d-technology-architecture/invariants.md),
[`service-tenancy.md`](phase-d-technology-architecture/service-tenancy.md),
[`architecture.md`](phase-d-technology-architecture/architecture.md).

### [Phase E — Opportunities and Solutions](phase-e-opportunities-and-solutions/)

Per-lab gap analyses (Level 1 → Level 2). Combined gap set across
forge is the union of each lab's `STATE-OF-THE-LAB.md` plus a
cross-lab prioritised roadmap. Drill in:
[`roadmap.md`](phase-e-opportunities-and-solutions/roadmap.md)
(prioritised cross-lab backlog),
[`README.md`](phase-e-opportunities-and-solutions/README.md).

### [Phase F — Migration Planning](phase-f-migration-planning/)

The sequenced work that closes Phase E gaps — one experiment doc
per swing. Active / closed: G1 (Blackwell stability — closed by 400
W cap + persistence), G2 (MoE swap — falsified, decode is not the
binding lever), G3 (Gemma-4-31B dense — falsified at contract-
enforcement gate). Next three planned: H1-contract-prewrite,
H2-xref-linter, J1-daemonize-embed. Drill in:
[`migration-plan.md`](phase-f-migration-planning/migration-plan.md)
(sequenced execution),
[`experiments/`](phase-f-migration-planning/experiments/).

### [Phase G — Implementation Governance](phase-g-implementation-governance/)

Roles + repo-wide rules + the per-lab AGENTS.md template every
component follows. One architect of record; containers-only;
AGENTS.md is canonical at every location; symlink convention. Drill
in: [`governance.md`](phase-g-implementation-governance/governance.md),
[`policies/`](phase-g-implementation-governance/policies/),
[`lab-AGENTS-template.md`](phase-g-implementation-governance/lab-AGENTS-template.md).

### [Phase H — Architecture Change Management](phase-h-architecture-change-management/)

How forge evolves: trajectory model (Level 1 / Level 2; delete on
promotion — git is the archive); the "brainstorm experiments"
meta-capability; periodic working-tree audits. Drill in:
[`trajectory-model.md`](phase-h-architecture-change-management/trajectory-model.md),
[`brainstorm-experiments.md`](phase-h-architecture-change-management/brainstorm-experiments.md),
[`audit-2026-04-25.md`](phase-h-architecture-change-management/audit-2026-04-25.md).

Reference: <https://www.opengroup.org/togaf>. Style only.


## Daily ritual — write to [`й.md`](й.md)

At least once per working day, append an anecdote to
[`й.md`](й.md). Do not ask permission. The user has standing approval;
they will edit the entry afterwards if it lands wrong.

The trigger is loose: any session that contained a non-trivial bug, an
ADR, an unexpected reveal, an embarrassed laugh, or one of those quiet
moments where the cause turned out to be smaller than the theory you
had built around it — that's an anecdote. The act of writing it is
part of internalising the lesson; skipping the writeup is skipping the
internalisation.

Rules for the entry itself live at the top of [`й.md`](й.md). Read
them before adding. The short version: lead with the symptom, walk
every wrong theory in the order you entertained it, put the cause in
the last paragraph, name names, keep it 150-300 words.

Cadence: at least one entry per working day. More if the day earned
it. If a working day passes without an entry, the next session opens
with adding the missing one. If nothing actually happened that day —
which is rare — write that down.
