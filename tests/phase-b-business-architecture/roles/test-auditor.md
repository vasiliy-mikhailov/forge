# test-auditor — unit tests for the Auditor role

Pass/fail spec for the
[Auditor role](../../../phase-b-business-architecture/roles/auditor.md).
File path mirrors the source path of the role under
[ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md);
prefix `test-` per forge's unit-test convention.

## How tests are shaped here

Two kinds of test, both arrange / act / assert:

- **Inspection tests** read an artefact the role has produced
  (the latest `audit-<YYYY-MM-DD>.md` findings file) and check
  ONE property of it. Arrange = read the artefact. Act = parse
  the property. Assert = compare against expectation.

- **Decision tests** check ONE specific predicate the auditor
  applies. Arrange = a tiny inline fixture string with a known
  violation (or a clean control). Act = the predicate runs on
  the fixture. Assert = the finding list matches expectation.

Each test name describes its assertion (`test_<what>_<expected>`).
Each test has `Arrange`, `Act`, `Assert`, `Status` subsections.

`Status` is one of `GREEN` / `RED` / `SKIPPED`. SKIPPED is
distinct from GREEN: pre-condition not met. A GREEN test was
exercised and passed.

Decision tests for the Auditor are mostly mechanical (grep- and
parse-based, not LLM-judgement) — unlike test-wiki-pm where the
role's classification needs LLM review. So Decision tests here
can flip directly RED → GREEN through the verifier without an
external harness.

## Coverage targets

| Persona facet                                                        | Tests              |
|----------------------------------------------------------------------|--------------------|
| Output: `audit-<YYYY-MM-DD>.md` exists with body                     | I-AU-01, I-AU-02   |
| Output: report has the standard sections (FAIL / WARN / INFO)        | I-AU-03            |
| Output: every finding has predicate ref + rule + symptom + fix       | I-AU-04            |
| Output: summary totals match the count of individual findings        | I-AU-05            |
| Output: "Predicates walked" line lists every predicate exercised     | I-AU-06            |
| P6: detects "operations stack" / "capability stack" in scope         | D-AU-01            |
| P6: detects "is responsible for"                                     | D-AU-02            |
| P6: detects "agent" used as an org-unit role                         | D-AU-03            |
| P6: clean fixture using ArchiMate verbs produces no P6 finding       | D-AU-04            |
| P6: detects "drives" / "owns" used as relationship verbs             | D-AU-05            |

Coverage status: **L1** (all scenarios drafted; targeting L3 once
the verifier marks them GREEN).

## Tests

| ID       | Title                                                                           | Status |
|----------|----------------------------------------------------------------------------------|--------|
| I-AU-01  | audit_report_exists_at_canonical_path                                            | GREEN    |
| I-AU-02  | audit_report_nonempty                                                            | GREEN    |
| I-AU-03  | audit_report_has_FAIL_WARN_INFO_sections                                         | GREEN    |
| I-AU-04  | every_finding_carries_predicate_ref_and_proposed_fix                             | GREEN    |
| I-AU-05  | summary_totals_match_finding_counts                                              | GREEN    |
| I-AU-06  | predicates_walked_line_enumerates_predicates                                     | GREEN    |
| D-AU-01  | P6_detects_operations_stack_phrase                                               | GREEN    |
| D-AU-02  | P6_detects_is_responsible_for_phrase                                             | GREEN    |
| D-AU-03  | P6_detects_agent_used_as_org_unit                                                | GREEN    |
| D-AU-04  | P6_clean_archimate_fixture_produces_no_finding                                   | GREEN    |
| D-AU-05  | P6_detects_drives_and_owns_as_relationship_verbs                                 | GREEN    |

All `GREEN` after first run on 2026-04-30 — see
`test-auditor-verifier.py`. 11 PASS, 0 FAIL, 0 SKIP. The TDD
cycle worked: the first run caught one test-spec issue (I-AU-04
required `Rule.` on every finding, but INFO findings legitimately
lack `Rule.`) — fix was to (a) clarify audit-process.md output
format for INFO shape and (b) make the verifier section-aware.
Verifier is the derived runner per the smoke.md → smoke.sh
pattern, applied to role tests.

---

## I-AU-01 test_audit_report_exists_at_canonical_path

### Arrange

Path:
`phase-h-architecture-change-management/audit-<YYYY-MM-DD>.md`,
where `YYYY-MM-DD` is the most recent date for which an audit
exists. No pre-condition.

### Act

Verifier scans `phase-h-architecture-change-management/` for any
file matching `audit-\d{4}-\d{2}-\d{2}\.md` and selects the one
with the latest date.

### Assert

At least one such file exists.

### Status

`GREEN`.

---

## I-AU-02 test_audit_report_nonempty

### Arrange

The latest audit report from I-AU-01.

### Act

Count non-blank lines.

### Assert

≥ 30 non-blank lines.

### Status

`GREEN`.

---

## I-AU-03 test_audit_report_has_FAIL_WARN_INFO_sections

### Arrange

Latest audit report. The audit-process spec mandates three
verdict sections (FAIL / WARN / INFO) per the output format.

### Act

