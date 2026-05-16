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
     and on a schedule. The relaxation exists because forge's primary
     motivation is **time-to-market** — cycle cadence is the lever
     that controls how many CATS iterations fit in a session, and a
     gate that takes 13+ minutes per cycle (with live-LLM tests in
     scope) destroys cadence. The alternative — silently skipping
     slow tests — is worse: it hides regressions in exactly the
     expensive integration paths we most want to keep green. TIA
     catches everything the immediate change breaks; the full-suite
     gate at coarser intervals catches cross-module drift TIA misses.

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
- **Artifacts come from tests.** Leaderboard data points,
  performance numbers, golden outputs, screenshot baselines,
  benchmark scores — anything checked into the repo that's a
  *result* — must come from a test that pins its shape. Ad-hoc
  scripts that produce numbers without a test_spec are forbidden:
  re-running the script silently yields different numbers because
  no contract pins what "the same artifact" means. Concretely:
    - A campaign that produces a leaderboard data point lives as a
      pytest test (often opt-in / marked slow), not as a `bin/`
      script invoked by hand.
    - The test_spec declares: what config the run uses, what the
      result file path is, what fields the result MUST contain
      (n_games, mean_score type, etc.), and what tolerances apply
      (e.g. "mean_score >= 0 and is a finite float"). It does NOT
      assert a specific value — model noise is real — but it pins
      the *shape* so the artifact's structure is stable.
    - The test writes the artifact to its declared path as part of
      executing; checking in the artifact + the test together makes
      "what produced this number?" answerable by `git blame`.
    - Slow live-model tests (5+ min each) are opt-in via a pytest
      marker; the TIA per-cycle gate skips them; the coarser-gate
      sessions run them deliberately to refresh the leaderboard.
  Without this rule, the repo accumulates "raw numbers" that look
  authoritative but have no traceable lineage.
- **No silent bug fixes.** When a bug is discovered OUTSIDE a test run
  (manual probe, production observation, eyeballing logs, an agent
  noticing something looks off), the agent MUST:
    1. Write a `test_spec` that captures the bug as a behaviour
       contract — what behaviour was expected, what was observed.
    2. Write the matching test code. Run it; CONFIRM it reproduces
       the bug (RED, with the same error mode that was originally
       observed). If the test does not reproduce the bug, it does
       not actually pin the behaviour and is not yet a useful test.
    3. Only then fix the underlying code.
    4. Re-run the test; confirm GREEN.
    5. Commit the test + fix together so the audit trail is intact.
  A "silent fix" (code change without a corresponding test that
  would have caught the bug) is forbidden. The test suite must
  remember every bug we ever found, so the regression is never free
  to come back. This applies equally to import errors discovered
  while running a script, integration failures seen while running
  the bench live, and real-system observations from operations.

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

## Specs are language-agnostic

`test_spec_*.md` and `src_spec_*.md` files describe contracts that
implementations satisfy. The contract MUST be expressible without
naming the implementation language. Python `Protocol`, Go `interface`,
TypeScript `interface`, and Rust `trait` should all be valid targets
for the same spec.

Rules:

