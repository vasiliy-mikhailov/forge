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

## CATS methodology (inlined from `phase-preliminary/cats.md`)

**Keep in sync** with [`phase-preliminary/cats.md`](phase-preliminary/cats.md).
Drift is a defect.

# CATS methodology — bridging TOGAF documents to robust implementation (clean architecture test specs)

Read this before writing implementation code in any forge lab.

## Stance

- **Act as a senior functional programmer who happens to implement
  in Python.** Pure functions over stateful methods. Immutability
  (frozen dataclasses, tuples) over mutation. Composition over
  inheritance. Small, focused functions with explicit inputs and
  outputs. Side effects sit at the edges; the core is pure.
- **Prefer fitness functions: constraints → search → verification →
  repair → repeat.** Define what success looks like *as a check*
  before you start; iterate against the check; verify on each pass;
  repair when the check regresses. Tests are fitness functions:
  they encode the constraint. Quality floors are fitness functions:
  they catch search drift. Live-runtime tests are fitness functions
  against the real environment.


## What this connects

TOGAF documents (Phase A vision, Phase B business architecture, Phase
C information systems architecture, ADRs, per-lab SPEC.md) describe
**what**. This file describes **how** an agent turns them into code
without losing fidelity.

Test-first. Tests pin the contract documents promise. Code exists
only to make tests pass. Spec describes only what tests prove.

## The CATS cycle (one iteration)

Do all eleven steps for ONE test case, then start the next.

  1. Pick the next behavior that advances the TOGAF documents under
     implementation. Smallest unit that adds value; avoid scoping
     beyond one paragraph of src-spec. Confirm with the user when
     ambiguous.
  2. Add an entry to the tests-spec file. Carry enough detail to
     reconstruct the test if test code is lost. Format:

         test_when_X_then_Y
           Arrange: what fixture / inputs the test sets up.
           Act:     what call / interaction the test makes.
           Assert:  what property of the result the test checks.

     The when-clause maps to Arrange + Act; the then-clause maps to
     Assert. The entry IS the contract.
  3. Extend the matching src-spec only as far as the new test demands.
     No 'Out of scope' / 'deferred' / 'future' enumeration.
  4. Write ONE pytest function in test_<module>.py using Arrange /
     Act / Assert. Function name matches step 2.
  5. Run pytest. Red expected.
  6. Write the minimum code to make it green. NO validation, type
     coercion, error handling, or behavior beyond what the test asserts.
  7. Run the just-added test. Green.
  8. Refactor while green. Four artifacts in scope:
       - tests-spec: collapse near-duplicate entries; tighten names.
       - src-spec: trim overpromises (anything no test exercises).
       - test code: extract duplicated arrange blocks; rename.
       - implementation code: extract duplication, simplify, rename.
     The refactor MUST NOT change observable behavior; no src-spec or
     tests-spec promise should change.
  9. Run the IMPACTED test scope per **test impact analysis (TIA)**
     — every test connected to the code you touched. "Connected" =
     imports a module you modified, or transitively imports one.
     Confirm every previously-green test in that set is still green.
     If any regressed, the refactor was not behavior-preserving —
     revert.

     The FULL suite is a coarser gate, not per-cycle. It runs before
     pushing a chain of cycles, at session boundary, in CI, and on
     schedule. Cycle cadence is the lever; a 13+ min per-cycle gate
     destroys it. TIA catches what the immediate change breaks;
     full-suite catches cross-module drift TIA misses.

     TIA implementations:
       - **Manual**: identify imports of changed modules, run pytest
         against matching test files.
       - **Tool-assisted**: `pytest-testmon` replays tests whose
         coverage intersects the diff.
       - **Static**: ast-walk tests to build a test->imports graph,
         intersect with changed-files set.

     Pragmatic guidance:
       - When uncertain whether a test is connected, include it.
       - Before `git push` of a chain, run the FULL suite.
       - Document the TIA scope in the commit message under step-11.
  10. Commit and push. Only after step 9 is green. Message names the
      cycle and the test case. Push to origin so remote stays in sync.
  11. Report progress. After the commit, surface:
        - TOGAF documents under implementation (SPEC.md, ADRs)
        - approximate coverage percent (tested / enumerated requirements)
        - estimated time for remaining cycles
        - next cycle name + planned scope
      A document at 100% coverage is fully validated; everything else
      is aspirational.

## Discipline rules

- src-spec describes only what tests prove. Anything no test exercises
  is a lie — delete it. No 'Out of scope' section, no anticipatory
  enumeration.
