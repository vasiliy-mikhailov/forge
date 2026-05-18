# CLAUDE.md / AGENTS.md — instructions for LLM agents in this repo

Read by agents (Claude Code, Codex CLI, Cowork, etc.) before any
change. Keep it short. Depth lives in the per-phase folders; this
file is the navigation index.


## Writing — cross out the excessive words

> Writing is easy. All you have to do is cross out the excessive
> words. — Mark Twain

Master rule. Every other writing rule in this repo derives from
it. Cognitive load is the bottleneck on doing good work; excess
words are the largest controllable source.

- **Code comments**: keep "what" (the line of intent faster
  than re-reading the code). Strip "why" — it lives in the
  spec, ADR, or SOLUTION-ARCHITECTURE. Strip cycle archaeology
  ("Cycle 47: ...") — it lives in git.
- **Specs (test_spec, src_spec, SPEC.md)**: one decision per
  spec. No "out of scope" sections, no anticipatory enumeration,
  no "previously X but cycle N changed it" preambles. Specs
  describe the current decision; git holds the chronology.
- **Architecture docs / ADRs**: current state only. When a
  decision changes, edit the doc — don't append an amendment
  header. Old versions live in git.
- **Commit messages**: as long as needed to capture the why,
  no longer. The CATS RED/GREEN block carries the load; English
  preambles around it stay terse.
- **AGENTS.md / CATS.md / rules docs**: when a rule changes,
  rewrite it. Don't keep both wordings with "but per cycle N
  this was amended" noise.

If you find yourself adding more than a sentence of "why" to a
file with a corresponding spec or ADR, stop. Put the why where
it belongs.

## What this repo is

**forge** is a home-lab R&D monorepo for ML / RL / LLM experiments,
structured by **TOGAF ADM phase** at the top level (`phase-preliminary/`,
`phase-a-…` through `phase-h-…`, `phase-requirements-management/`).

Phase C application architecture holds four labs: `wiki-compiler`,
`wiki-bench`, `wiki-ingest`, `rl-2048`. Each is a TOGAF-Phase-A-H-scoped
sub-component with its own AGENTS.md. Lab table:
[`phase-c-information-systems-architecture/application-architecture/components.md`](phase-c-information-systems-architecture/application-architecture/components.md).

Phase D holds deployment topology (single-server, GPU pair, caddy +
ports, docker compose) —
[`phase-d-technology-architecture/architecture.md`](phase-d-technology-architecture/architecture.md),
[`phase-d-technology-architecture/services/`](phase-d-technology-architecture/services/).

"Experiment" = an individual run-instance inside a lab. A lab is a
room; an experiment is a run.


## Where to start

- **Setup / quick-start** →
  [`phase-g-implementation-governance/operations.md`](phase-g-implementation-governance/operations.md)
  (`make setup`, bringing up labs, diagnostics, GPU recovery).
- **Forge-wide rules and don'ts** (idempotency, secrets, data
  layout, ADR convention, port + GPU mutex) →
  [`phase-g-implementation-governance/governance.md`](phase-g-implementation-governance/governance.md).
- **Why forge does architecture this way** →
  [`phase-preliminary/`](phase-preliminary/).
- **Currently being worked on** →
  [`phase-e-opportunities-and-solutions/roadmap.md`](phase-e-opportunities-and-solutions/roadmap.md),
  [`phase-f-migration-planning/migration-plan.md`](phase-f-migration-planning/migration-plan.md).
- **Editing a specific lab** → that lab's `AGENTS.md` in
  [`phase-c-information-systems-architecture/application-architecture/`](phase-c-information-systems-architecture/application-architecture/).
- **Test contract** → [`tests/README.md`](tests/README.md). Update
  the model **before** editing `scripts/smoke.sh`.
- **Writing implementation code that matches TOGAF docs** →
  [`phase-preliminary/cats.md`](phase-preliminary/cats.md). Per-lab
  application at `<lab>/CATS.md`.

## Connecting to the lab

The lab host is reachable as `mikhailov.tech` (DNS) on port 2222.

**Always use `ssh mikhailov.tech` — never the IP, never a short alias
like `ssh forge`.** Short aliases that resolve to the LAN IP only
work from the operator's home network; agents running elsewhere fail
silently or slowly.

