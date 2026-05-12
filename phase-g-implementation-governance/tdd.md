# TDD methodology — bridging TOGAF documents to robust implementation

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

## The TDD cycle (one iteration)

Do all seven steps for ONE test case, then commit, then start the next.

  1. Pick the next behavior that advances the TOGAF documents under
     implementation (vision, capability, ADR, SPEC.md). Smallest unit
     that adds value is usually right; avoid scoping a single cycle
     beyond what fits in one paragraph of spec. Confirm scope with
     the user when ambiguous.
  2. Add ONE line to the test-spec file naming the case in
     test_when_X_then_Y form.
  3. Extend the matching spec only as far as the new test demands.
     Keep the 'Out of scope' list honest — everything not yet
     tested goes there.
  4. Write ONE pytest function in test_<module>.py using Arrange /
     Act / Assert. Function name matches the test case name from
     step 2.
  5. Run pytest. Red expected.
  6. Write the minimum code to make it green. Do NOT add validation,
     type coercion, error handling, or any other behavior beyond what
     the test asserts.
  7. Run pytest. Green. Commit with a message naming the cycle and
     the test case.

## Discipline rules

- Spec describes only what tests prove. Anything in a spec file that
  no test exercises is a lie. Move it to 'Out of scope' or delete.
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
    SPEC.md                            lab functional spec
    AGENTS.md                          operator interface
    spec/                              functional specs (mirror SPEC.md sections)
      <module>.md
      <sub-area>/<module>.md
    tests/
      specs/                           test case enumerations (mirror spec/)
        <module>.md
      test_<module>.py                 pytest, AAA bodies
    bench/ or src/ or <lab>/           clean implementation
      <module>.py

## Reverse-engineering legacy code

When a lab has legacy code that drifted from spec, move it to a
quarantined directory (per-lab convention — see lab AGENTS.md / TDD.md)
and rebuild from tests via the cycle above. Rules:

  - Read the quarantined code to learn its observable behavior; do not
    import from it.
  - New code has no dependency on the quarantined code.
  - Each green cycle frees a slice of the quarantined code to delete.

Lab-specific quarantine paths and reverse-engineering notes live in
each lab's own TDD.md.

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
Without discipline the gap leaks: implementation drifts from spec,
spec drifts from implementation, both drift from documented vision.
The test-spec → spec → test → code chain keeps every layer auditable
from any other. A change to a TOGAF document forces a change to spec,
which forces a change to test, which forces a change to code, which
surfaces in a commit. The cycle works in reverse too — a bug in
production forces a regression test, which forces a spec amendment,
which may force a TOGAF document amendment.

## Per-lab adoption

Each lab that follows this methodology should keep its lab-specific
conventions in <lab>/TDD.md and reference this document at the top.
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
