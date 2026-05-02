# ADR 0013 — md is source code; TDD applies to it

**Phase.** Preliminary (architecture method extension).

**Status.** Accepted. (Architecture-method ADRs in forge are
accepted by the architect of record; no committee.)

**Date.** 2026-04-30.

## Context

Forge holds two kinds of executable artefact:

1. **Code that machines run** — Python in the wiki-bench
   coordinator, bash in `scripts/smoke.sh`, Dockerfiles, compose
   files. Tested by `tests/smoke.md` (prose model) → `smoke.sh`
   (derived script) per the existing TDD discipline in
   [`/tests/README.md`](../../tests/README.md).
2. **Markdown that LLM agents run** — the
   [`per-source-summarize.md`](../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/prompts/per-source-summarize.md)
   prompt the bench coordinator hands to the model, the
   [`wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
   process the Wiki PM role activates from, the
   [`wiki-pm.md`](../../phase-b-business-architecture/roles/wiki-pm.md)
   role definition itself, the lab `AGENTS.md` files, the per-
   capability quality-dimension specs, the persona files in
   [`/phase-b-business-architecture/roles/`](../../phase-b-business-architecture/roles/).

The first kind has been treated as code with tests for years.
The second kind has been treated as documentation — prose written
once, reviewed once, and never run against assertions. Several
recent regressions on the kurpatov-wiki product line traced
back to gaps in the second kind:

- A prompt rule that told the model "3-5 paragraphs of 100-200
  words" silently capped Лекция output at ~1000 words regardless
  of source length. No test caught it; the regression was found
  by eye-read.
- The bench-grade `extract_section()` regex used `\b` after a
  header that ends with `)`, silently zeroing `lecture_words`
  across the entire K1 v2 corpus. Treated as a code bug, but the
  *spec* (the bench-grade md) had no acceptance criterion that
  would have caught it.
- A persona file declared "the agent must escalate schema
  changes" — a sentence with no test backing. An agent following
  the persona could quietly change schema and pass review.

Each regression was costly because the artefact looked correct
when read — every md file Future-Vasiliy opens reads as if it
has always been the truth (the
[architecture method's delete-on-promotion rule](../architecture-method.md)
makes that explicit). When a md file is wrong, there is no
artefact older or newer to compare against; the only signal is a
downstream regression. By then the cost is real.

The alternative is to apply TDD to md. Each md whose content
drives an LLM agent or pipeline is *source code in a different
syntax*; tests over its outputs make the contract falsifiable
before a regression hits production.

## Decision

**Every md file in forge that drives a runtime behaviour is
source code, and TDD applies to it.**

Concretely:

1. **Drives runtime behaviour** means the md is read by an LLM
   agent, a verifier script, or a downstream automation that
   makes a decision based on its content. Examples: prompts,
   role definitions, process specs, lab AGENTS.md, per-capability
   quality specs, prompt skill files in `.agents/skills/`,
   anything in `phase-requirements-management/`.

   *Not* covered: README files, ADRs themselves, prose
   architecture docs (vision, drivers, traceability), changelogs.
   Those are documentation about the system; their truth is
   verified by review, not by tests.

2. **Tests live under top-level [`/tests/`](../../tests/)**
   mirroring the source path of the md they cover, prefixed
   `test-`. Example:

   ```
   forge/phase-b-business-architecture/roles/wiki-pm.md
       └── covered by ──▶
   forge/tests/phase-b-business-architecture/roles/test-wiki-pm.md
   ```

   The mirror rule is the same as Python's unit-test convention
   (`tests/test_<module>.py`), extended across the forge
   repo. Each md that "is source code" has at most one
   `test-*.md` file at the mirrored location; multiple test
   scenarios live as `## T-<abbrev>-NN` H2 sections inside it.

3. **Test file shape** is documented inside each test file's
   preamble (Scenario / Fixture / Acceptance / Run / Status /
   Coverage map per scenario; lifecycle RED → GREEN → STALE).
   Forge does not put the convention in a single template file —
   each test file states its own convention because the
   discipline is "the file is the spec." See
   [`/tests/phase-b-business-architecture/roles/test-wiki-pm.md`](../../tests/phase-b-business-architecture/roles/test-wiki-pm.md)
   for the worked example.

4. **TDD lifecycle.** Tests are authored *before* the md drives
   anything for the first time. Tests stay `RED` until the md's
   driven output passes them, then `GREEN`. When the md changes
   and the rerun fails, back to `RED`. When evidence shows the
   test was wrong (the md's output passes the test but the
   downstream artefact is bad), the test goes `STALE` and is
   re-written with rationale.

5. **Tests are specs, not code.** A test md is a *behavioural
   specification*: each case states *when [condition] then
   [expected behaviour]* with sub-sections Set-expected-result,
   Arrange (input + agent), Act (send to agent, gather real),
   Assert (expected = real). For tests covering md that drives
   an LLM agent, these are called *agentic behaviour tests*.
   The test md does not contain code. Any code that mechanises
   the Act + Assert steps is a **runner** — a derived mechanism
   that lives under `scripts/test-runners/`, not under
   `tests/`. Runners are optional; manual execution by the
   architect is conformant.

