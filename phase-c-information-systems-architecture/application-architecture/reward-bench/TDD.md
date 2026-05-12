# reward-bench TDD methodology

Anchor doc for the rebuild. Read this before touching code. Reads
SPEC.md for *what* the bench measures and this file for *how* we
rebuild it.

## Goal

Reverse-engineer the legacy implementation in _bak/ into clean code
under bench/ via test-driven development, one observable behavior at a
time. Tier 1 first; tiers 2-4 later. Interactive submission protocol
only (per SPEC.md Submission protocols section).

## The TDD cycle (one iteration)

Do ALL seven steps for ONE test case, then commit, then start the next.

  1. Pick the smallest next behavior. Read the relevant slice of
     _bak/ if you need to learn what the legacy code did. Confirm
     scope with the user when ambiguous.
  2. Add ONE line to tests/specs/<module>.md naming the test case
     in test_when_X_then_Y form.
  3. Extend spec/<module>.md only as far as the new test demands.
     Keep the 'Out of scope' list honest — everything not yet
     tested goes there.
  4. Write ONE pytest function in tests/test_<module>.py using
     Arrange-Act-Assert. The function name matches the test case
     name from step 2.
  5. Run pytest. Red expected.
  6. Write the minimum code in bench/<module>.py to make it green.
     Do NOT add validation, type coercion, error handling, or any
     other behavior beyond what the test asserts.
  7. Run pytest. Green. Commit with a message naming the cycle
     and the test case.

## Discipline rules

- Spec describes only what tests prove. Anything in spec/ that no
  test exercises is a lie. Move it to 'Out of scope' or delete.
- One test case per cycle. Do not pre-write large test enumerations.
- Test names are sentences: test_when_X_then_Y. One when-clause,
  one then-clause. If the name has two whens or two thens, split
  into two tests.
- Test bodies are Arrange / Act / Assert with those literal
  comments. Three blocks max.
- No code without a failing test. If the cycle requires touching
  bench/<module>.py without a corresponding red test, stop and
  pick a smaller behavior.
- Each commit covers exactly one cycle. The diff should be
  readable in one screen.

## When to stop a cycle

Stop and ask the user when:
- You discover a behavior in _bak/ that's clearly a bug. Decide
  with the user whether to pin it (preserve) or fix it (clean impl
  diverges from legacy).
- Two reasonable behaviors fit the test case. Spec ambiguity needs
  human resolution.
- The next smallest case would require infrastructure you do not
  yet have (e.g., a vLLM server, a real workspace, a docker
  sandbox). Decide whether to build the infrastructure first or
  shrink the scope further.

## Folder layout

  reward-bench/
    SPEC.md                          bench spec
    AGENTS.md                        operator interface
    TDD.md                           this file
    spec/                            cross-tier functional specs
      parser.md                      interactive protocol parser
      models/<name>.md               per-model bench addendums
      tier1/                         tier-1 functional specs
    tests/
      specs/                         test case enumerations (mirror spec/)
        SPEC.md
        parser.md
        models/
        tier1/
      test_parser.py                 pytest for cross-tier code
      tier1/                         pytest for tier-1 code
    bench/                           clean implementation
      parser.py                      cross-tier code
      tier1/                         tier-1 code
    _bak/                            legacy code; read only
    tasks/                           task definitions (2048, ...)

## Role of _bak

Legacy code lives at _bak/bin/ and _bak/test_*.py. Read it to
understand legacy behavior and to find regressions worth pinning.
Do NOT import from _bak. Do NOT extend _bak. New code in bench/
must be written fresh; bench/ has no dependency on _bak.

When a cycle is green and committed, the parts of _bak/ that
correspond to the now-covered behavior remain in _bak as
historical reference. Eventually we delete _bak entirely.

## Where to ask the user

Pause and ask when:
- A spec decision can change downstream tests (e.g., 'should empty
  name skip the call or raise?').
- A new model or family needs to be added.
- The cycle touches an architectural concern not yet in SPEC.md
  (then amend SPEC.md before writing code).