- Describe the **behaviour** ("a `ModelClient` sends messages and
  returns a reply containing content plus a structured tool_calls
  list"), not the syntax (do NOT write "a Python class implementing
  `typing.Protocol`...").
- Describe the **types in prose or table form**, not as a language
  literal (do NOT write "`def call(messages: list[dict], *, tools:
  list[dict] | None = None) -> AssistantReply`"). Prefer:

      `call(messages, tools)` accepts a sequence of message objects
      (each `{role, content}`) and an optional tool-schema sequence;
      returns a reply object with fields `content` (string) and
      `tool_calls` (sequence of tool-call objects, possibly empty).

- Cross-reference the implementation file path so the reader can jump
  from the language-agnostic contract to the current binding.

- When a contract spans a network boundary (HTTP, gRPC, queue
  message), include an **OpenAPI fragment** inline. OpenAPI is the
  one language-agnostic IDL allowed inside a Markdown spec; it
  carries enough detail for an implementer in any language to build
  a conforming client or server. Embed it as a fenced ` ```yaml `
  block.

Example: a port for an LLM chat call MAY be sketched in OpenAPI:

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

The point: a spec must remain useful when the implementation is
re-platformed (Python -> Go, monolith -> service, in-process port
-> HTTP). Code references and runnable examples may still be
language-specific — they are illustrations, not the contract.

## One test_spec per contract — across all binding modes

Per [ADR 0014](#) test_specs name their dependency-injection seam.
Per [ADR 0018](#) every runtime-boundary dependency has a Port +
production adapter + Fake + autouse binding. The natural consequence
is **one test_spec per contract** — not one test_spec per binding.

Concrete rule:

- A test that proves "main() returns AttemptResult shaped correctly"
  is ONE contract. It runs as a **unit test** against a Fake binding
  (autouse), as a **hermetic seam test** against the real production
  code under `@pytest.mark.no_fake` with a stubbed lower seam, and as
  an **e2e test** against the live production stack under
  `@pytest.mark.live`. Same contract, three bindings — **one
  test_spec**.

- The test_spec's "Model client injection point" subsection (or its
  more general "Sandbox injection point" equivalent) names how the
  test can be re-run under each mode.

- The test function MAY be parametrised over the binding:

      @pytest.mark.parametrize("binding", ["fake", "no_fake", "live"])
      def test_when_X_then_Y(binding, ...):
          ...

  or three separate functions sharing one spec file. The spec file is
  the contract record; the function count is an implementation detail.

- **DO NOT** write a "unit test variant" and a "live test variant" of
  the same contract under separate test_spec files. That is the
  duplication this rule rejects.

- **DO** keep separate test_specs when the contract genuinely differs
  per binding. Example: a live spec asserting "vLLM responds within
  5 minutes" is a real-stack-only contract — no fake equivalent. It
  gets its own spec because it tests something the fake cannot.

The reason: a contract that holds under the Fake but breaks under the
Live binding is a bench bug — not a "different test". Treating them
as the same test_spec with two bindings keeps the contract honest:
the unit run guards the bench code, the live run guards the integration.
A regression in either is the SAME spec breaking.

## One src_spec per contract — across all implementations

Mirror of the cycle-110 test_spec rule, applied to src_specs. Per
[ADR 0018](#) every runtime-boundary dependency has a Port +
production adapter + Fake. The Port IS the contract. Adapters MUST
conform to it.

Concrete rule:

- A Port (e.g. `CanonicalScorerPort`) gets ONE src_spec describing the
  contract: method signatures, return shape, error semantics, lifecycle
  guarantees, what the Port forbids (e.g. "MUST NOT raise on hostile
  input"). This is the document a Liskov violation refers back to.

- Adapter implementations — the Fake, the production InProcess, the
  Docker variant — do NOT get parallel src_specs duplicating the Port
  contract. The adapter file gets a module-level docstring naming the
  Port it implements; cross-cutting decisions (Docker isolation, image
  versioning, walltime sentinels) live in ADRs.

- Adapters MAY have their own src_spec only when they expose surface
  **beyond** the Port. Examples that justify an adapter src_spec:
  `FakeModelClient.calls` recording for test assertions;
  `DockerCanonicalScorer`'s `--cpus` and image-tag knobs that callers
  configure. The adapter src_spec then documents only that added
  surface and links to the Port src_spec for the contract proper.

- Entities (value objects, data types — `AttemptResult`,
  `BenchConfig`) keep their own src_specs: they ARE the contract;
  there's no separate Port.

- Use-case modules (orchestrators that wire Ports together, e.g.
  `run_loop`, `main`) keep their own src_specs: their contract is the
  composition, not any single Port.

The reason: duplicating Port semantics across N adapter src_spec files
is exactly the drift the "Git is the history" rule rejects. The Port
file is the contract record; the adapter file is HOW we cross the
seam. Their concerns don't overlap and shouldn't share spec prose.

When this matters:

- Adding a new adapter for an existing Port (cycle 109's
  `DockerCanonicalScorer` joining `InProcessCanonicalScorer` and
  `FakeCanonicalScorer` under `CanonicalScorerPort`): add the code
  file with a Port-naming docstring, write tests, do NOT create a
  parallel src_spec for the new adapter unless it adds caller-visible
  surface beyond `score()`.

- Refactoring an existing single-implementation module into a Port +
  adapter pair (cycle 109's split of `score_submission` into
  `CanonicalScorerPort` + three adapters): create the Port src_spec,
  delete the now-redundant adapter src_specs in place (per "Git is
  the history") rather than appending "Superseded by Port spec"
  notes.

## Git is the history; specs describe the current decision

ADRs, src_specs and test_specs describe **the current decision** and
**the current contract**, not the history of how either evolved. The
repository's git history is the durable record of every transition.
Don't duplicate it inside the spec files.

Concrete rules:

- **Don't write "Superseded by X" notes.** When an ADR is fully
  superseded, **delete the file**. Future readers find it via
  `git log -- docs/adr/<name>.md`.
- **Don't keep version-history blocks** ("Accepted v1 (cycle 72)…
  Superseded by v2 (cycle 76)… Superseded by v3 (cycle 79 + 80)").
  Rewrite the spec to describe only v3. `git blame` and
  `git log -p` show the v1 / v2 prose and when they changed.
- **Don't append amendment sections.** When a finding changes the
  decision, **rewrite the affected paragraphs in place**. Footnotes
  like "Cycle 95 amendment: actually we also need X" become noise as
  the file ages. Edit the body so it reads as the truth as of HEAD.
- **Cycle-number stamps inside spec prose are usually noise.** "(cycle
  77)" markers proliferate and rot. Keep them only when they orient a
  reader who needs to grep `git log --grep='cycle 77'` for the
  rationale. When in doubt, delete.
- **Cross-references stay.** Linking from one *current* document to
  another (`see [ADR 0003](...)`) is fine — that's the docs graph.
  Linking to a deleted ADR is broken; delete the link or rewrite the
  reference to whatever supersedes it.

The reason: spec files that accumulate "Superseded by", "Amendment N",
"Originally we did X, now we do Y" turn into archaeology. New readers
have to mentally diff to find the actual current state. Git already
solves that problem; we lose nothing by trusting it.

When this matters:
- Cleaning up after a refactor cycle: delete the superseded ADR
  rather than marking it "Status: Superseded".
- Resolving a deferred finding: edit the body to describe the
  resolved state rather than appending "Resolved by cycle N".
- Bumping a Dockerfile or runner version: the version header comment
  block (e.g. "v0.1 -> v0.2 -> v0.3 -> v0.4 with reasons") is one
  legitimate exception, since pinning the image-tag → semantics
  mapping is part of the contract, not history.

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

