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
- **Writing implementation code that has to match TOGAF
  documents** (any lab) →
  [`phase-preliminary/cats.md`](phase-preliminary/cats.md)
  — the test-spec-driven cycle that bridges architecture documents
  (Phase A vision, Phase C SPECs, ADRs) to runnable code.
  Per-lab application lives at `<lab>/CATS.md` and references the
  forge-wide methodology.

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


---

## CATS methodology (inlined from `phase-preliminary/cats.md`)

**Keep in sync** with the canonical copy at
[`phase-preliminary/cats.md`](phase-preliminary/cats.md).
Drift is a defect; when one file changes, update the other. CATS is
the test-spec-driven cycle every implementation cycle in this repo
follows.

# CATS methodology — bridging TOGAF documents to robust implementation (clean architecture test specs)

Read this before writing implementation code in any forge lab.

## What this connects

TOGAF documents (Phase A vision, Phase B business architecture, Phase
C information systems architecture, ADRs, per-lab SPEC.md files)
describe **what** the system should do. This file describes **how** an
agent (human or LLM) turns those documents into code without losing
fidelity.

The connection is test-first. Tests pin the contract that documents
promise. Code exists only to make tests pass. Spec describes only what
tests prove.

## The CATS cycle (one iteration)

Do all eleven steps for ONE test case, then start the next.

  1. Pick the next behavior that advances the TOGAF documents under
     implementation (vision, capability, ADR, SPEC.md). Smallest unit
     that adds value is usually right; avoid scoping a single cycle
     beyond what fits in one paragraph of src-spec. Confirm scope with
     the user when ambiguous.
  2. Add an entry to the tests-spec file. Not a one-liner — the entry
     must carry enough detail to reconstruct the test if the test code
     is lost. Format:

         test_when_X_then_Y
           Arrange: what fixture / inputs the test sets up.
           Act:     what call / interaction the test makes.
           Assert:  what property of the result the test checks.

     The when-clause maps to Arrange + Act; the then-clause maps to
     Assert. The entry IS the contract; test code is its embodiment.
  3. Extend the matching src-spec only as far as the new test demands.
     The src-spec describes exactly what tests prove. Nothing else.
     No 'Out of scope' / 'deferred' / 'future' enumeration —
     anything not in the spec is implicitly not yet specified.
  4. Write ONE pytest function in test_<module>.py using Arrange /
     Act / Assert. Function name matches the test case name from
     step 2.
  5. Run pytest. Red expected.
  6. Write the minimum code to make it green. Do NOT add validation,
     type coercion, error handling, or any other behavior beyond what
     the test asserts.
  7. Run the just-added test. Green.
  8. Refactor while green. The four artifacts that can rot — tests-spec, src-spec,
     test code, implementation code — are all in scope:
       - tests-spec: collapse near-duplicate entries; tighten names
         that drifted from the test_when_X_then_Y form.
       - src-spec: trim overpromises (anything no test exercises),
         consolidate paragraphs.
       - test code: extract duplicated arrange blocks into helpers
         or fixtures; rename for clarity.
       - implementation code: extract duplication, simplify structure,
         improve naming.
     The refactor must NOT change any observable behavior; no new test
     should be passing or failing because of it, and no src-spec or
     tests-spec promise should change.
  9. Run the IMPACTED test scope per **test impact analysis (TIA)**
     — every test connected to the code you touched. "Connected"
     means: the test imports a module you modified, or imports a
     module that transitively imports one you modified. Confirm
     every previously-green test in that connected set is still
     green. If any regressed, the refactor was not behavior-
     preserving — revert and try again.

     The FULL suite is a coarser gate, NOT a per-cycle gate. It runs
     before pushing a chain of cycles, at session boundary, in CI,
     and on a schedule. The reason for the relaxation: when the
     suite includes live-LLM tests (single test = 5+ minutes), a
     full-suite gate every cycle either freezes the cadence or
     drives the agent to silently skip slow tests (the worst
     outcome). The full-suite gate at coarser intervals catches
     cross-module drift TIA misses; TIA catches everything the
     immediate change breaks.

     Implementations of TIA:
       - **Manual**: agent identifies imports of changed modules,
         runs `pytest` against the matching test files. Works for
         small repos and clean module graphs.
       - **Tool-assisted**: tools like `pytest-testmon` track
         per-test coverage maps across runs and replay only tests
         whose coverage intersects the diff.
       - **Static**: ast-walk the test tree to build a
         test-file -> imports graph, intersect with the
         changed-files set, run intersection.

     Pragmatic guidance:
       - When uncertain whether a test is connected, include it.
       - Before `git push` of a chain of cycles, run the FULL suite.
         The push is the escape-from-local moment; that's where the
         wider gate applies.
       - Document the TIA scope chosen in the commit message under
         the step-11 coverage report — readers can audit whether the
         choice was reasonable.
  10. Commit and push. Only after step 9 reports the entire suite
      green. Message names the cycle and the test case so the trace
      is reproducible when context collapses. Push to origin so the
      remote stays in sync with each cycle — otherwise commits pile
      up locally and the user cannot see them.
  11. Report progress. After the commit, surface:
        - the TOGAF documents under implementation (SPEC.md, ADRs,
          capability docs) being driven by this work
        - approximate coverage percent of each document (count tested
          requirements / total enumerated requirements)
        - estimated time to complete remaining cycles for the current
          document, broken down by cycle if possible
        - the next cycle name + its planned scope
      The report makes the gap between TOGAF promises and tested
      reality auditable. A document at 100% coverage is fully
      validated by tests; everything else is still aspirational.

