# test-AGENTS — agentic behaviour tests for the wiki-ingest lab AGENTS.md

Behavioural specification for
[`/phase-c-information-systems-architecture/application-architecture/wiki-ingest/AGENTS.md`](../../../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/AGENTS.md).
Path mirrors the source path (per
[ADR 0013](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)).

## What an agentic behaviour test is

A test case states **when [condition] then [expected behaviour]**.
The test is the spec — not code. A separate *runner* (manual or
scripted) executes the case by inspecting the lab's `AGENTS.md`
file and comparing observed properties against the expected. The
runner is a derived mechanism and lives at
[`/scripts/test-runners/test-lab-AGENTS-runner.py`](../../../../scripts/test-runners/test-lab-AGENTS-runner.py).

Each case has four sections:

- **Set expected result** — what the lab AGENTS.md must contain.
- **Arrange** — bake in input (the AGENTS.md path); arrange agent
  (the runner reads the file).
- **Act** — runner parses; gathers real result.
- **Assert** — `expected = real`; verdict per ADR 0015 ladder.

Cases numbered `LA-WI-NN` (LA for Lab AGENTS, then
short slug to disambiguate per-lab).

## Cases

| ID            | When … then …                                                                                              | Verdict |
|---------------|------------------------------------------------------------------------------------------------------------|---------|
| LA-WI-01 | When the lab is active, then its `AGENTS.md` exists at the canonical path.                              | PASS    |
| LA-WI-02 | When the lab `AGENTS.md` exists, then it has all 8 Phase A–H headers from the canonical template.       | PASS    |
| LA-WI-03 | When the lab `AGENTS.md` exists, then it cross-links the canonical template (`lab-AGENTS-template.md`). | PASS    |
| LA-WI-04 | When the lab `AGENTS.md` exists, then every Phase header has at least one non-blank content line.        | PASS    |

Verdicts last refreshed by
[`/scripts/test-runners/test-lab-AGENTS-runner.py`](../../../../scripts/test-runners/test-lab-AGENTS-runner.py)
on the commit date.

---

## LA-WI-01 When the lab is active, then its AGENTS.md exists at the canonical path

### Set expected result

`/phase-c-information-systems-architecture/application-architecture/wiki-ingest/AGENTS.md` exists.

### Arrange

- Input data: forge working tree at `HEAD`.
- Agent: the runner reads the path.

### Act

Read the file via `pathlib.Path.exists()`.

### Assert

- Expected: file exists.
- Verdict: PASS if exists, FAIL otherwise.

### Reward

**Motivation reference.** Realises the *Outcome* "every active
lab carries its own agent-context document." Rolls up to the
*Architecture Knowledge Management* capability — single source
of truth.

**Score components**:

- C1. File exists at canonical path (1 pt).

**Aggregate.** Sum.
**Score range.** 0..1.
**PASS threshold.** 1.
**Italian-strike band.** n/a (binary).

---

## LA-WI-02 When the lab AGENTS.md exists, then it has all 8 Phase A–H headers

### Set expected result

The file contains all 8 canonical headers (`## Phase A — …` through
`## Phase H — …`) per
[`/phase-g-implementation-governance/lab-AGENTS-template.md`](../../../../phase-g-implementation-governance/lab-AGENTS-template.md).

### Arrange

- Input: lab AGENTS.md text.
- Agent: runner greps for header pattern.

### Act

Match `^## Phase [A-H] ` headers; count distinct phases.

### Assert

- Expected: 8 distinct phases present.
- Verdict per fraction (count/8); PASS if = 8.

### Reward

**Motivation reference.** Realises the *Outcome* "the TOGAF
phase scaffolding permeates from forge level to every lab."

**Score components**:

- C1. fraction = (distinct Phase headers found) / 8 (1 pt).

**Aggregate.** Fraction.
**Score range.** 0..1.
**PASS threshold.** 1.0 (all 8 required).
**Italian-strike band.** n/a (any missing phase is FAIL — no
partial credit on a structural template requirement).

---

## LA-WI-03 When the lab AGENTS.md exists, then it cross-links the canonical template

### Set expected result

The file contains a reference to
`lab-AGENTS-template.md` (any relative path; substring match).

### Arrange

- Input: lab AGENTS.md text.

### Act

`grep 'lab-AGENTS-template.md'` substring search.

### Assert

- Expected: ≥ 1 hit.
- Verdict: PASS if found.

### Reward

**Motivation reference.** Realises the *Outcome* "every lab
AGENTS.md is traceable to its canonical source" — single source
of truth for the agent-context format.

**Score components**:

- C1. Template cross-link present (1 pt).

**Aggregate.** Sum.
**Score range.** 0..1.
**PASS threshold.** 1.
**Italian-strike band.** n/a (binary).

---

## LA-WI-04 When the lab AGENTS.md exists, then every Phase header has at least one non-blank content line

### Set expected result

For each `## Phase X` header, the body between this header and
the next `## ` (or EOF) contains at least one non-blank line.
Empty Phase sections are not allowed — they're a smell ("we have
the header but no content").

### Arrange

- Input: lab AGENTS.md text + the 8 phase headers.

### Act

Per-phase: extract the body block, count non-blank lines.

### Assert

- Expected: every phase has ≥ 1 non-blank line.
- Verdict per fraction (filled/8). PASS if all 8 filled;
  italian-strike if 6-7 filled (justified for a young lab where
  some phases legitimately have no content yet); FAIL otherwise.

### Reward

**Motivation reference.** Realises the *Outcome* "the lab
AGENTS.md is substantive, not skeleton." A lab with empty
Phase sections is in italian-strike state at the AGENTS layer.

**Score components**:

- C1. fraction = (phases with non-blank body) / 8 (1 pt).

**Aggregate.** Fraction.
**Score range.** 0..1.
**PASS threshold.** 0.75 (6 of 8 phases filled).
**Italian-strike band.** 0.75 ≤ score < 1.0 (some phases
empty; surface for architect attention).

---

## Verdict lifecycle

```
PENDING ──(case authored, runner not yet executed)──▶ PENDING
PENDING ──(runner executes, real == expected)───────▶ PASS
PENDING ──(runner executes, real ≠ expected)────────▶ FAIL
PASS    ──(persona / lab AGENTS.md changed; rerun fails)─▶ FAIL
PASS    ──(real artefact contradicts expected; spec was wrong)──▶ STALE
STALE   ──(case re-written with rationale)──────────▶ PENDING
```
