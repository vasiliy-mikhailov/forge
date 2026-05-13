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
  9. Run the FULL test suite (not just the new test). Confirm every
     previously-green test is still green. If any regressed, the
     refactor was not behavior-preserving — revert and try again.
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
in: `entities/`, `use_cases/`, `adapters/`, `frameworks/`, plus any
lab-specific cross-cutting groupings such as `architecture/` (for the
ast-walking dependency-direction tests) or `clean_arch/` (for layered
wire-up tests).

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

Mandatory architectural tests per lab:

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