6. **Coverage levels** are per-md, defined inside the test file:
   L0 (no tests) → L1 (≥ 1 scenario) → L2 (every Output line has
   a predicate) → L3 (every quality dimension + decision-right
   has a scenario) → L4 (every escalation has a falsifying test)
   → L5 (mechanical runner). Targets are stated in the md's role
   / process / capability description; missing the target without
   rationale is a defect.

7. **Verifier preference order.** When an acceptance predicate
   can be implemented mechanically (regex, parse, numeric
   comparison), it must be — that is the runner. When it cannot,
   LLM-as-judge (a *different* role asked yes/no) is the
   fallback. Eye-read is allowed but is a smell flag — too many
   eye-read predicates means the test is not really a test.

8. **Failure handling matches code TDD.** A failing test on main
   blocks merges that depend on it. A persona change that turns
   `GREEN` to `RED` reverts or the test is rewritten *and the
   reason is in the commit message*. No "test was wrong, deleted"
   commits; STALE → re-write with rationale.

9. **Transitive coverage of single-role process specs.**
   When a process spec md is exclusively activated from a
   single role's persona file (e.g.
   `phase-requirements-management/wiki-requirements-collection.md`
   is loaded only by the Wiki PM role; `phase-h-architecture-
   change-management/audit-process.md` is loaded only by the
   Auditor role), the role's tests transitively cover the
   process spec — if the spec changes and the role's outputs
   regress, the role's test catches it. No separate test md is
   required at the process-spec mirror path.

   This carve-out applies only when activation is
   single-role-exclusive. A process spec activated from two
   or more roles, or activated directly by a tool, needs its
   own test md at the canonical mirror path. The carve-out is
   recorded with each affected role: the role's persona file's
   `## Tests` section names the process spec it transitively
   covers.

## Consequences

**Positive.**

- Persona files become falsifiable. *"The Wiki PM role escalates
  schema changes"* moves from prose-aspiration to a predicate the
  next agent run is checked against.
- Prompts gain regression coverage. The Лекция prompt's "no
  length cap" decision is documented in
  [ADR 0013 of wiki-bench](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0013-python-coordinator-decomposition.md);
  a test on the prompt's output (compression ratio band, voice-
  preservation predicates) prevents the cap from sneaking back in.
- Process specs become executable. Each `S1-SN` step in the
  requirements process can carry an acceptance predicate; a
  rewrite that drops a step trips the test.
- Refactors of md become safe. The architecture method's
  delete-on-promotion rule means a refactor erases the prior
  state from the working tree. A test ensures the new state
  still satisfies what the prior state did — without a test, the
  refactor can silently regress.

**Negative — accepted.**

- More md to maintain. Every "driving" md gains a sibling test
  file. At single-architect scale this is cheap (one md, one
  test md), and it scales sub-linearly (one role test covers
  three scenarios).
- Test files can themselves be wrong. The `STALE` state is the
  failure mode — a test that passes on a bad artefact had a
  blind spot. Mitigated by the convention that any STALE event
  is logged with rationale and the rewrite is a commit, not an
  in-place edit.
- Some predicates are not mechanically checkable today. The
  preference order (mechanical → LLM-as-judge → eye-read) makes
  the gap explicit — every eye-read predicate is a candidate
  for replacement once a verifier pattern exists.

**Out of scope.**

- A central md-test runner. The lab `tests/smoke.sh` pattern is
  for code; role tests are evaluated per-test today (manually or
  by ad-hoc verifier). When the volume crosses a threshold (~10
  active md tests), the architect opens a Phase F experiment to
  introduce a runner. Building the runner before that is
  premature — it would be infrastructure with no consumers.
- Test coverage of pure documentation md (READMEs, ADRs, prose
  architecture). Those are not source code under this ADR. They
  are reviewed; if a README is wrong, the fix is to edit the
  README, not to write a test against it.

## Currently realised

- [`/tests/phase-b-business-architecture/roles/test-wiki-pm.md`](../../tests/phase-b-business-architecture/roles/test-wiki-pm.md)
  — first md test under this discipline. Three scenarios
  (T-WP-01 / T-WP-02 / T-WP-03), all `RED`. The
  [Wiki PM role](../../phase-b-business-architecture/roles/wiki-pm.md)
  is the first md the discipline applies to.

## Backward references

- [`../architecture-method.md`](../architecture-method.md) — the
  trajectory model + delete-on-promotion rule this ADR extends.
- [`../framework-tailoring.md`](../framework-tailoring.md) —
  forge's adopted vs skipped TOGAF concepts. md-TDD is an
  *adopted* engineering discipline applied to a TOGAF-shaped
  artefact set.
- [`/tests/README.md`](../../tests/README.md) — the existing
  smoke-test discipline; the kind of test in this ADR is added
  as a sibling kind there.
- [Wiki-bench ADR 0013](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0013-python-coordinator-decomposition.md)
  — the regression-driven motivation for several of the early
  failures cited in Context.


## Motivation chain

Per [P7](../architecture-principles.md) — backfit:

- **Driver**: md files drive runtime LLM behaviour; without
  TDD discipline, behaviour drift goes undetected.
- **Goal**: Architect-velocity (test-first ⇒ regressions land
  with the diff that introduces them, not weeks later).
- **Outcome**: every md driving runtime has a `tests/<path>/`
  test md; transitive coverage carve-out (dec 9) keeps the
  spec honest without N-fold duplication.
- **Capability realised**: Architecture knowledge management.
- **Function**: Drive-runtime-md-via-TDD.