## Discipline rules

- src-spec describes only what tests prove. Anything in a src-spec file
  that no test exercises is a lie. Delete it — no 'Out of scope'
  section, no anticipatory enumeration. Spec grows only as tests grow.
- One test case per cycle. Do not pre-write large test enumerations
  — they accrete unverified speculation.
- Test names are sentences: test_when_X_then_Y. One when-clause,
  one then-clause. If the name has two whens or two thens, split.
- Test bodies are Arrange / Act / Assert with those literal comments.
  Three blocks.
- No code without a failing test. If the cycle requires touching
  implementation without a corresponding red test, stop and pick a
  smaller behavior.
- Each commit covers exactly one cycle. The diff should be readable
  in one screen.

## Suggested folder layout per lab

  <lab>/
    SPEC.md                            lab functional spec — the document UNDER
                                       implementation (TOGAF-facing; what the
                                       lab promises to do for its capability).
    AGENTS.md                          operator interface
    src-spec/                         CODE-facing functional specs. Two-level
                                       hierarchy: <layer>/<source_file>/.
                                       First level is the clean-arch layer
                                       (entities, use_cases, adapters,
                                       frameworks, plus lab-specific groupings
                                       such as architecture, clean_arch).
                                       Second level is the python module name
                                       under test (e.g. agent_loop, parser,
                                       score_submission). Inside, ONE file PER
                                       BEHAVIOR; filename mirrors the test:
                                         src_spec_when_X_then_Y.md
                                       so the file IS the contract for that
                                       behavior. No roll-up file per feature.
      <layer>/<source_file>/src_spec_when_X_then_Y.md
    tests-spec/                        CODE-facing test case specs. Same
                                       two-level hierarchy as src-spec/:
                                       <layer>/<source_file>/. ONE file PER
                                       TEST; filename mirrors the test:
                                         test_spec_when_X_then_Y.md
                                       Holds the Arrange / Act / Assert contract
                                       for that single test, written per step 2.
                                       No roll-up file per feature.
      <layer>/<source_file>/test_spec_when_X_then_Y.md
    tests/                             pytest implementations of tests-spec/.
      test_<module>.py
    src/                               clean implementation, generated to
                                       satisfy src-spec/. Symmetric to
                                       tests/ which satisfies tests-spec/.
      <module>.py

## Test file mirrors source file

A pytest file in `tests/` is named `test_<module>.py` for the exact
`<module>.py` it covers in `src/`. One source file → one test
file. The mirroring is required so coverage is traceable by file:

    src/<area>/inference.py            covered by
    tests/<area>/test_inference.py

    src/<area>/parser.py               covered by
    tests/<area>/test_parser.py

A test file may hold many `test_when_X_then_Y` functions; what is
forbidden is grouping tests that span multiple source files into one
`test_<feature>.py` or `test_end_to_end.py`. End-to-end coverage
emerges from the union of per-module test files plus shared fixtures,
not from a separate \end_to_end\ file.

The per-behavior naming for spec files (test_spec_when_X_then_Y.md,
src_spec_when_X_then_Y.md) and the per-module naming for test code
(test_<module>.py) coexist: each test function maps 1:1 to a
test_spec_when_X_then_Y.md file, but the .py file it lives in is
chosen by which src/ module it exercises.