- One test case per cycle. No pre-written test enumerations.
- Test names: test_when_X_then_Y. One when, one then. Split if more.
- Test bodies: Arrange / Act / Assert with those literal comments.
- No code without a failing test. If a cycle needs implementation
  without a red test, pick a smaller behavior.
- **Minimal implementation during GREEN; no speculative code.** The
  implementation MUST be the smallest change that makes the test
  pass. No extra fields, methods, pre-generalized Protocols, "while
  I'm here" tidy-up, or future-proof abstractions. Refactor happens
  in REFACTOR (final step or dedicated cycle), never during GREEN.
  Port-lifting, helper extraction, renaming, splitting modules — all
  belong at refactor. Mixing produces speculative abstractions that
  break previously-green tests.
- Each commit covers exactly one cycle. Diff readable in one screen.
- **Artifacts come from tests.** Leaderboard data points, performance
  numbers, golden outputs, screenshot baselines, benchmark scores —
  any *result* checked into the repo — must come from a test that
  pins its shape. Ad-hoc number-producing scripts are forbidden.
    - A leaderboard-producing campaign lives as a pytest test
      (often opt-in / marked slow), not a `bin/` script.
    - The test_spec declares: what config, the result file path,
      required fields (n_games, mean_score type), tolerances
      ("mean_score >= 0 and finite"). It does NOT assert a specific
      value — model noise is real — but pins the *shape*.
    - The test writes the artifact to its declared path; the
      artifact + test commit together makes lineage answerable via
      `git blame`.
    - Slow live-model tests (5+ min) are opt-in via pytest marker;
      per-cycle TIA skips them; coarser gates refresh the leaderboard.
- **No silent bug fixes.** When a bug is discovered outside a test
  run (manual probe, production observation, log eyeballing):
    1. Write a `test_spec` capturing the bug — expected vs observed.
    2. Write test code. CONFIRM it reproduces the bug (RED, same
       error mode). Otherwise the test does not pin the behaviour.
    3. Only then fix the code.
    4. Re-run; confirm GREEN.
    5. Commit test + fix together.
  Silent fixes (code change without a corresponding test) are
  forbidden. Applies to import errors, integration failures, and
  real-system operations observations equally.

- **When introducing a CATS or ADR rule, audit existing code in the
  same cycle; do not pre-fix.** A new rule that applies to "all X"
  must include a **read-only** audit in the same cycle. Each
  violation becomes a follow-up cycle. The rule-cycle commit ships:
  rule + audit summary + follow-up task list. The first violation
  is fixed in the NEXT cycle. This prevents:
    1. Rules silently allowing pre-existing violations (backsweep
       forgotten, backlog accumulates invisibly).
    2. Mixing rule introduction with speculative fixes that break
       previously-green tests.

## Suggested folder layout per lab

  <lab>/
    SPEC.md                            lab functional spec — TOGAF-facing
                                       document UNDER implementation.
    AGENTS.md                          operator interface
    src-spec/                          CODE-facing functional specs.
                                       Two-level: <layer>/<source_file>/.
                                       ONE file per behavior.
      <layer>/<source_file>/src_spec_when_X_then_Y.md
    tests-spec/                        CODE-facing test specs. Same
                                       two-level hierarchy. ONE file per test.
      <layer>/<source_file>/test_spec_when_X_then_Y.md
    tests/                             pytest implementations.
      test_<module>.py
    src/                               implementation satisfying src-spec/.
      <module>.py

## Test file mirrors source file

`tests/test_<module>.py` covers `src/<module>.py`. One source file →
one test file. Coverage is traceable by file:

    src/<area>/inference.py            covered by
    tests/<area>/test_inference.py

    src/<area>/parser.py               covered by
    tests/<area>/test_parser.py

A test file may hold many `test_when_X_then_Y` functions. Grouping
tests across source files into `test_<feature>.py` or
`test_end_to_end.py` is forbidden. End-to-end coverage emerges from
the union of per-module test files.

Each test function maps 1:1 to a test_spec_when_X_then_Y.md file; the
.py file it lives in is chosen by which src/ module it exercises.

## Spec folder hierarchy mirrors clean-arch + source layout

Two-level hierarchy:

    src-spec/<layer>/<source_file>/src_spec_when_X_then_Y.md
    tests-spec/<layer>/<source_file>/test_spec_when_X_then_Y.md