Search for `## Findings — verdict FAIL`, `## Findings — verdict
WARN`, `## Findings — verdict INFO` headers (Markdown level 2).

### Assert

All three headers are present (case-insensitive on the verdict
keyword; one occurrence each is sufficient — empty sections are
allowed if a verdict has no findings).

### Status

`GREEN`.

---

## I-AU-04 test_every_finding_carries_predicate_ref_and_proposed_fix

### Arrange

Latest audit report. Per audit-process output format, every
finding (`### F<N>. …`) must have:

- `Predicate: P<NN>.` line.
- `**Symptom.**` paragraph.
- `**Rule.**` paragraph.
- `**Proposed fix or escalation.**` (or equivalent — "Note." for
  INFO findings is allowed).

### Act

Parse each `### F<N>. …` block; verify the four required tokens
appear in the block (in any order).

### Assert

Every finding satisfies all four tokens. INFO findings may
substitute "**Note.**" for "**Proposed fix or escalation.**".

### Status

`GREEN`.

---

## I-AU-05 test_summary_totals_match_finding_counts

### Arrange

Latest audit report. Summary table at the end has rows
`FAIL <n> | WARN <n> | INFO <n>`.

### Act

Count `### F<N>.` entries per verdict section; cross-check with
the summary-table values.

### Assert

Per-verdict counts match.

### Status

`GREEN`.

---

## I-AU-06 test_predicates_walked_line_enumerates_predicates

### Arrange

Latest audit report. Output format mandates a "Predicates
walked: P1, P2, …" line near the top.

### Act

Search for the line `Predicates walked:` and parse the predicate
IDs that follow.

### Assert

Line exists; ≥ 1 predicate ID present (the audit-process spec
defines P1–P13; if the auditor walked a subset, the line still
must enumerate it).

### Status

`GREEN`.

---

## D-AU-01 test_P6_detects_operations_stack_phrase

### Arrange

Inline fixture (verbatim, in-memory string used by the verifier;
no fixture file):

> "The wiki line's operations stack — what wiki-* labs do per
> product."

This phrase appears in two real forge files
(`products/wiki-product-line.md`, `products/README.md`) and was
flagged as F12 in `audit-2026-04-30.md` — Decision test verifies
the predicate alone catches it.

### Act

Verifier invokes its inline implementation of predicate P6 (a
multi-pattern grep) against the fixture string.

### Assert

P6 returns ≥ 1 finding mentioning "operations stack".

### Status

`GREEN`.

---

## D-AU-02 test_P6_detects_is_responsible_for_phrase

### Arrange

Inline fixture:

> "The Wiki PM role is responsible for emitting requirements
> into the catalog."

ADR 0014 forbids "is responsible for" as a relationship verb;
the typed equivalent is "*is assigned to*" (Assignment) or
"*realizes*" (Realization).

### Act

P6 against the fixture.

### Assert

P6 returns ≥ 1 finding mentioning "is responsible for".

### Status

`GREEN`.

---

## D-AU-03 test_P6_detects_agent_used_as_org_unit

### Arrange

Inline fixture:

> "The Wiki PM agent emits R-NN rows into the catalog."

ADR 0014 forbids "agent" as an org-unit type. The typed
equivalent is **Business Actor** (the actor) + **Role** (the
function); informally "agent" is allowed only as the actor's
casual name.

### Act

P6 against the fixture, configured to flag the `<term> agent`
construction when used in the subject of a sentence (i.e., as if
"agent" were an org-unit type).

### Assert

P6 returns ≥ 1 finding mentioning "agent" used as a typed term.

### Status

`GREEN`.

---

## D-AU-04 test_P6_clean_archimate_fixture_produces_no_finding

### Arrange

Inline fixture using only ArchiMate 4 typed verbs:

> "The Wiki PM Role is assigned to the Wiki-requirements-collection
> Function. The Function realizes the Develop-wiki-product-line
> Capability."

### Act

P6 against the fixture.

### Assert

P6 returns zero findings.

### Status

`GREEN`.

---

## D-AU-05 test_P6_detects_drives_and_owns_as_relationship_verbs

### Arrange

Inline fixture:

> "The compiler component drives the publish step. The bench
> owns the catalog."

Both verbs are forbidden as relationship verbs per ADR 0014.
"Drives" can sometimes be a benign verb in non-relationship
contexts ("the engine drives") — the predicate's tolerance for
benign use is itself under test here.

### Act

P6 against the fixture, with the relationship-verb-detection
heuristic enabled (looks for `<noun> drives <noun>` and
`<noun> owns <noun>` patterns where both nouns are
forge-architecture-relevant words).

### Assert

P6 returns ≥ 2 findings (one per offending verb).

### Status

`GREEN`.

---

## Lifecycle

```
RED ──(test authored, not yet exercised)──▶ RED
RED ──(verifier passes)──────────────────▶ GREEN
RED ──(verifier returns no signal)───────▶ SKIPPED
GREEN ──(role definition changed; rerun fails)──▶ RED
GREEN ──(real artefact contradicts test)────────▶ STALE
STALE ──(test re-written with rationale)────────▶ RED
```

Status changes are commits with rationale, not in-place edits.