## Spec folder hierarchy mirrors clean-arch + source layout

Spec files do NOT live as a flat list. They live in a two-level
hierarchy:

    src-spec/<layer>/<source_file>/src_spec_when_X_then_Y.md
    tests-spec/<layer>/<source_file>/test_spec_when_X_then_Y.md

First level (`<layer>/`) is the clean-arch layer the source code lives
in. Under `src/` and `src-spec/`, the ONLY allowed first-level folders
are the four canonical clean-arch layers: `entities/`, `use_cases/`,
`adapters/`, `frameworks/`. Under `tests/` and `tests-spec/`, the same
four layers are allowed plus two cross-cutting test groups:
`architecture/` (ast-walking dependency-direction tests) and
`clean_arch/` (layered wire-up tests that span multiple layers).

Feature-bundle folders at the first level (`tier1/`, `bench/`,
`myfeature/`) are a violation. They re-introduce the mixed-concerns
problem clean architecture is supposed to prevent — a `tier1/` that
contains HTTP, parsing, file IO and business logic in one folder
hides exactly the seam an architectural test should pin. Decompose
such bundles into the four layers immediately; the architectural test
specs then make the dependency direction enforceable.

Second level (`<source_file>/`) is the python module name under test
— the bare module stem, no `.py` extension, no `test_` prefix. For
`src/<layer>/parser.py`, specs live under `src-spec/<layer>/parser/`
and `tests-spec/<layer>/parser/`.

Example:

    src/use_cases/score_submission.py
      <-> src-spec/use_cases/score_submission/src_spec_*.md
      <-> tests-spec/use_cases/score_submission/test_spec_*.md
      <-> tests/use_cases/test_score_submission.py

    src/adapters/game_board_2048.py
      <-> src-spec/adapters/game_board_2048/src_spec_*.md
      <-> tests-spec/adapters/game_board_2048/test_spec_*.md
      <-> tests/adapters/test_game_board_2048.py

### Cross-cutting test folders (architecture/, clean_arch/)

The two cross-cutting test folders pin properties of the codebase
itself, not a single source file. There is no "source file under
test" for an ast-walking dependency-direction test or a layered
wire-up test. The second-level name therefore uses the **test file
stem with the `test_` prefix dropped** — the same drop-the-`test_`
rule, applied to the test file when there is no source file to point
at.

Example:

    tests/architecture/test_dependency_direction.py
      <-> tests-spec/architecture/dependency_direction/test_spec_*.md

    tests/clean_arch/test_score_submission_wired.py
      <-> tests-spec/clean_arch/score_submission_wired/test_spec_*.md

The result: tests-spec/ is ALWAYS two levels deep. A test spec
sitting directly under tests-spec/<layer>/ with no per-source-file
folder is a violation, regardless of whether the layer is a clean-arch
layer or a cross-cutting test group. The rule applies uniformly.

The hierarchy buys three things:

  - Directory listing answers "what specifies module X?" with one
    `ls src-spec/<layer>/<module>/` — no grep.
  - Architectural test specs and behavioral specs live in distinct
    layer folders, so cross-cutting concerns don't pollute per-module
    folders.
  - A new layer or a new module shows up as a new folder, not a
    naming-convention violation buried in a long flat list. The
    structure makes the four clean-arch layers visible without
    reading the code.

## Single-module vs multi-module monolith

A lab is one of two shapes:

**Single-module.** The whole lab is one clean-arch unit. `src/` is
the unit's root; its direct children are exactly the four canonical
layers.

    src/
      entities/
      use_cases/
      adapters/
      frameworks/

**Multi-module.** The lab contains multiple bounded contexts, each a
self-contained clean-arch unit. `src/` is no longer a unit; it is a
container of modules. Each module is itself a clean-arch unit with
its own four canonical layers.

    src/
      <module_a>/
        entities/
        use_cases/
        adapters/
        frameworks/
      <module_b>/
        entities/
        use_cases/
        adapters/
        frameworks/