First level (`<layer>/`) is the clean-arch layer. Under `src/` and
`src-spec/`, only the four canonical layers: `entities/`,
`use_cases/`, `adapters/`, `frameworks/`. Under `tests/` and
`tests-spec/`, same four plus two cross-cutting groups: `architecture/`
(ast-walking dependency-direction tests) and `clean_arch/` (layered
wire-up tests spanning multiple layers).

Feature-bundle folders (`tier1/`, `bench/`, `myfeature/`) at the
first level are a violation — they re-introduce the mixed-concerns
problem clean architecture prevents. Decompose into the four layers
immediately.

Second level (`<source_file>/`) is the python module name under test
— bare stem, no `.py`, no `test_` prefix. For `src/<layer>/parser.py`,
specs live under `src-spec/<layer>/parser/` and
`tests-spec/<layer>/parser/`.

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

These pin properties of the codebase, not a single source file. The
second-level name uses the **test file stem with `test_` dropped**:

    tests/architecture/test_dependency_direction.py
      <-> tests-spec/architecture/dependency_direction/test_spec_*.md

    tests/clean_arch/test_score_submission_wired.py
      <-> tests-spec/clean_arch/score_submission_wired/test_spec_*.md

tests-spec/ is ALWAYS two levels deep. A spec sitting at
tests-spec/<layer>/ with no per-source-file folder is a violation.

The hierarchy:
  - One `ls src-spec/<layer>/<module>/` answers "what specifies X?".
  - Cross-cutting concerns don't pollute per-module folders.
  - New layers/modules surface as new folders, not naming violations.

## Single-module vs multi-module monolith

Two shapes:

**Single-module.** The lab is one clean-arch unit. `src/` is the
unit's root; its direct children are the four canonical layers.

    src/
      entities/
      use_cases/
      adapters/
      frameworks/

**Multi-module.** Multiple bounded contexts, each a self-contained
clean-arch unit. `src/` is a container of modules; each module is a
clean-arch unit with its own four layers.

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

Spec folder structure mirrors source folder structure exactly:
single-module → `src-spec/<layer>/<source_file>/`; multi-module →
`src-spec/<module>/<layer>/<source_file>/`.

### Module-to-module dependency rules

Modules form a hierarchy: the outermost orchestrator composes inner
bounded-context modules. Outer-module-depends-on-inner-module mirrors
outer-layer-depends-on-inner-layer:

  - Outer modules may import the **public API** of an inner module —
    its `entities/` and `use_cases/`. These are the contract.
  - Outer modules MUST NOT import inner `adapters/` or `frameworks/`.
  - Inner modules NEVER import from outer modules.
  - Peer modules (tier1, tier2) NEVER import each other. Tier-to-tier
    coupling is routed through the orchestrator.

Cycles between modules are a hard violation. Shared types belong in
a third inner module (e.g. `shared/`, `kernel/`) both depend on.

## Spec files are Markdown

`src_spec_*.md` and `test_spec_*.md` MUST be valid Markdown — they
render on GitHub, in previewers, in IDE side panels.

- Paragraph breaks need a blank line. Soft wraps collapse.
- Test names, file paths, env vars, HTTP verbs, inline code in backticks.
- Test-spec entries: heading per test case
  (`### \`test_when_X_then_Y\``) + bulleted `**Arrange**` /
  `**Act**` / `**Assert**`.
- Tables for layers, fields, fixtures.
- Cross-references use Markdown link syntax (relative paths).

## Specs are language-agnostic

Contracts MUST be expressible without naming the implementation
language. Python `Protocol`, Go `interface`, TypeScript `interface`,
Rust `trait` should all be valid targets.

