# Audit process

The activation file for the
[Auditor role](../phase-b-business-architecture/roles/auditor.md).
A typed checklist of conformance predicates the audit walks; the
output is a `phase-h-architecture-change-management/audit-<YYYY-MM-DD>.md`
file with findings indexed `F1, F2, …` per the format below.

## When to walk

- Periodically (architect's call; today every ~5 days under
  active development).
- After a structural change to the rule set (a new ADR; a change
  to architecture-method.md or architecture-principles.md;
  introduction of a new phase folder).
- Before a major commit that the architect wants reviewed for
  rule conformance.
- When a downstream regression suggests the rules drifted from
  the working tree.

## Predicates

Numbered checks the auditor performs. Each predicate has an *id*,
a one-line *property* it asserts, the *signal* (mechanical or
judgement) used to test it, and the rule(s) the property derives
from. A predicate produces 0+ findings when violated.

### P1 — Architect-of-record commit attribution

**Property.** All commits on `main` are authored by the architect
of record (single-architect-of-record principle).
**Signal.** `git log --format='%an' main | sort -u` returns one
identity (modulo bot identity used by Cowork).
**Rule.** [Architecture principle 1](../phase-preliminary/architecture-principles.md):
single architect.
**Verdict.** Anything other than the architect's identity = `WARN`
(legitimate cases exist: agent commits with explicit
attribution); anything that *masks* the architect = `FAIL`.

### P2 — Capability trajectory completeness

**Property.** Every Capability file under
`phase-b-business-architecture/capabilities/` either declares its
*Quality dimensions* table with `Level 1 (today)` and
`Level 2 (next)` columns, or explicitly states "no active
trajectory."
**Signal.** Grep for "Quality dimensions" + table headers in each
capability file.
**Rule.** [Architecture method](../phase-preliminary/architecture-method.md)
trajectory model.
**Verdict.** Missing table without "no active trajectory" note
= `FAIL`.

### P3 — Containers-only deployment

**Property.** No deployment artefact in `phase-c-…/` or
`phase-d-…/` references a non-container runtime (systemd
unit running a Python process, a binary on bare metal,
etc.) without an explicit ADR exception.
**Signal.** Grep for `systemd`, `nohup`, `bare metal`, `pip
install` outside Dockerfile / compose contexts in lab `SPEC.md`
and lab AGENTS.md.
**Rule.** [Architecture principle 3](../phase-preliminary/architecture-principles.md):
containers-only.
**Verdict.** A non-container deployment without ADR justification
= `FAIL`.

### P4 — Single-server deployment

**Property.** No artefact references a second host beyond
`mikhailov.tech` without an explicit ADR exception.
**Signal.** Grep for hostnames; check that `mikhailov.tech` is
the only one in operational paths.
**Rule.** [Architecture principle 4](../phase-preliminary/architecture-principles.md):
single-server.
**Verdict.** Second host = `FAIL`; passing reference (e.g. a
Wikipedia URL or a Docker registry hostname) = ignore.

### P5 — md-as-source-code (ADR 0013): test coverage

**Property.** Every md file that drives runtime behaviour has at
least an `RED`-or-better md test under `tests/<source-path>/test-<name>.md`.
"Drives runtime behaviour" means: prompts, role definitions,
process specs, lab AGENTS.md, per-capability quality specs,
prompt skill files (per [ADR 0013](../phase-preliminary/adr/0013-md-as-source-code-tdd.md)).
**Signal.** For each runtime-md file, check the mirror path
exists in `tests/`.
**Verdict.** Missing test = `FAIL`. README, ADR, prose
architecture md (not runtime-driving) = ignore.

### P6 — ArchiMate 4 vocabulary (ADR 0014): forbidden vague verbs

**Property.** New prose in artefacts edited after 2026-04-30
does not contain the forbidden vague verbs / nouns: "is
responsible for", "drives" (as relationship verb), "owns" (as
relationship verb), "operations stack", "capability stack" (as a
file-shape name; "capability map" is OK), "agent" used as
org-unit (the typed term is *Business Actor* + *Role*).
**Signal.** Grep across forge for the forbidden patterns; cross-
check with `git log` mtime to apply only to files edited after
the ADR landed.
**Rule.** [ADR 0014](../phase-preliminary/adr/0014-archimate-across-all-layers.md).
**Verdict.** Forbidden term in a recently-edited file = `WARN`
(soft transition); in a new file = `FAIL`.

### P7 — Trajectory model: no status-flag accumulation

**Property.** No artefact contains "Superseded by", "Withdrawn",
"Deprecated", "Closed" status flags; no `legacy/` or `archive/`
directory exists.
**Signal.** Grep for those exact strings + `find -type d -name 'legacy'`.
**Rule.** [Architecture method](../phase-preliminary/architecture-method.md):
delete-on-promotion.
**Verdict.** Any hit = `FAIL`.