Concrete example — reward-bench (the orchestrator) running tier1,
tier2, tier3 as separate evaluation pipelines:

    src/
      reward_bench/        orchestrator module
        entities/          BenchRun, ModelTarget, TierConfig
        use_cases/         RunBench, SelectTier, AggregateLeaderboard
        adapters/          TierAdapter implementations, leaderboard
                           presenters, swipe-store adapters
        frameworks/        CLI entry point, scheduler, DB driver
      tier1/               one specific evaluation tier
        entities/          AttemptResult, Submission, Iteration, Swipe
        use_cases/         ScoreSubmission, IterateToSubmission
        adapters/          ParserAdapter, GameBoardAdapter,
                           VllmChatAdapter, PythonModuleLoader
        frameworks/        docker provisioner, vLLM HTTP driver
      tier2/               another tier (control-minecraft, etc.)
        ...

Both shapes coexist with the same spec hierarchy: in single-module
mode, specs live under `src-spec/<layer>/<source_file>/`. In
multi-module mode, specs live under
`src-spec/<module>/<layer>/<source_file>/`. The rule is: the spec
folder structure mirrors the source folder structure exactly.

### Module-to-module dependency rules

Modules form a hierarchy. The lab's outermost module is the
orchestrator that composes the others; the inner modules are
specialised bounded contexts. The same dependency rule that holds
within a module (outer-layer-depends-on-inner-layer) holds between
modules (outer-module-depends-on-inner-module):

  - An outer module may import the **public API** of an inner module
    — its `entities/` and its `use_cases/`. These are the module's
    contract.
  - An outer module may NEVER import the **internals** of an inner
    module — its `adapters/` or `frameworks/`. Those are private to
    the inner module; reaching past the contract breaks the seam.
  - An inner module NEVER imports from an outer module. The tier
    must not know the orchestrator exists; this is what lets the
    tier ship independently.
  - Peer modules (tier1 and tier2) NEVER import from each other.
    Both are inner to the orchestrator; both expose use_cases the
    orchestrator composes. Tier-to-tier coupling is always routed
    through the orchestrator.

Cycles between modules are a hard violation. If two modules need to
share types, those types belong in a third inner module (often a
`shared/` or `kernel/` module) that both depend on, never in either
of the two.

## Spec files are Markdown

Both `src_spec_*.md` and `test_spec_*.md` files MUST be valid
Markdown. They render on GitHub, on local previewers, in IDE side
panels — readers depend on that rendering to navigate the spec.

Concrete rules:

- Paragraph breaks need a blank line. Soft line wraps inside a
  paragraph collapse to a single line.
- Test names, file paths, environment variable names, HTTP verbs,
  and inline code go in backticks.
- Test-spec entries use a heading per test case (`### \`test_when_X_then_Y\``)
  followed by bulleted `**Arrange**` / `**Act**` / `**Assert**`
  blocks. The bullets render as a definition-list-like structure
  on GitHub.
- Tables are appropriate for enumerating layers, fields, fixtures.
- Cross-references between spec files use Markdown link syntax
  (relative paths) so navigation works in any renderer.

The reason: a spec file that fails to render is a spec file the
agent and the user cannot read. Plain-text-with-indentation that
collapses in Markdown is a near-invisible drift.

## File naming convention

Per-behavior spec files are named after the test they justify:

    src-spec/<layer>/<source_file>/src_spec_when_X_then_Y.md
    tests-spec/<layer>/<source_file>/test_spec_when_X_then_Y.md

ONE file per test case. The filename IS the contract; reading the
directory listing tells the agent immediately which test the file
backs. Do NOT bundle multiple test specs into one file per feature
— small per-behavior files are easier to scan, link to, and refactor.
No roll-up index file at the directory root is needed — folder
structure + per-behavior filenames are enough. Trying to maintain a
separate "index" or "end_to_end" file just adds another rotting
artifact that drifts from the actual per-behavior files.

The corresponding test code and implementation code files use:

    tests/<area>/test_<module>.py
    src/<area>/<module>.py

A test code file may contain multiple test functions; one per
test_spec_when_X_then_Y.md. The src code is whatever satisfies the
collected src_spec_when_X_then_Y.md files in that area.

## Implementation ADRs — between SPEC.md and test_spec

A `test_spec_when_X_then_Y.md` pins ONE behavior in 30-300 words.
`SPEC.md` describes the lab's promise to its TOGAF capability in
hundreds of lines. Between those two layers there is a third: the
**architectural decisions** that shape how the lab is built — too
detailed for SPEC.md but too cross-cutting for any single test_spec.
Those decisions live as **implementation ADRs** at
`<lab>/docs/adr/NNNN-short-slug.md`.