- Describe **behaviour** ("a `ModelClient` sends messages and returns
  a reply containing content plus a tool_calls list"), not syntax.
- Describe **types in prose or table form**, not language literals.
  Prefer:

      `call(messages, tools)` accepts a sequence of message objects
      (each `{role, content}`) and an optional tool-schema sequence;
      returns a reply with fields `content` (string) and `tool_calls`
      (sequence of tool-call objects, possibly empty).

- Cross-reference the implementation file path.
- When a contract spans a network boundary (HTTP, gRPC, queue),
  include an **OpenAPI fragment** inline — the one language-agnostic
  IDL allowed. Fenced ` ```yaml ` block.

Example: an LLM chat port in OpenAPI:

```yaml
openapi: 3.1.0
components:
  schemas:
    AssistantReply:
      type: object
      required: [content, tool_calls]
      properties:
        content: { type: string }
        tool_calls:
          type: array
          items: { $ref: '#/components/schemas/ToolCall' }
paths:
  /chat/completions:
    post:
      requestBody:
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ChatRequest' }
      responses:
        '200':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/AssistantReply' }
```

Specs must survive re-platforming (Python → Go, monolith → service).
Code references are illustrations, not the contract.

## One test_spec per contract — across all binding modes

Per [ADR 0014](#) test_specs name their DI seam. Per [ADR 0018](#)
every runtime-boundary dependency has Port + production adapter +
Fake + autouse binding. Result: **one test_spec per contract**, not
per binding.

- "main() returns AttemptResult shaped correctly" is ONE contract.
  It runs as unit test (Fake binding, autouse), hermetic seam test
  (`@pytest.mark.no_fake` with stubbed lower seam), and e2e test
  (`@pytest.mark.live` against live stack). Same contract, three
  bindings — one test_spec.

- The test_spec's "Model client injection point" / "Sandbox injection
  point" subsection names how to re-run under each mode.

- The test function MAY be parametrised:

      @pytest.mark.parametrize("binding", ["fake", "no_fake", "live"])
      def test_when_X_then_Y(binding, ...):
          ...

  or three functions sharing one spec file. The spec is the contract
  record; function count is an implementation detail.

- **DO NOT** write "unit variant" and "live variant" of the same
  contract under separate test_spec files.

- **DO** keep separate test_specs when the contract genuinely differs
  per binding (e.g. "vLLM responds within 5 minutes" — real-stack-only,
  no fake equivalent).

- **Parametrisation over a registry follows the same rule.**
  `@pytest.mark.parametrize("target", MODEL_REGISTRY, ...)` asserting
  a property for every value is ONE contract → ONE test_spec. Values
  live in the registry, not in spec filenames. Use `<target.id>` /
  `<target.served_name>` placeholders in the spec body.

  Exception: a parameter value with genuinely different observed
  behaviour (model whose tokenizer leaks SentencePiece; solver with
  its own walltime envelope) earns its own spec.

A contract that holds under Fake but breaks under Live is a bench
bug, not a different test. Same spec, two bindings keeps the
contract honest.

## One src_spec per contract — across all implementations

Mirror of the test_spec rule. Per [ADR 0018](#) every runtime-boundary
dependency has Port + production adapter + Fake. The Port IS the
contract; adapters conform.

- A Port (e.g. `CanonicalScorerPort`) gets ONE src_spec: method
  signatures, return shape, error semantics, lifecycle, forbids
  ("MUST NOT raise on hostile input"). Liskov violations refer here.

- Adapters (Fake, InProcess, Docker) do NOT get parallel src_specs
  duplicating the Port. The adapter file gets a module-level
  docstring naming the Port. Cross-cutting decisions (Docker
  isolation, image versioning, walltime sentinels) live in ADRs.

- Adapters MAY have their own src_spec only for surface **beyond**
  the Port (`FakeModelClient.calls` for test assertions;
  `DockerCanonicalScorer`'s `--cpus` / image-tag knobs). The adapter
  src_spec documents only that added surface and links to the Port spec.

- Entities (`AttemptResult`, `BenchConfig`) keep their own src_specs
  — they ARE the contract.

- Use-case modules (`run_loop`, `main`) keep their own src_specs —
  their contract is the composition.

Duplicating Port semantics across adapter src_specs is the drift the
"Git is the history" rule rejects.

When this matters:

- Adding an adapter to an existing Port: add code with Port-naming
  docstring, write tests, do NOT create a parallel src_spec unless
  it adds caller-visible surface.

- Refactoring a single-implementation module into Port + adapter:
  create the Port src_spec, delete the now-redundant adapter src_specs
  in place (no "Superseded by Port spec" notes).

## Lift implicit contracts into Ports — the rule of three

[ADR 0018](#) forces a Port at runtime-boundary introduction
(subprocess, HTTP, fs, Docker) — first instance. It does not catch
**internal composition seams** that accumulate over cycles (a
`Callable` parameter in `use_cases/`, a dispatch-by-name registry,
several classes sharing a single-method shape).

For those: **the rule of three, applied at refactor**.

- SECOND implementation: note it. Two is coincidence; abstraction
  is speculative.

- THIRD: the **refactor step** (or a dedicated refactor cycle) lifts:

      1. `src/ports/<name>.py` with the `Protocol`.
      2. `src-spec/ports/<name>/...`.
      3. test_spec parametrised over adapter implementations.
      4. Existing implementations renamed to named adapters; call
         sites switch to a Port-typed parameter.
      5. Architectural `PORT_MANIFEST` extended.

- **Lift always happens AFTER all behavioral tests are GREEN.** Never
  during RED. Observable behaviour MUST NOT change. Tests going red
  during the lift means the lift was wrong; revert.

- The lift MAY be its own cycle if large (multi-file renames,
  conftest binding changes). Always AFTER green.

- **One-off shapes stay inline.** Rule of three is a heuristic. When
  in doubt, lift later — cost at fourth instance is small; cost of
  premature abstraction is concrete code no one needs.

External boundaries are forced because their side-effect surface is
untestable without a Fake. Internal composition seams compound
silently — three classes sharing a shape look fine but prevent
parametrised tests, prevent architectural conformance enforcement,
and let contracts drift. Rule of three is the lower-bound moment at
which the cost of NOT lifting exceeds the cost of lifting.

## Three runtimes, two scales of src_spec — unit / live / production

Every test_spec describes one contract across all bindings; "binding
modes" are **runtimes**, and every src_spec has **two adapter scales**
that define the bindings.

### Two scales of src_spec

Every runtime-boundary Port src_spec declares two adapter scales:

- **Unit scale** — the Fake adapter. In-memory, deterministic,
  scripted. Autouse Fake binding per ADR 0018. Examples:
  `FakeModelClient`, `FakeCanonicalScorer`. Fakes exist only in tests.

- **Live & production scale** — the Real adapter. Real subprocess,
  HTTP, Docker. **Same Real adapter runs under both live-test and
  production — they differ only in DI parameters, not code.** Examples:
  `VllmOpenAIClient`, `DockerCanonicalScorer`.

Adapter src_specs declare scale; Port src_spec lists adapters by
scale. Multiple adapters at the same scale are allowed
(`InProcessCanonicalScorer` as a second live/production-scale
adapter). Two-scale rule is the floor.

Pure-Python composition Ports (rule of three) MAY have a single
trivial adapter serving both scales (`NullSupervisor`, `NullCondenser`
— real code, no side-effect surface). The src_spec MUST declare:

  > **Scales**: NullSupervisor is the trivial real adapter and serves
  > both unit and live/production scales. No separate Fake exists
  > because the Port has no side-effect surface to fake.

### Three runtimes

A **runtime** = `(adapter-scale, DI-parameter-pack)`:

- **Unit** — unit-scale adapters + smallest config (`max_iters=1`,
  `n_trials=1`, 1 seed, `hard_wall_sec=5`). Default; unmarked.
  Milliseconds. Per-cycle TIA gate. Catches seam-wiring breaks.

- **Live** — live/production-scale adapters + reduced config
  (`max_iters=10`, `n_trials=1`, 3 seeds, `hard_wall_sec=60`,
  `smoke_early_stop=True`). `@pytest.mark.live`. Minutes. Pre-merge
  gate. Catches fake-fidelity drift AND broken real boundaries
  (image missing, daemon down, malformed tokens).

- **Production** — live/production-scale adapters + FULL config
  (`max_iters=500`, `n_trials=10`, 20 seeds, `hard_wall_sec=300`).
  `@pytest.mark.production`. Hours; doubles as canonical bench
  (`run_canonical_battery()`). Catches scale-dependent breaks
  (state at iter 200+, multiprocessing races, `walltime_exceeded`).

What changes between the three runtimes:

| dimension      | unit            | live             | production       |
|----------------|-----------------|------------------|------------------|
| adapter scale  | unit (Fake)     | live/production  | live/production  |
| `max_iters`    | 1               | 10               | 500              |
| `n_trials`     | 1               | 1                | 10               |
| seeds          | 1               | 3                | 20               |
| `hard_wall_sec`| 5               | 60               | 300              |
| marker         | (default)       | `@live`          | `@production`    |
| typical time   | ms              | minutes          | hours            |

Live and production share the **same code path** — only config
differs. Contract holds under live but breaks production = missed
scale-dependence. Holds under unit but breaks live = Fake drifted.

### Every test_spec MUST cover all three runtimes

- Every test_spec declares three runtime variants. Typically ONE
  function parametrised over `(runtime, config)`:

      @pytest.mark.parametrize("runtime,config", [
          ("unit",       UNIT_CONFIG),
          ("live",       LIVE_CONFIG),
          ("production", PROD_CONFIG),
      ])
      def test_when_X_then_Y(runtime, config, ...):
          ...

  OR three functions sharing one spec file.

- The conftest autouse fixture (ADR 0014) binds the adapter scale by
  runtime parameter/marker: Fake for unit; Real for live and production.

- Assertions assert on the CONTRACT (the property that holds across
  all three). Per-runtime tolerances live in config, not assertions.

- Scale-invariant contracts (entity-shape tests, Port-Protocol
  existence, pure-function unit tests) MAY opt out of live/production
  with an explicit justification:

      > **Runtime scope**: unit only — this contract is
      > scale-invariant by construction (asserts on `AttemptResult`'s
      > frozen-dataclass shape; no boundary involved).

  Without justification, all three runtimes are required.

### The Runtime injection points spec section

Renamed from "Model client injection point". Table naming
`(adapter, config)` per runtime:

| runtime    | adapter binding        | config            |
|------------|------------------------|-------------------|
| unit       | `FakeModelClient` (autouse) | `UNIT_CONFIG`     |
| live       | `VllmOpenAIClient`     | `LIVE_CONFIG`     |
| production | `VllmOpenAIClient`     | `PROD_CONFIG`     |

Scale-invariant test_specs note "unit only" instead of the full table.

### Why this matters

Unit test pins seam wiring. Live test pins "the real boundary works."
Production test pins scale-dependent behaviour. Each catches what
the others can't. The fake-fidelity trap (Fake says ok, real
disagrees) and the scale-blindness trap (passes at max_iters=1,
breaks at iter 200) both close under three-runtime discipline.

## Git is the history; specs describe the current decision

ADRs, src_specs, test_specs describe the **current decision**, not
its evolution. Git is the durable record. Don't duplicate it.

- **Don't write "Superseded by X" notes.** Delete superseded ADRs.
  Readers find them via `git log -- docs/adr/<name>.md`.
- **Don't keep version-history blocks.** Rewrite to describe only
  the current version. `git blame` and `git log -p` show prior prose.
- **Don't append amendment sections.** Rewrite affected paragraphs
  in place. The body should read as truth as of HEAD.
- **Cycle-number stamps inside spec prose are usually noise.** Keep
  only when they orient `git log --grep='cycle 77'` lookups.
- **Cross-references stay.** Links between current documents are the
  docs graph. Links to deleted ADRs are broken — delete or redirect.

Exception: version header comment blocks ("v0.1 → v0.2 → v0.3 → v0.4
with reasons") are legitimate — pinning image-tag → semantics is
part of the contract, not history.

## File naming convention

Per-behavior spec files are named after the test they justify:

    src-spec/<layer>/<source_file>/src_spec_when_X_then_Y.md
    tests-spec/<layer>/<source_file>/test_spec_when_X_then_Y.md

ONE file per test case. The filename IS the contract. Do NOT bundle
multiple test specs into one feature file. No roll-up "index" or
"end_to_end" file — folder structure + per-behavior filenames suffice.

Test code and implementation:

    tests/<area>/test_<module>.py
    src/<area>/<module>.py

A test file holds multiple functions, one per
test_spec_when_X_then_Y.md.

## Implementation ADRs — between SPEC.md and test_spec

A test_spec pins ONE behavior in 30-300 words. SPEC.md describes the
lab's TOGAF promise in hundreds of lines. Between them: the
**architectural decisions** — too detailed for SPEC.md, too
cross-cutting for any test_spec. They live as **implementation ADRs**
at `<lab>/docs/adr/NNNN-short-slug.md`.

Each ADR captures:

- **Status** — Accepted (date) | Superseded by ADR-NNN | Deprecated.
- **Context** — what forced the decision.
- **Decision** — one-sentence position, specific enough to write code.
- **Consequences** — positive AND negative; revert cost.
- **Alternatives considered** — named and briefly rejected.
- **Implementation pointers** — files/cycles that realise it.

Lab-local numbering (own sequence from `0001`), distinct from
forge-wide ADRs in `phase-preliminary/adr/`.

### When to write an implementation ADR

BEFORE the cycle that realises it. Symptoms that an ADR is overdue:

- You're typing "we chose X because Y" into a test_spec body.
- A decision is referenced/contradicted by `_bak/` legacy.
- Two reasonable implementations fit SPEC.md.
- The cycle will write production code hard to revert without context.

Pause the test_spec cycle, write the ADR, commit, then realise.
test_spec references the ADR by relative path.

### Example

`reward-bench` faced "condenser uses same model as bench, or
separate smaller one?". SPEC.md mentioned "a condenser" without
committing; legacy `_bak/` used separate. The decision was made AS
AN ADR (`reward-bench/docs/adr/0001-condenser-uses-same-model-as-bench.md`)
BEFORE the wiring cycle. Implementation pointers name the realising
cycles.

## Two layers of code-facing spec, one TOGAF document under implementation

  - SPEC.md at the lab root: the document under implementation,
    TOGAF-facing (what the lab measures, tiers, outputs). Coverage
    of SPEC.md is the step-11 report.
  - src-spec/ and tests-spec/: code-facing. Every tests-spec entry
    derivable from src-spec + SPEC.md; every src/ line derivable
    from src-spec + tests-spec.
  - SPEC.md change → src-spec → tests-spec → tests → src/. Chain
    works in either direction.

## Reverse-engineering legacy code

For legacy code that drifted from src-spec/SPEC.md: move to a
quarantine directory (per-lab) and rebuild from tests.

  - Read quarantined code to learn observable behavior; do not import.
  - New code has no dependency on quarantined code.
  - Each green cycle frees a slice to delete.

Lab-specific quarantine paths live in each lab's CATS.md.

## When to stop a cycle and ask the user

- Behavior in legacy code is clearly a bug — pin or fix?
- Two reasonable behaviors fit the test case.
- The next smallest case requires unbuilt infrastructure.
- The cycle touches an architectural concern not in TOGAF docs.
  Amend the relevant TOGAF doc *before* writing code.

## Why this works as a TOGAF bridge

The chain SPEC.md → src-spec → tests-spec → tests → src/ keeps every
layer auditable from any other. SPEC.md change forces src-spec
update, which forces tests-spec, tests, src/, surfacing in a commit.
Reverse: a src/ bug forces a tests-spec regression entry, which may
force src-spec and SPEC.md amendments.

## Per-lab adoption

Each lab keeps lab-specific conventions in `<lab>/CATS.md`
referencing this document at the top — module names, quarantine
scope, lab-specific 'when to ask' cases.


## Stay close to the real scenario

Do not fabricate inputs. Do not capture fixtures preemptively. Do not
build extractors for hypothetical model behavior. Reality is cheaper
than imagination.

  - Test inputs come from the real system: live LLM calls, real
    configs, captured request/response pairs from real models. Not
    invented strings.
  - A fixture (frozen input on disk) is justified ONLY when real-time
    cost makes the suite unusable (e.g. >60 s for unit-level).
  - When a cycle goes red on live output, read the failure log; do
    not speculate about edge cases.
  - Multi-round speculative edits are forbidden. Two consecutive
    edits in one cycle not driven by a new red test from the real
    system → stop and ask the user.


## The real system includes its hardest dependency from cycle 1

When a bench, agent, or pipeline depends on a remote / expensive /
non-deterministic component (LLM, sandbox, connector, API), that
component participates in cycle 1. No stand-ins, no canned replies,
no "build the harness first then plug the LLM in later".

  - The hardest dependency is where reality bites. A harness that
    works against a stand-in but not the real thing proves nothing.
  - Substituting reference solvers hides the surprises the cycle
    exists to surface (token budgets, reasoning preambles, kernel
    quirks).
  - Deferring lets code drift from what the real dependency expects.
    Plugging in last produces cascading red.

If the dependency needs non-trivial settings (token budgets, container
flags, sandbox image), copy from legacy/production config. Don't
invent budgets — production knew better. A 1500-token budget against
a 65k-context reasoning model "because 1500 felt enough" is the
canonical failure mode.

If the test cannot exercise the hardest dependency yet (container
down, API key missing), the cycle is **blocked**, not deferred. Fix
the infrastructure first.


## Decompose a capability into one test per observable layer

If a single test would force the cycle to exercise multiple layers
(HTTP → auth → chat → parse → compile → load → run), decompose into
one test per layer:

  - Layer 1 / infrastructure reachable
  - Layer 2 / generic protocol works
  - Layer 3 / specific request/response works
  - Layer 4 / response can be parsed
  - Layer 5 / parsed value loads as the expected object
  - Layer 6 / object behaves as expected
  - ...

A failing test name localizes the break. Coarse end-to-end is a smoke
alarm for the whole house; ten layered tests are the room-level
alarms you need.

Shared expensive setup (an LLM call feeding several tests) is
acceptable via a session-scoped pytest fixture: live capture,
in-memory, evicted per pytest run. NOT frozen on disk. Session
fixtures still exercise the real system; on-disk fixtures freeze a
moment and stop catching drift.

## Clean architecture, enforced by architectural test specs

CATS code forms a clean dependency graph per Uncle Bob's Clean
Architecture + SOLID. Behavioral tests pin what code does;
architectural tests pin how it's layered.

### The four layers

Innermost outward:

  src/<lab>/
    entities/    Pure domain types (dataclasses, enums, value objects).
                 No imports from other src/ layers; no urllib, requests,
                 subprocess, docker, file IO, env vars.
                 Examples: AttemptResult, GameResult, Submission.

    use_cases/   Application business rules. Orchestrates entities
                 through abstract Ports (Protocol or ABC). Imports
                 entities/ only.
                 Examples: ScoreSubmission, IterateToSubmission.

    adapters/    Concrete Port implementations. Translates between
                 entities and external systems. Imports entities/ and
                 use_cases/.
                 Examples: VllmChatAdapter, DockerInferenceAdapter.

    frameworks/  The only layer touching HTTP libraries, docker
                 commands, file system, env vars. Wires adapters to
                 drivers. May import any inner layer.
                 Examples: vllm_http_driver, docker_provisioner.

The Dependency Rule: dependencies point INWARD. Outer depends on
inner; inner knows nothing about outer.

### Architectural test specs

A pytest that walks the src/ import graph (via `ast`) and asserts
dependency direction. Pins a static invariant, not behavior.

Mandatory per lab. Two families: **dependency-direction**
(who-imports-whom) and **structural** (which folders exist).

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

Dependency-direction tests answer "are the layers wired correctly?"
— but only if the layers exist. Structural tests pin that the layers
exist and no rogue feature-bundle folder sneaks in.

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

The same structural tests apply to src-spec/ and tests-spec/ — spec
hierarchy mirrors code hierarchy.

On failure, the message names the rogue folder. Fix: (a) decompose
into the four layers (preferred), or (b) prove it's a whitelisted
test group.

### SOLID in CATS

- **SRP**: each module exposes ONE focused purpose. Mixing
  orchestration with HTTP plumbing and file IO violates SRP.
- **Open/Closed**: a new model family adds an adapter, not a
  use_cases change. New tier adds use cases + adapters; entities
  untouched.
- **Liskov**: adapters under the same port are interchangeable.
- **Interface Segregation**: ports are small. A use case needing
  `chat(messages) -> str` depends on a one-method `ChatPort`, not
  a thirty-method fat client.
- **Dependency Inversion**: use_cases imports Protocols; frameworks
  constructs concrete adapters at app entry.

### When to write the architectural test spec

Add the moment a new layer emerges; the test prevents future drift.

### Where inputs, outputs, reports, and persistence live

Every lab concern fits one of four layers:

- **Inputs** (submission model + prompt) are request DTOs at the
  use-case boundary. Reusable domain concepts → `entities/`;
  otherwise small dataclass beside the use case in `use_cases/`.

- **Outputs** (attempt results, scores, stats) are response DTOs.
  Stable domain results → `entities/` (`AttemptResult`, `Iteration`);
  use-case-specific shapes → `use_cases/`.

- **Reports** (markdown/HTML/terminal summaries) are presenters —
  output-side adapters in `adapters/`. No business logic; format only.

- **Persistence** splits across layers: abstract port
  (`SwipeStorePort`) in `use_cases/`; concrete adapter
  (`SqliteSwipeStoreAdapter`, `MarkdownSwipeStoreAdapter`) in
  `adapters/`; non-trivial drivers (sqlite client, S3 SDK, env-var
  lookup) in `frameworks/`. The store may be markdown files indexed
  by timestamp with pathlib IO in the adapter — no `frameworks/`
  occupant needed. Pick the simplest store that captures what the
  lab needs to remember.

If a new concern doesn't fit, ask: (a) domain type, (b) application
rule, (c) input/output translator, or (d) low-level driver? Never a
fifth answer; "make a new top-level folder" is wrong.

### Refactor under CATS

Restructuring src/ is itself a sequence of CATS cycles:

  1. New architectural test spec for the next dependency rule.
  2. Test red because current code violates.
  3. Refactor src/ (move, rename, extract interfaces).
  4. Behavioral tests still green.
  5. Architectural test green.
  6. Commit + push.

Each cycle moves one piece into its correct layer with the test as
evidence. The codebase converges on Clean Architecture under the
same TSDD discipline.


## End of inlined CATS