**Always run agents with SSH connection multiplexing enabled.** Without
it, every command pays the full TCP/TLS/auth handshake (~3 s each); a
single CATS cycle is 7–10 SSH calls, so multiplexing is roughly a
10× speedup. Add this to `~/.ssh/config`:

```
Host mikhailov.tech
  HostName mikhailov.tech
  User vmihaylov
  Port 2222
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  StrictHostKeyChecking accept-new
  ControlMaster auto
  ControlPath ~/.ssh/cm/%C
  ControlPersist 10m
```

The first call establishes a master socket under `~/.ssh/cm/`; every
subsequent `ssh mikhailov.tech` or `scp ... mikhailov.tech:...` call
within 10 minutes reuses it (~0.3 s instead of ~3 s). `mkdir -p
~/.ssh/cm` if the directory doesn't exist.

## Architecture — TOGAF-style layered structure (navigation index)

Organized by TOGAF ADM phase, with a Preliminary phase above the eight
ADM phases. Each phase folder carries its own README + topical files;
each Phase C lab carries its own AGENTS.md scoped Phase A-H. One
paragraph per phase below so an agent can decide where to drill in.

We adopt TOGAF *vocabulary and layering*, not certification. No
Architecture Vision Statements or Architecture Definition Documents
as formal deliverables. Full tailoring decision:
[`phase-preliminary/framework-tailoring.md`](phase-preliminary/framework-tailoring.md).
Before introducing any TOGAF ceremony, verify it isn't skipped there.
Reference guide: <https://guides.visual-paradigm.com/the-all-in-one-togaf-guide/>.

### [Phase 0 — Preliminary](phase-preliminary/)

The architecture *capability itself* — how forge does architecture
before any Architecture Vision is set. Framework tailoring (what
TOGAF/ArchiMate we adopt or skip), architecture team (one architect
of record), the four meta-principles (single architect, capability
trajectories, containers-only, single-server), architecture method
(Level 1 / Level 2 trajectory with delete-on-promotion), repository
convention (Phase A-H folder layout, AGENTS.md / CLAUDE.md symlink,
per-lab template). Drill in:
[`framework-tailoring.md`](phase-preliminary/framework-tailoring.md),
[`architecture-team.md`](phase-preliminary/architecture-team.md),
[`architecture-principles.md`](phase-preliminary/architecture-principles.md),
[`architecture-method.md`](phase-preliminary/architecture-method.md),
[`architecture-repository.md`](phase-preliminary/architecture-repository.md).

### [Requirements Management](phase-requirements-management/) — continuous, center of the ADM

Sits at the **center** of the ADM circle, not as a one-shot phase.
Runs across every phase: Strategy & Motivation (Preliminary, A, B, H)
emit requirements; Implementation & Migration (E, F, G) absorb them;
Core Layers (B, C, D) are where they take physical shape. Forge
realises it as the union of open quality-dimension trajectories
(Level 1 / Level 2) across Phase B and Phase D, plus undecomposed
Phase A goals. Phase F experiments are the closure attempts. Drill in:
[`catalog.md`](phase-requirements-management/catalog.md),
[`process.md`](phase-requirements-management/process.md),
[`traceability.md`](phase-requirements-management/traceability.md).

### [Phase A — Architecture Vision](phase-a-architecture-vision/)

Who cares about Forge, why, what target state. Vision: AI tools that
save human time on cognitive work. Goals: TTS / PTS / EB /
Architect-velocity. Principles every other phase obeys:
single-architect-of-record, capability-trajectories, containers-only,
single-server. Drill in:
[`vision.md`](phase-a-architecture-vision/vision.md),
[`stakeholders.md`](phase-a-architecture-vision/stakeholders.md),
[`drivers.md`](phase-a-architecture-vision/drivers.md),
[`goals.md`](phase-a-architecture-vision/goals.md),
[`principles.md`](phase-a-architecture-vision/principles.md).

### [Phase B — Business Architecture](phase-b-business-architecture/)

Capabilities (what forge can do), org units (who), products (what
ships). Four capabilities: R&D, Service operation, Product delivery,
Architecture knowledge management. One org unit (the architect).
Three products: Kurpatov Wiki (active, canonical), Tarasov Wiki
(pre-pilot), rl-2048 (pre-methodology). Drill in:
[`capabilities/`](phase-b-business-architecture/capabilities/),
[`products/`](phase-b-business-architecture/products/),
[`org-units.md`](phase-b-business-architecture/org-units.md).