Each implementation ADR captures:

- **Status** — Accepted (date) | Superseded by ADR-NNN | Deprecated.
- **Context** — what forced the decision; what observations or
  prior decisions led to it.
- **Decision** — the one-sentence position. Specific enough that an
  agent reading it knows what code to write.
- **Consequences** — positive AND negative; what reverting would
  cost.
- **Alternatives considered** — each named and briefly rejected.
- **Implementation pointers** — files/cycles that realise the
  decision (or are planned to).

Implementation ADRs have **lab-local numbering** (own sequence
starting at `0001`), distinct from forge-wide ADRs in
`phase-preliminary/adr/`. The forge-wide sequence captures decisions
that affect multiple labs; the lab-local sequence captures decisions
that affect one lab only.

### When to write an implementation ADR

Write one BEFORE the cycle that realises the decision, not after.
Symptoms that an ADR is overdue:

- You're about to write a test_spec but you keep typing "we chose X
  because Y" into the spec body instead of the behavior contract.
- The decision is referenced (or contradicted) by `_bak/` legacy
  code and you want the new direction recorded for the audit trail.
- Two reasonable implementations fit the SPEC.md text and you need
  to pin which one was chosen.
- The cycle ahead will write production code that's hard to revert
  without losing context.

In each case: pause the test_spec cycle, write the ADR, commit it,
THEN start the cycle that realises it. The test_spec then references
the ADR by relative path; readers chase the link if they need the
rationale.

### Example

`reward-bench` faced "the condenser uses the same model as the model
under bench, or a separate smaller one?". SPEC.md mentioned "a
condenser" without committing to either; the legacy `_bak/` used a
separate model. The decision was made AS AN ADR
(`reward-bench/docs/adr/0001-condenser-uses-same-model-as-bench.md`)
BEFORE the cycle that wires the condenser. The ADR's Implementation
pointers section names the cycles that will realise it.

## Two layers of code-facing spec, one TOGAF document under implementation

  - SPEC.md at the lab root is the document under implementation. It
    is TOGAF-facing (what the lab measures, what its tiers are, what
    its outputs are). Coverage of SPEC.md is the report from step 11.

  - src-spec/ and tests-spec/ are both code-facing artifacts. They
    describe and verify code, not the TOGAF promise. The symmetry
    matters: every entry in tests-spec/ should be derivable from
    src-spec/ and SPEC.md, and every line of src/ code should be
    derivable from src-spec/ + tests-spec/.

  - When SPEC.md changes (TOGAF document amended), src-spec/ may
    need to follow, which triggers tests-spec/ updates, which trigger
    tests, which trigger code. The propagation chain works in either
    direction.

## Reverse-engineering legacy code

When a lab has legacy code that drifted from src-spec / SPEC.md, move it to a
quarantined directory (per-lab convention — see lab AGENTS.md / CATS.md)
and rebuild from tests via the cycle above. Rules:

  - Read the quarantined code to learn its observable behavior; do not
    import from it.
  - New code has no dependency on the quarantined code.
  - Each green cycle frees a slice of the quarantined code to delete.

Lab-specific quarantine paths and reverse-engineering notes live in
each lab's own CATS.md.

## When to stop a cycle and ask the user

- A behavior in legacy code is clearly a bug. Decide whether to pin
  it (preserve) or fix it (clean impl diverges from legacy).
- Two reasonable behaviors fit the test case. Ambiguity needs human
  resolution.
- The next smallest case requires infrastructure you do not yet have.
  Decide whether to build the infrastructure first or shrink the
  scope further.
- The cycle touches an architectural concern not yet in TOGAF
  documents. Amend the relevant TOGAF doc *before* writing code.

## Why this works as a TOGAF bridge

TOGAF separates architecture (what + why) from implementation (how).
Without discipline the gap leaks: src/ drifts from src-spec, src-spec
drifts from src/, both drift from the documented TOGAF vision. The
chain SPEC.md → src-spec → tests-spec → tests → src/ keeps every
layer auditable from any other. A change to a TOGAF document (SPEC.md)
forces a change to src-spec, which forces a change to tests-spec,
which forces a change to tests, which forces a change to src/, which
surfaces in a commit. The cycle works in reverse too — a bug in src/
forces a regression entry in tests-spec, which forces an src-spec
amendment, which may force a SPEC.md amendment.