### P8 — AGENTS.md / CLAUDE.md symlink convention

**Property.** Every directory that has agent-context has both
`AGENTS.md` (the file) and `CLAUDE.md` (a symlink to AGENTS.md).
**Signal.** `find` for AGENTS.md, check `CLAUDE.md` sibling is a
symlink.
**Rule.** [`architecture-repository.md`](../phase-preliminary/architecture-repository.md).
**Verdict.** Missing symlink, or inverted (CLAUDE.md as file with
AGENTS.md symlink) = `FAIL`.

### P9 — Lab AGENTS.md follows canonical Phase A-H template

**Property.** Every lab AGENTS.md has the canonical
`## Phase A — …` through `## Phase H — …` headers per
[`../phase-g-implementation-governance/lab-AGENTS-template.md`](../phase-g-implementation-governance/lab-AGENTS-template.md).
**Signal.** Grep for the eight Phase headers in each lab's
AGENTS.md.
**Verdict.** Missing header = `FAIL`.

### P10 — ADR numbering monotonicity

**Property.** ADR numbers across forge are monotonic (no two
ADRs share a number; numbers proceed without gaps unless a
gap is annotated).
**Signal.** Collect all `NNNN-*.md` filenames under all `adr/`
folders; sort; check for duplicates / gaps.
**Verdict.** Duplicate = `FAIL`; gap = `INFO`.

### P11 — Cross-reference integrity

**Property.** Every relative markdown link in forge resolves
to an existing file or anchor.
**Signal.** Parse markdown links from each `.md`; for relative
paths, check the target file exists.
**Verdict.** Broken link = `FAIL`.

### P12 — Catalog row hygiene

**Property.** Every row in
[`../phase-requirements-management/catalog.md`](../phase-requirements-management/catalog.md)
has all required cells: ID matching `R-[ABDFR]-...`, Source,
Quality dim, Level 1, Level 2, Closure attempt, Status. Status
is one of `OPEN` / `CLOSED <date>`.
**Signal.** Parse the markdown table; assert per-cell rules.
**Verdict.** Malformed row = `FAIL`; missing closure-attempt for
an `OPEN` row = `WARN`.

### P13 — Test-suite verdicts present and documented

**Property.** Every md test file under `tests/` has its scenario
status table updated to match the verifier's last run output, OR
explicitly notes that the verifier hasn't been run since the
last edit.
**Signal.** Parse the test-file status table; cross-check with
`git log` of the verifier script + test md.
**Verdict.** Stale status (test file says GREEN but verifier
returns FAIL) = `FAIL`; missing status = `WARN`.

## Output format

```
# Forge docs audit — <YYYY-MM-DD>

Re-audit driven by: <one-line trigger>.
Predicates walked: <P1, P2, … list>.
Run by: <Auditor role / agent harness>.

## Findings — verdict FAIL

### F1. <one-line title>
Predicate: P<NN>. Path(s): <forge-relative path(s)>.
**Symptom.** <what was observed>
**Rule.** <which rule the symptom violates>
**Proposed fix or escalation.** <fix / "escalate"  >

### F2. …

## Findings — verdict WARN

### F<N>. …
(same shape as FAIL findings)

## Findings — verdict INFO

### F<N>. <one-line title>
Predicate: P<NN>. Path(s): <forge-relative path(s)>.
**Symptom.** <what was observed>
**Note.** <why this is noteworthy but not a violation; predicate
refinement, documented exception, etc.>

(INFO findings may omit **Rule.** and **Proposed fix.** because
they do not represent rule violations; the **Note.** paragraph
captures both why it's noteworthy and any follow-up action.)

## Summary

| Verdict | Count |
|---------|-------|
| FAIL    | <n>   |
| WARN    | <n>   |
| INFO    | <n>   |

Predicates walked: <list>.
Predicates skipped this run: <list with reason>.
```

## Operating rules

- **One walk → one file.** Each audit produces exactly one
  `audit-<date>.md`. Do not retroactively edit prior audits.
- **Findings live in the date-stamped file.** Closing a finding
  in a later audit is recorded in the *new* audit, not by editing
  the old one (per delete-on-promotion: each audit is itself a
  Plateau of audit state).
- **Predicates evolve.** When a class of finding repeats across
  audits, escalate to architect to either add a predicate to this
  file or open an ADR. Don't keep re-finding the same thing.
- **Verdicts have explicit definitions.** `FAIL` = unambiguous
  rule violation; `WARN` = likely violation, architect-callable;
  `INFO` = noteworthy but not a violation. Avoid using `WARN` for
  "I'm not sure"; that's an escalation.
