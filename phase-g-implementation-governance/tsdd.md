# TSDD methodology — bridging TOGAF documents to robust implementation (test-spec-driven development)

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

## The TSDD cycle (one iteration)

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
     Keep the 'Out of scope' list honest — everything not yet
     tested goes there.
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
         that drifted from the test_when_X_then_Y form; prune
         tested items from the "Out of scope" list.
       - src-spec: trim overpromises (anything no test exercises),
         consolidate paragraphs, refresh the "Out of scope" list.
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
  that no test exercises is a lie. Move it to 'Out of scope' or delete.
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
    src-spec/                         CODE-facing functional specs. One file
                                       per feature, named code_spec_<feature>.md
                                       so the role is unmistakable in the file
                                       listing.
      code_spec_<feature>.md
      <sub-area>/code_spec_<feature>.md
    tests-spec/                        CODE-facing test case specs. Mirrors
                                       src-spec/ structure. One file per
                                       feature, named test_spec_<feature>.md
                                       so the symmetry with code_spec is
                                       visible. Each entry is a test_when_X_then_Y
                                       contract with Arrange/Act/Assert detail,
                                       written per step 2 of the cycle.
      test_spec_<feature>.md
      <sub-area>/test_spec_<feature>.md
    tests/                             pytest implementations of tests-spec/.
      test_<module>.py
    src/                               clean implementation, generated to
                                       satisfy src-spec/. Symmetric to
                                       tests/ which satisfies tests-spec/.
      <module>.py

## Spec files are Markdown

Both `code_spec_*.md` and `test_spec_*.md` files MUST be valid
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

Per-feature spec files use a prefix that names the artifact's role:

    src-spec/<area>/code_spec_<feature>.md
    tests-spec/<area>/test_spec_<feature>.md

Both files map 1:1 to a feature. Reading the directory listing tells
the agent immediately which file is the code spec and which is the
test spec. No roll-up index file at the directory root is needed —
the folder structure plus the prefix is enough. Trying to maintain
a separate "index" file just adds another rotting artifact.

The corresponding implementation and test code files use:

    src/<area>/<feature>.py
    tests/<area>/test_<feature>.py

so the four artifacts for one feature have four predictable paths.

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
quarantined directory (per-lab convention — see lab AGENTS.md / TSDD.md)
and rebuild from tests via the cycle above. Rules:

  - Read the quarantined code to learn its observable behavior; do not
    import from it.
  - New code has no dependency on the quarantined code.
  - Each green cycle frees a slice of the quarantined code to delete.

Lab-specific quarantine paths and reverse-engineering notes live in
each lab's own TSDD.md.

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
conventions in <lab>/TSDD.md and reference this document at the top.
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