## Per-lab adoption

Each lab that follows this methodology should keep its lab-specific
conventions in <lab>/CATS.md and reference this document at the top.
The lab-specific file enumerates lab-only choices (module names,
specific reverse-engineering scope, lab-specific 'when to ask' cases).


## Stay close to the real scenario

Do not fabricate inputs. Do not capture fixtures preemptively. Do not
build extractors for hypothetical model behavior. Each of these is a
windmill — work that looks productive but produces no signal about
the actual system.

Concrete rules:

  - Test inputs come from the real system under test: live LLM calls,
    real config files, real captured request/response pairs from a
    real benched model. Not strings invented in the test file.
  - A fixture (frozen test input on disk) is justified ONLY when the
    real-time cost makes the test suite unusable (e.g., > 60 s for
    a unit-level run). Until that cost is observed and felt, use the
    live source and accept the latency.
  - When a cycle goes red on live-system output, the question is
    "what does the real system actually do?" — read the real output
    in the failure log, do not speculate about edge cases the system
    might exhibit.
  - Multi-round speculative edits chasing imagined behavior are
    forbidden. If two consecutive code edits in the same cycle are
    not driven by a new red test from the real system, stop and ask
    the user.

The lesson from past sessions: hand-rolled BPE marker tests, fabricated
fence-extractor edge cases, and premature reply fixtures all wasted
hours that one direct probe of the real model would have ended in
minutes. Reality is cheaper than imagination.


## The real system includes its hardest dependency from cycle 1

When a bench, agent, or pipeline depends on a remote / expensive /
non-deterministic component (an LLM, a sandbox, a connector, a remote
API), that component must participate in cycle 1. No stand-ins, no
reference fixtures, no "build the harness first then plug the LLM in
later". Reasons:

  - The hardest dependency is where reality bites. A harness that
    works against a stand-in but never against the real component
    proves nothing about the system.
  - Substituting reference solvers / synthetic responses / canned
    replies hides exactly the surprises that the cycle exists to
    surface (token budgets, reasoning preambles, kernel quirks).
  - Deferring the hard dependency lets the rest of the code drift
    from what the real dependency expects. Plugging in last produces
    cascading red.

If the hard dependency requires non-trivial settings (token budgets,
container flags, sandbox image), copy them from the legacy / production
config. Do not invent budgets that look reasonable; production knew
better. A 1500-token budget against a 65k-context reasoning model
because "1500 felt enough" is the canonical failure mode this rule
exists to prevent.

Rule: if the test cannot exercise the hardest dependency yet (the
container is not up, the API key is missing, the secret is not in
.env), the cycle is blocked, not deferred. Stop and fix the
infrastructure before writing more code.


## Decompose a capability into one test per observable layer

If a single test would force the cycle to also exercise upstream or
downstream layers (HTTP -> auth -> chat -> parse -> compile -> load ->
run), decompose into independent test cases — one per layer. Each
layer-test pins exactly one observable capability:

  - Layer 1 / infrastructure reachable
  - Layer 2 / generic protocol works
  - Layer 3 / specific request/response works
  - Layer 4 / response can be parsed
  - Layer 5 / parsed value loads as the expected object
  - Layer 6 / object behaves as expected
  - ...

When something breaks, the failing test name localizes the break. A
single coarse end-to-end test is a smoke alarm for the whole house;
ten layered tests are the room-level alarms you actually need.

Shared expensive setup (an LLM call that produces input for several
downstream tests) is acceptable via a session-scoped pytest fixture:
live capture, in-memory, evicted at the end of every pytest run. Not
frozen on disk. The distinction matters — session fixtures still
exercise the real system every run, on-disk fixtures freeze a moment
of reality and stop catching drift.

## Clean architecture, enforced by architectural test specs

CATS code must form a clean dependency graph per Uncle Bob's Clean
Architecture and the SOLID principles. Behavioral tests pin what the
code does; architectural test specs pin how the code is layered.

### The four layers