### [Phase C — Information Systems Architecture](phase-c-information-systems-architecture/)

Application Architecture (four labs: wiki-compiler, wiki-bench,
wiki-ingest, rl-2048; wiki-* are content-agnostic) + Data
Architecture (raw.json + skill-v2 wiki shape + retrieval index).
Each lab has its own AGENTS.md / SPEC.md / Dockerfile / ADRs. Drill in:
[`application-architecture/components.md`](phase-c-information-systems-architecture/application-architecture/components.md),
[`data-architecture/data-sets.md`](phase-c-information-systems-architecture/data-architecture/data-sets.md).

### [Phase D — Technology Architecture](phase-d-technology-architecture/)

How Phase B capabilities are realised. Six services (LLM inference,
agent orchestration, vector retrieval, container runtime,
transcription, source-of-truth) each provided by a component
(vLLM 0.19.1, OpenHands SDK 1.17.0, embed_helpers + e5, Docker,
faster-whisper, GitHub). Trajectories attach to service quality
dimensions, not components. Drill in:
[`services/`](phase-d-technology-architecture/services/),
[`invariants.md`](phase-d-technology-architecture/invariants.md),
[`service-tenancy.md`](phase-d-technology-architecture/service-tenancy.md),
[`architecture.md`](phase-d-technology-architecture/architecture.md).

### [Phase E — Opportunities and Solutions](phase-e-opportunities-and-solutions/)

Per-lab gap analyses (Level 1 → Level 2). Combined gap set = union
of each lab's `STATE-OF-THE-LAB.md` plus a cross-lab prioritised
roadmap. Drill in:
[`roadmap.md`](phase-e-opportunities-and-solutions/roadmap.md)
(prioritised cross-lab backlog),
[`README.md`](phase-e-opportunities-and-solutions/README.md).

### [Phase F — Migration Planning](phase-f-migration-planning/)

Sequenced work that closes Phase E gaps — one experiment doc per
swing. Active/closed: G1 (Blackwell stability — closed by 400 W cap
+ persistence), G2 (MoE swap — falsified), G3 (Gemma-4-31B dense —
falsified at contract-enforcement gate). Planned: H1-contract-prewrite,
H2-xref-linter, J1-daemonize-embed. Drill in:
[`migration-plan.md`](phase-f-migration-planning/migration-plan.md)
(sequenced execution),
[`experiments/`](phase-f-migration-planning/experiments/).

### [Phase G — Implementation Governance](phase-g-implementation-governance/)

Roles, repo-wide rules, per-lab AGENTS.md template. One architect of
record; containers-only; AGENTS.md is canonical at every location;
symlink convention. Drill in:
[`governance.md`](phase-g-implementation-governance/governance.md),
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
[`й.md`](й.md). Do not ask permission — standing approval; the user
edits afterwards if it lands wrong.

Trigger: any session with a non-trivial bug, an ADR, an unexpected
reveal, an embarrassed laugh, or a cause smaller than the theory
built around it. Writing it is internalising the lesson.

Entry rules live at the top of [`й.md`](й.md). Short version: lead
with the symptom, walk every wrong theory in order, put the cause in
the last paragraph, name names, 150-300 words.

If a working day passes without an entry, the next session opens with
adding it. If nothing happened — rare — write that down.


---

## CATS methodology

## Stance

- **Act as a Senior Erlang AI Engineer.** Pure functions over
  stateful processes. Immutability (binaries, tuples, records)
  over mutation. Composition over inheritance. Small, focused
  functions with explicit inputs and outputs. Side effects sit
  at the edges (gen_servers); the core is pure.
- **Constraints are tests, not prose.** Express invariants and
  contracts as TDD-style unit tests, meta-tests (architecture
  shape checks), or live integration tests. Markdown test_spec
  and src_spec ceremony is dead. Erlang -spec attributes carry
  type contracts, EUnit pins behavior, Common Test pins
  integration. The doc explains why; the tests prove what.
- **Prefer fitness functions: constraints, search, verification,
  repair, repeat.** Define what success looks like as a check
  before you start; iterate against the check; verify on each
  pass; repair when the check regresses. Live-runtime tests are
  fitness functions against the real environment.
