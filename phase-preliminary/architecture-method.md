# Architecture method

How forge moves the architecture forward — the operating model
that links Phase E (gaps) to Phase F (experiments) to Phase H
(promotion to Level 1).

## The Level 1 / Level 2 trajectory model

Every capability (Phase B) and every technology service (Phase D)
has a **quality dimension** and two values along it:

- **Level 1** = as-is (how the dimension reads today).
- **Level 2** = to-be (the next planned value, with a metric delta
  that defines "reached").

A trajectory is a single L1 → L2 swing. There is no Level 3 in the
working tree — once Level 2 is reached, it *becomes* the new Level
1 and the prior Level 1 description is **deleted from docs**. The
next planned state becomes the new Level 2.

This is **forge's chosen approach to architecture**, declared
here in the Preliminary phase. Phase H operates the method (records
promotions, defines what "baggage" is, runs the brainstorm-
experiments meta-capability); Preliminary just declares it.

## Anti-patterns explicitly rejected

We do not maintain:

- `legacy/` tiers
- `Superseded by NNNN` cross-links
- `archive/` directories
- `Withdrawn` / `Deprecated` / `Closed` status flags

**Presence of text in the working tree means current; absence
means git history.** Every doc reads as if it has always been the
truth. A reader does not need to parse a status field to decide
whether to believe a sentence.

## Where trajectories attach

Trajectories attach to **service quality dimensions** (Phase D) or
**capability quality dimensions** (Phase B), not to components.
Replacing a component (e.g. vLLM 0.19.1 → 0.20) is just the next
step on the same trajectory; "Was vLLM 0.19.1" annotations do not
stay in the working tree.

This is the architecturally interesting consequence of the
method: the trajectory is the line; the component is the cursor on
the line. A new component is not a new architecture — it is the
architecture executing.

## Rationale

The method exists to keep the working tree small as the
architecture matures. Without delete-on-promotion, Phase D's
services pages would accumulate one paragraph per past component
generation, and the Level-1 description of each capability would
drift into a status log. By forcing the writer to delete on
promotion, every document stays at "what is true now."

The cost is that historical context lives only in `git log` /
`git blame`, not in the working tree. We accept that cost because
the alternative — a working tree that documents its own history —
makes the working tree itself unreadable at scale.

## md is source code; TDD applies

An extension landed in [ADR 0013](adr/0013-md-as-source-code-tdd.md):
any md that drives runtime behaviour (prompts the bench hands
to the model, role definitions LLM agents activate from,
process specs that decompose into steps, lab AGENTS.md, per-
capability quality specs) is source code, and the same TDD
discipline forge uses for code applies. Tests live at
`tests/<source-path>/test-<name>.md` mirroring the source
tree (Python unit-test convention). Tests are authored
*before* the md drives anything for the first time and stay
`RED` until the md's output passes them. Coverage levels
L0–L5 per md, defined inside each test file's preamble.

Verifier preference: mechanical (regex / parse / numeric) →
LLM-as-judge (a different role asked yes/no) → architect
eye-read. Eye-read is allowed but is a smell flag — too many
eye-read predicates means the test is not really a test.

This extension applies to the md kinds enumerated in
ADR 0013. README files, ADRs, and prose architecture docs
are documentation under review, not source under tests.

## How the method consumes the principles

The four [architecture principles](architecture-principles.md) are
the meta-constraints that decide which trajectories are valid:

- A trajectory whose Level 2 violates P3 (containers-only) is
  invalid even if its metric improvement is huge.
- A trajectory whose Level 2 requires breaking P1 (single
  architect) requires re-opening Preliminary first.
- And so on.

Phase F migration plans MUST cite the principles they affect, and
explicitly justify any near-violation.


## Measurable motivation chain (OKRs)
Per [P7](architecture-principles.md):

- **Driver**: forge needs a chosen architecture method
  (TOGAF + ArchiMate per ADR 0014); without an explicit
  method, every per-phase decision re-invents the wheel.
- **Goal**: Architect-velocity (one method, one trajectory
  rule, one delete-on-promotion convention).
- **Outcome**: trajectory model + delete-on-promotion are
  forge's load-bearing rules; audit P2 + P7 walk them.
- **Measurement source**: n/a — declarative: trajectory model + delete-on-promotion (consumed by P2 + P7)
- **Capability realised**: Architecture knowledge management
  ([../phase-b-business-architecture/capabilities/forge-level.md](../phase-b-business-architecture/capabilities/forge-level.md)).
- **Function**: Define-the-architecture-method.
- **Element**: this file.