Innermost outward:

  src/<lab>/
    entities/    Pure domain types. Dataclasses, enums, value objects.
                 NO imports from other src/ layers. NO imports of
                 urllib, requests, subprocess, docker, file IO, env vars.
                 Example: AttemptResult, GameResult, Submission.

    use_cases/   Application business rules. Orchestrates entities
                 through abstract "ports" (Python Protocol or ABC
                 interfaces). May import entities/ only.
                 Example: ScoreSubmission, IterateToSubmission.

    adapters/    Interface adapters. Concrete implementations of the
                 ports declared in use_cases/. Translates between the
                 entity world and external systems. May import
                 entities/ and use_cases/.
                 Example: VllmChatAdapter (implements ChatPort),
                 DockerInferenceAdapter (implements InferencePort).

    frameworks/  The only layer that touches HTTP libraries, docker
                 commands, file system, environment variables. Wires
                 adapters to concrete drivers. May import any inner
                 layer.
                 Example: vllm_http_driver, docker_provisioner.

The Dependency Rule: code dependencies point only INWARD. Outer layers
depend on inner; inner layers know nothing about outer.

### Architectural test specs

An architectural test spec is a pytest that walks the src/ import
graph (via the `ast` module) and asserts the dependency direction.
It is NOT a behavioral test — it pins a static invariant of the
codebase.

Mandatory architectural tests per lab. There are two families:
**dependency-direction** tests (who-imports-whom) and **structural**
tests (which folders exist).

### Dependency-direction tests

  test_when_entities_imports_inspected_then_no_outer_layer_imports
    Arrange: walk every .py under src/<lab>/entities/.
    Act:     parse imports via ast.
    Assert:  no module imports anything starting with use_cases.,
             adapters., frameworks., urllib, subprocess, requests,
             httpx, docker, pathlib (except via stdlib).

  test_when_use_cases_imports_inspected_then_no_framework_imports
    Arrange: walk every .py under src/<lab>/use_cases/.
    Act:     parse imports via ast.
    Assert:  no module imports from adapters. or frameworks.;
             no direct urllib/subprocess/docker; no environment
             variable access.

  test_when_adapters_imports_inspected_then_no_framework_imports
    Arrange: walk every .py under src/<lab>/adapters/.
    Act:     parse imports via ast.
    Assert:  no imports from frameworks. — adapters expose ports
             but don't choose drivers.

### Structural tests

The dependency-direction tests answer "are the layers wired
correctly?" — but only if the layers exist. The structural tests pin
that the layers DO exist and that no rogue feature-bundle folder
sneaks in. They are the test-spec embodiment of the "Spec folder
hierarchy mirrors clean-arch + source layout" rule.

  test_when_src_inspected_then_every_clean_arch_unit_has_exactly_four_layers
    Arrange: walk src/<lab>/ and identify clean-arch units (a folder
             that contains any of entities/, use_cases/, adapters/,
             frameworks/ as direct children).
    Act:     list the unit's direct children.
    Assert:  the unit's direct children are exactly {entities,
             use_cases, adapters, frameworks} (plus __init__.py and
             __pycache__). No rogue feature-bundle subfolder inside
             a clean-arch unit.

  test_when_src_inspected_then_no_layer_folder_appears_outside_a_clean_arch_unit
    Arrange: walk src/<lab>/ recursively. For every folder named
             entities/, use_cases/, adapters/, or frameworks/, look
             at its parent.
    Assert:  the parent is a clean-arch unit (contains all four
             layers). This prevents a stray entities/ or use_cases/
             folder from sitting at an arbitrary level.

  test_when_src_top_level_inspected_then_is_unit_or_module_container
    Arrange: list non-dunder, non-pycache directories directly under
             src/<lab>/.
    Assert:  EITHER all four canonical layers appear at src/ (lab
             is single-module: src/ IS the clean-arch unit) OR none
             of the four canonical layers appears at src/ and every
             direct subfolder is itself a clean-arch unit (lab is
             multi-module: each subfolder is a module). Mixed layouts
             — a layer folder next to a module folder at src/ — are
             a violation.

  test_when_tests_top_level_inspected_then_mirrors_src_layout
    Arrange: tests/<lab>/ subfolders, same rule as src/.
    Assert:  same shape as src/, plus the two cross-cutting test
             groups architecture/ and clean_arch/ are always allowed
             at the test root (they carry layer-spanning tests).

  test_when_modules_inspected_then_no_inner_imports_outer_or_peer_internals
    Arrange: for every multi-module lab, walk src/<lab>/<module>/
             and ast-collect imports.
    Assert:  no module imports from src.<other_module>.adapters or
             src.<other_module>.frameworks. Cross-module imports are
             allowed ONLY into src.<other_module>.entities or
             src.<other_module>.use_cases. No import cycles between
             modules.

