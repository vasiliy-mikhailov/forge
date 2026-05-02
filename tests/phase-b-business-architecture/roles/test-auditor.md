# test-auditor — agentic behaviour tests for the Auditor role

Behavioural specification for the
[Auditor role](../../../phase-b-business-architecture/roles/auditor.md).
Path mirrors the source path of the role (per
[ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)).

## What an agentic behaviour test is

A test case states **when [condition] then [expected behaviour]**.
The test is the spec — not code. A separate *runner* (manual,
scripted, or LLM-as-judge) executes the case by setting up the
agent, sending the input, and comparing the agent's real output
against the expected result. The runner is a derived mechanism
and lives outside `tests/` (today: `scripts/test-runners/`).

Each case has four sections:

- **Set expected result** — what the agent should produce.
  Defined first so the spec is the spec.
- **Arrange** — bake in the input data; arrange the agent
  (which persona, which activation file, what state).
- **Act** — send the input to the agent; gather the real result.
- **Assert** — `expected = real`. Verdict is `PASS` / `FAIL` /
  `PENDING` (not yet run).

Cases are numbered `AU-<NN>`. There is no further classification
(no Inspection / Decision split) — the specification doesn't care
how the runner achieves verification.

[ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
extends each case with a `### Reward` section that scores the
agent's output against the role's Measurable motivation chain. Verdict
ladder: `PENDING` → `FAIL` (score < threshold) → `PASS-italian-strike` (threshold ≤ score < 0.8 × max) → `PASS` (score ≥ 0.8 × max). The italian-strike state surfaces agents that technically conform while producing thin work.

## Cases

| ID    | When … then …                                                                         | Verdict |
|-------|---------------------------------------------------------------------------------------|---------|
| AU-01 | When the Auditor walks the working tree, then it produces an `audit-<YYYY-MM-DD>.md` file. | PASS    |
| AU-02 | When the Auditor produces an audit, then the file has FAIL / WARN / INFO sections.    | PASS    |
| AU-03 | When the Auditor produces a finding, then the finding carries Predicate ID + Symptom + (Rule + Proposed fix for FAIL/WARN; Note for INFO). | PASS |
| AU-04 | When the Auditor produces an audit, then the Summary table totals match the per-section finding counts. | PASS |
| AU-05 | When the Auditor's input contains "operations stack", then it produces a P6 finding under verdict FAIL citing the phrase. | PASS |
| AU-06 | When the Auditor's input contains "is responsible for", then it produces a P6 FAIL finding. | PASS |
| AU-07 | When the Auditor's input contains "agent" used as an org-unit, then it produces a P6 FAIL finding. | PASS |
| AU-08 | When the Auditor's input contains only ArchiMate-typed verbs, then it produces no P6 finding. | PASS |
| AU-09 | When the Auditor's input contains "X drives Y" or "X owns Y" as relationship verbs, then it produces a P6 FAIL finding per offence. | PASS |

Verdicts last refreshed on 2026-04-30 by the runner at
[`/scripts/test-runners/test-auditor-runner.py`](../../../scripts/test-runners/test-auditor-runner.py).

---

## AU-01 When the Auditor walks the working tree, then it produces an `audit-<YYYY-MM-DD>.md` file

### Set expected result

A file matching `audit-\d{4}-\d{2}-\d{2}\.md` exists under
`phase-h-architecture-change-management/`.

### Arrange

- **Input data.** The forge working tree at `HEAD`.
- **Agent.** Cowork session loaded with
  [`auditor.md`](../../../phase-b-business-architecture/roles/auditor.md)
  as persona and
  [`audit-process.md`](../../../phase-h-architecture-change-management/audit-process.md)
  as activation. No prior audit on the same date in scope.

### Act

- The agent walks predicates P1–P13 against the working tree.
- The agent writes findings to a new
  `phase-h-architecture-change-management/audit-<YYYY-MM-DD>.md`
  file per the audit-process output format.

### Assert

- **Expected.** A file matching the date-stamped pattern exists.
- **Real.** Listing of `phase-h-architecture-change-management/`.
- **Verdict.** PASS if any such file exists.

---

### Reward

**Motivation reference.** Realises the *Outcome* "audit work product exists at the canonical path" — a precondition for any later case in this file. Rolls up to the *Architect-velocity* Goal.

**Score components**:

- C1. File matching `audit-\d{4}-\d{2}-\d{2}\.md` exists (1 pt)

**Aggregate.** sum.

**Score range.** 0..1.

**PASS threshold.** 1.

**Italian-strike band.** n/a (binary case; only PASS or FAIL).

## AU-02 When the Auditor produces an audit, then the file has FAIL / WARN / INFO sections

### Set expected result

The audit file contains all three section headers (Markdown
level-2): `## Findings — verdict FAIL`, `## Findings — verdict
WARN`, `## Findings — verdict INFO`. Empty sections are
permitted; the headers must be present.

### Arrange

- **Input data.** The latest `audit-<YYYY-MM-DD>.md` file in
  `phase-h-architecture-change-management/`.
- **Agent.** Already produced the audit (AU-01 PASS).

### Act

- Read the latest audit file.
- Search for the three required headers.

### Assert

- **Expected.** All three headers found.
- **Real.** Header search result.
- **Verdict.** PASS if all three found.

---

### Reward

**Motivation reference.** Realises a thoroughness sub-Outcome of "the audit produces a substantive report." An audit with 5 lines is technically valid but useless; the threshold of 30 lines is the minimum body that includes Predicates-walked + at least one finding + Summary.

**Score components**:

- C1. ≥ 30 non-blank lines (1 pt)

**Aggregate.** sum.

**Score range.** 0..1.

**PASS threshold.** 1.

**Italian-strike band.** n/a (binary).

## AU-03 When the Auditor produces a finding, then the finding carries Predicate ID + Symptom + (Rule + Proposed fix for FAIL/WARN; Note for INFO)

### Set expected result

Each `### F<N>. …` block in the audit:

- **FAIL or WARN section** — contains `Predicate: P<NN>`,
  `**Symptom.**`, `**Rule.**`, and `**Proposed fix or
  escalation.**` (or `**Proposed fix.**`).
- **INFO section** — contains `Predicate: P<NN>`,
  `**Symptom.**`, and `**Note.**` (Rule and Fix are optional
  for INFO since INFO findings do not represent rule
  violations).

### Arrange

- **Input data.** The latest `audit-<YYYY-MM-DD>.md`.
- **Agent.** Already produced the audit (AU-01 PASS).

### Act

- For each section (FAIL / WARN / INFO), parse all `### F<N>.`
  blocks.
- For each block, check the required tokens for its section's
  shape.

### Assert

- **Expected.** Every block conforms to its section's shape.
- **Real.** Per-block token check.
- **Verdict.** PASS if all blocks conform.

---

### Reward

**Motivation reference.** Realises the *Outcome* "every finding the audit emits is actionable" — without Predicate ID + Symptom + Rule (FAIL/WARN) or Note (INFO), the architect can't act on the finding.

**Score components**:

- C1. Per-section shape check across all findings (FAIL/WARN need pred+symptom+rule+fix; INFO needs pred+symptom+note) (1 pt)

**Aggregate.** fraction (well-formed / total).

**Score range.** 0..1.

**PASS threshold.** 1.

**Italian-strike band.** 0.7 ≤ score < 1.0 (most findings well-formed but some malformed; surfaces audits that are mostly-good but sloppy on some).

## AU-04 When the Auditor produces an audit, then the Summary table totals match the per-section finding counts

### Set expected result

The Summary table at the end of the audit declares totals like
`| FAIL | <n> |`. Those totals equal the count of `### F<N>.`
blocks in each verdict section.

### Arrange

- **Input data.** The latest audit file.
- **Agent.** Already produced the audit.

### Act

- Count `### F<N>.` blocks per verdict section.
- Parse the Summary table values.

### Assert

- **Expected.** Per-verdict counts match the table values.
- **Real.** Computed counts vs declared values.
- **Verdict.** PASS if all match.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the audit's totals are trustable." A summary table that disagrees with the in-section finding counts erodes architect confidence in the whole report.

**Score components**:

- C1. All 3 verdict counts match per-section ### F<N> blocks (1 pt)

**Aggregate.** sum.

**Score range.** 0..1.

**PASS threshold.** 1.

**Italian-strike band.** n/a (binary).

## AU-05 When the Auditor's input contains "operations stack", then it produces a P6 finding under verdict FAIL citing the phrase

### Set expected result

The audit's FAIL section contains a finding whose:

- `Predicate:` line names `P6`,
- `**Symptom.**` paragraph quotes (or paraphrases) the
  `operations stack` phrase from the input,
- `**Rule.**` paragraph references ADR 0014.

### Arrange

- **Input data.** A small body of text containing the verbatim
  string:

  > The wiki line's operations stack — what wiki-* labs do per
  > product.

  (This phrase appears in two real forge files
  `phase-b-business-architecture/products/wiki-product-line.md`
  and `…/products/README.md`; AU-05 isolates the predicate
  behaviour from any specific real file.)

- **Agent.** Cowork session loaded with `auditor.md` +
  `audit-process.md`. Predicate P6 is in scope of this run.

### Act

- The agent walks P6 against the input.
- The agent produces an audit (or appends to an existing one).

### Assert

- **Expected.** A FAIL finding citing P6 + "operations stack".
- **Real.** The finding(s) the agent produced for this input.
- **Verdict.** PASS if a matching finding exists.

---

### Reward

**Motivation reference.** Realises the *Outcome*
"architecture inconsistencies are surfaced before they
propagate" — rolls up to the *Architect-velocity* Goal
(Phase A). The score measures how thoroughly the audit
fulfils that Outcome on this single fixture.

**Score components** (each 0/1 unless noted):

- C1. Finding exists in FAIL section.
- C2. Predicate cell names `P6`.
- C3. Symptom paragraph quotes the phrase verbatim.
- C4. Rule paragraph cites ADR 0014.
- C5. Proposed-fix paragraph is concrete (≥ 10 words AND
  references at least one path / replacement term).
- C6. Proposed fix would actually resolve the violation
  (replacement term is one of: "capability map",
  "function", or another ArchiMate-typed element).

**Aggregate.** Sum (range 0..6).

**PASS threshold.** 3.

**Italian-strike band.** 3 ≤ score < 5.

**Score = 6.** Ideal — architect would not need to revise
the finding text before acting on it.

## AU-06 When the Auditor's input contains "is responsible for", then it produces a P6 FAIL finding

### Set expected result

The audit's FAIL section contains a finding citing P6 and the
phrase "is responsible for" (or its grammatical variants
"are responsible for").

### Arrange

- **Input data.**

  > The Wiki PM role is responsible for emitting requirements
  > into the catalog.

- **Agent.** Same as AU-05.

### Act

- Same as AU-05.

### Assert

- **Expected.** P6 FAIL finding citing the phrase.
- **Real.** The finding(s) the agent produced.
- **Verdict.** PASS if a matching finding exists.

---

### Reward

**Motivation reference.** Same as AU-05 — *Outcome* "architecture inconsistencies are surfaced before they propagate" rolling up to *Architect-velocity*. Different specific violation pattern ("is responsible for" vs "operations stack").

**Score components**:

- C1. Finding exists in FAIL section (1 pt)
- C2. Predicate cell names `P6` (1 pt)
- C3. Symptom paragraph quotes the phrase verbatim (1 pt)
- C4. Rule paragraph cites ADR 0014 (1 pt)
- C5. Proposed-fix paragraph is concrete (≥ 10 words AND references at least one ArchiMate verb such as `is assigned to`, `realizes`, `serves`) (1 pt)
- C6. Proposed fix replaces the forbidden phrase with the correct ArchiMate verb (Assignment / Realization) (1 pt)

**Aggregate.** sum.

**Score range.** 0..6.

**PASS threshold.** 3.

**Italian-strike band.** 3 ≤ score < 5 (finding present and predicate-cited but fix is vague or wrong).

## AU-07 When the Auditor's input contains "agent" used as an org-unit, then it produces a P6 FAIL finding

### Set expected result

The audit's FAIL section contains a finding citing P6 and the
incorrect use of "agent" as an org-unit type. ADR 0014's
typed equivalent is `Business Actor` (the actor) + `Role`
(the function); informal use of "agent" as a casual name for
the actor is permitted, but `<noun> agent <verb>` in subject
position (treating "agent" as a typed term) is forbidden.

### Arrange

- **Input data.**

  > The Wiki PM agent emits R-NN rows into the catalog.

- **Agent.** Same as AU-05.

### Act

- Same as AU-05.

### Assert

- **Expected.** P6 FAIL finding citing the construction.
- **Real.** The finding(s) the agent produced.
- **Verdict.** PASS if a matching finding exists.

---

### Reward

**Motivation reference.** Same as AU-05/AU-06. Specific violation: "agent" used as an org-unit type (per ADR 0014 the typed term is *Business Actor* + *Role*).

**Score components**:

- C1. Finding exists in FAIL section (1 pt)
- C2. Predicate cell names `P6` (1 pt)
- C3. Symptom quotes the input string (1 pt)
- C4. Rule paragraph cites ADR 0014 + the *Business Actor / Role* distinction (1 pt)
- C5. Proposed fix is concrete (1 pt)
- C6. Proposed fix splits the term into *Business Actor* (the LLM session) + *Role* (what it plays) (1 pt)

**Aggregate.** sum.

**Score range.** 0..6.

**PASS threshold.** 3.

**Italian-strike band.** 3 ≤ score < 5.

## AU-08 When the Auditor's input contains only ArchiMate-typed verbs, then it produces no P6 finding

### Set expected result

The audit's FAIL section contains zero P6 findings whose Symptom
references the input.

### Arrange

- **Input data.** A clean fixture using only ArchiMate 4 typed
  verbs:

  > The Wiki PM Role is assigned to the Wiki-requirements-
  > collection Function. The Function realizes the
  > Develop-wiki-product-line Capability.

- **Agent.** Same as AU-05.

### Act

- Same as AU-05.

### Assert

- **Expected.** No P6 finding cites this input.
- **Real.** The finding(s) the agent produced.
- **Verdict.** PASS if no P6 finding cites the input.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the auditor does not produce false-positive findings on clean inputs." An auditor that flags ArchiMate-typed prose as a violation costs architect time.

**Score components**:

- C1. Zero P6 findings on the clean fixture (1 pt)
- C2. No spurious findings under any other predicate (the runner does not over-trigger) (1 pt)

**Aggregate.** sum.

**Score range.** 0..2.

**PASS threshold.** 2.

**Italian-strike band.** n/a (any false positive on a clean fixture is FAIL, not partial credit).

## AU-09 When the Auditor's input contains "X drives Y" or "X owns Y" as relationship verbs, then it produces a P6 FAIL finding per offence

### Set expected result

The audit's FAIL section contains at least two P6 findings —
one for "drives" used as a relationship verb, one for "owns"
used as a relationship verb.

### Arrange

- **Input data.**

  > The compiler component drives the publish step. The bench
  > owns the catalog.

  Both verbs are forbidden by ADR 0014 as relationship verbs.
  ("Drives" can be benign in non-relationship contexts —
  "the engine drives" — but `<noun> drives the <noun>` in
  subject-verb-object form is the architecture-relationship
  reading.)

- **Agent.** Same as AU-05.

### Act

- Same as AU-05.

### Assert

- **Expected.** Two P6 FAIL findings (one per offending verb).
- **Real.** The finding(s) the agent produced.
- **Verdict.** PASS if at least two such findings exist.

---

### Reward

**Motivation reference.** Same as AU-06/AU-07. Two specific violations in one fixture (`drives`, `owns`).

**Score components**:

- C1. ≥ 1 P6 finding for `drives` (1 pt)
- C2. ≥ 1 P6 finding for `owns` (1 pt)
- C3. Each finding has Predicate=P6, Symptom quote, Rule cite (1 pt)
- C4. Each Proposed-fix replaces the verb with an ArchiMate-typed equivalent (`is assigned to`, `realizes`, `serves`, etc.) (1 pt)

**Aggregate.** sum.

**Score range.** 0..4.

**PASS threshold.** 2.

**Italian-strike band.** 2 ≤ score < 3.2 (one verb caught but the other missed, or the fix is vague).

## AU-10 When the Auditor walks P20 against a synthetic bloat fixture, then it produces ≥ 3 bloat-pattern hits

### Set expected result

The P20 algorithm, run against
[`tests/phase-h-architecture-change-management/synthetic/bloated-fixture.md`](../../phase-h-architecture-change-management/synthetic/bloated-fixture.md),
returns hits in at least three distinct categories:

- `filler-phrase` (≥ 1 hit; the fixture contains "as mentioned
  above", "please note that", "as we have seen", "to recap", "in
  conclusion"),
- `orphan-header` (≥ 1 hit; the fixture has 3 stacked
  `## Section with no content` / `## Another empty section` /
  `## Yet another empty section` headers),
- `repeated-title` (1 hit; the fixture restates its own H1
  "A deliberately bloated fixture" as plain text in the body).

### Arrange

- **Input data.** The synth fixture md at the path above. The
  fixture is opted out of live audit walks via the
  `<!-- p20: deliberate-bloat-fixture -->` marker on its first
  non-blank line; the runner bypasses the path-and-marker
  carve-out by calling `p20_findings(text)` directly so the
  *algorithm* is exercised even though the *walker* would skip
  the file.

- **Agent.** Same as AU-05.

### Act

- The runner reads the fixture text.
- The runner calls `p20_findings(text)` (the pure algorithm,
  no carve-outs).

### Assert

- **Expected.** ≥ 1 hit each in `filler-phrase`, `orphan-header`,
  `repeated-title` categories.
- **Real.** The list of `(category, match)` tuples the algorithm
  returned.
- **Verdict.** PASS if all 3 categories have ≥ 1 hit AND the
  algorithm returns no hits when re-run on a copy of the fixture
  whose first non-blank line is `<!-- standard: external -->`
  (carve-out respected).

---

### Reward

**Motivation reference.** Realises the *Outcome* "operational
md stays low-token-density so agents read fast and act on
signal, not filler" — rolls up to the *Architect-velocity* Goal
(Phase A) and to the *Token-count bloat* Driver
([phase-a/drivers.md](../../../phase-a-architecture-vision/drivers.md)).

**Score components** (each 0/1):

- C1. Filler-phrase category has ≥ 1 hit on the fixture.
- C2. Orphan-header category has ≥ 1 hit on the fixture.
- C3. Repeated-title category has 1 hit on the fixture.
- C4. Algorithm returns no hits when fed a copy of the same
  fixture body whose first non-blank line is the standards-
  carve-out marker (`<!-- standard: external -->`) — i.e.,
  the carve-out path is honoured.

**Aggregate.** Sum (range 0..4).

**PASS threshold.** 3.

**Italian-strike band.** 3 ≤ score < 3.2 (one of the four
checks failed but the predicate is broadly working).

**Score = 4.** Ideal — the algorithm catches all three bloat
categories AND respects the standards carve-out.

## AU-11 When the Auditor produces an audit, then it carries an "Aggregate scores per agentic-md unit" section with ≥ 6 canonical-unit rows

### Set expected result

The latest audit md under
`phase-h-architecture-change-management/audit-YYYY-MM-DD*.md`
contains:

- An exact heading line `## Aggregate scores per agentic-md unit`,
- Followed by a markdown table with ≥ 6 data rows,
- Whose first cell (Unit name) covers all 6 canonical units:
  `Auditor`, `Wiki PM`, `rl-2048 lab AGENTS.md`,
  `wiki-bench lab AGENTS.md`, `wiki-compiler lab AGENTS.md`,
  `wiki-ingest lab AGENTS.md`.

### Arrange

- **Input data.** The latest audit md (resolved by
  `latest_audit_path()` — same helper AU-01 uses).

- **Agent.** Same as AU-01 (the runner reads the audit md
  directly; this is an Inspection-style test, not a P6
  decision case).

### Act

- The runner finds the latest audit md.
- The runner greps for the heading and the 6 canonical unit
  names in the table's first column.

### Assert

- **Expected.** Heading present + 6 / 6 canonical units present
  in the table.
- **Real.** Set of unit names actually found.
- **Verdict.** PASS if ≥ 6 / 6 unit names match the canonical
  set; FAIL otherwise.

---

### Reward

**Motivation reference.** Realises the *Outcome* "the audit
makes the agentic-md test suite's overall health visible at a
glance" — rolls up to the *Architect-velocity* Goal (Phase A).
Per [ADR 0015 dec 6](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md),
each role's aggregate score belongs in the audit.

**Score components** (each 0/1):

- C1. Heading `## Aggregate scores per agentic-md unit`
  present in the latest audit.
- C2. A markdown table follows the heading.
- C3. The table has ≥ 6 data rows.
- C4. All 6 canonical unit names appear in the first column.

**Aggregate.** Sum (range 0..4).

**PASS threshold.** 4 (all four checks must pass — the section
is either present and well-formed, or it isn't).

**Italian-strike band.** none (binary).

**Score = 4.** Ideal — the architect ran
`aggregate-scores.py` and pasted the output before authoring
the audit.

## Verdict lifecycle

```
PENDING ──(case authored, runner not yet executed)──▶ PENDING
PENDING ──(runner executes, real == expected)───────▶ PASS
PENDING ──(runner executes, real ≠ expected)────────▶ FAIL
PASS    ──(persona / activation changed; rerun real ≠ expected)──▶ FAIL
PASS    ──(real artefact contradicts expected; spec was wrong)───▶ STALE
STALE   ──(case re-written with rationale)──────────▶ PENDING
```

A `STALE` event is the expensive signal — the spec was wrong
about what the agent should produce. Each STALE event is logged
inline below the affected case with a reference to the artefact
that exposed the gap.

## Runner

The runner that automates the executable subset of these cases
lives at
[`/scripts/test-runners/test-auditor-runner.py`](../../../scripts/test-runners/test-auditor-runner.py).
It implements the Act + Assert steps for cases that don't need
agent-level judgement (today: AU-01 through AU-09 — all
mechanically checkable since predicate P6 is grep-based).

The runner is *not* a test; it's a derived mechanism. Cases
that need agent judgement (none today for this role) would
require an LLM-as-judge harness or architect eye-read.