The same three structural tests apply equally to src-spec/ and
tests-spec/ folders — spec hierarchy must mirror code hierarchy.

When a structural test fails, the failure message names the rogue
folder. The fix is always one of: (a) decompose the rogue folder
into the four canonical layers (preferred — see Refactor under CATS
below), or (b) prove the folder is one of the two whitelisted test
groups.

When a refactor crosses the dependency direction, the architectural
test breaks loudly. This is the static analog of behavioral test
pinning, and it makes Clean Architecture a property the suite enforces
rather than aspirational prose in a README.

### SOLID in CATS

- Single Responsibility: each module exposes ONE focused purpose.
  Code that mixes orchestration with HTTP plumbing with file IO
  violates SRP and must be refactored to separate layers.
- Open/Closed: extending the bench to a new model family adds a
  new adapter, not a modification to use_cases. New tier (T2/T3/T4)
  adds new use cases + adapters; entities and unchanged adapters
  stay untouched.
- Liskov Substitution: adapters implementing the same port are
  interchangeable. Tests on use_cases must run against any adapter
  satisfying the port contract.
- Interface Segregation: ports are small and focused. A use case
  that needs only `chat(messages) -> str` depends on a `ChatPort`
  with one method, not a fat client class with thirty.
- Dependency Inversion: high-level policy (use cases) depends on
  abstractions (ports); low-level details (HTTP, Docker) implement
  those abstractions. Concretely: use_cases imports a Protocol;
  frameworks constructs the concrete adapter at app entry.

### When to write the architectural test spec

Per the per-behavior cycle: an architectural rule is "next behavior"
when the import graph would silently allow a violation that wrecks
the design. Add the architectural test the moment a new layer
emerges; the test then prevents future drift.

### Where inputs, outputs, reports, and persistence live

The four canonical layers absorb every lab concern. New labs often
ask "where do I put inputs / outputs / reports / database storage?";
the answer is always one of the four:

- **Inputs** (e.g. a bench submission's model name + prompt) are
  request DTOs at the use-case boundary. A `Submission` value object
  with `model` and `prompt` fields lives in `entities/` if it is a
  reusable domain concept; otherwise as a small dataclass alongside
  the use case in `use_cases/`.

- **Outputs** (e.g. attempt results, scores, statistics) are response
  DTOs at the use-case boundary. Stable domain results live in
  `entities/` (e.g. `AttemptResult`, `Iteration`, `MeanScores`);
  use-case-specific response shapes live alongside the use case in
  `use_cases/`.

- **Reports** (human-readable summaries: markdown, HTML, terminal
  output) are presenters — output-side interface adapters. They live
  in `adapters/`, transforming entities into formatted strings or
  files. A presenter carries no business logic; it only formats.

- **Persistence** (storing every swipe, caching attempts, writing
  artifacts to disk) splits across the layers: the abstract port
  (`SwipeStorePort`) lives in `use_cases/`; the concrete adapter
  (`SqliteSwipeStoreAdapter`, `MarkdownSwipeStoreAdapter`, or
  similar) lives in `adapters/`; non-trivial drivers (sqlite/postgres
  client, S3 SDK, env-var lookup) live in `frameworks/`. The use
  case talks only to the port. The backing store doesn't have to be
  a database: a folder of markdown files indexed by timestamp is a
  perfectly valid swipe store and needs no `frameworks/` occupant at
  all — pathlib file IO in the adapter is enough. Pick the simplest
  backing store that captures what the lab needs to remember.

If a new concern does not obviously fit, ask: is it (a) a domain
type, (b) an application rule, (c) an input/output translator, or
(d) a low-level driver? That answer picks the layer. There is never a
fifth answer; "make a new top-level folder" is the wrong move and
indicates a layer that needs decomposing.

### Refactor under CATS

Restructuring src/ to fit the four layers is itself a sequence of
CATS cycles, each one:

  1. New architectural test spec asserting the next dependency rule.
  2. Test red because current code violates the rule.
  3. Refactor src/ to satisfy the rule (move files, rename, extract
     interfaces).
  4. Behavioral tests still green after the move.
  5. Architectural test green.
  6. Commit + push.

Each architectural cycle moves one piece of code into its correct
layer with the test as evidence. The codebase converges on Clean
Architecture under the same TSDD-style discipline the rest of CATS
uses.


## End of inlined CATS
