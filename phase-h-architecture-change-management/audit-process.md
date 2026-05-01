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

### P14 — Motivation chain present in role files

**Property.** Every role file under
`phase-b-business-architecture/roles/` (excluding README.md)
declares a `## Motivation chain` section per ADR 0015 decision
point 1, citing the Driver → Goal → Outcome → Capability →
Function → Role chain it serves.
**Signal.** For each role md, grep for `^## Motivation chain`.
**Rule.** [ADR 0015](../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1.
**Verdict.** Missing section = `WARN` (newly required; existing
roles transition on next edit). New role files added without the
section = `FAIL`.

### P15 — Catalog rows cite Goal or Driver in their Source cell

**Property.** Every Phase B / D row in
`phase-requirements-management/catalog.md` has a Source cell
naming a Phase A Goal (TTS / PTS / EB / Architect-velocity) or
a Driver (from `phase-a/drivers.md`), OR an upstream Phase F
closure (e.g. "G3 close-out").
**Signal.** Parse the Source cell of each row; check substring
match against the Phase A goal/driver names.
**Rule.** Architecture-method requirement-traceability +
ArchiMate Motivation chain (Driver → Goal → Requirement).
**Verdict.** Source cell empty or unrelated to the chain =
`WARN`.

### P16 — Per-product capabilities decompose from forge-level capabilities

**Property.** Every per-product capability file in
`phase-b-business-architecture/capabilities/` (other than
`forge-level.md` itself) cross-references one or more of the
four forge-level capabilities (R&D, Service operation, Product
delivery, Architecture knowledge management).
**Signal.** Grep for `forge-level.md` link in each capability
file.
**Rule.** ArchiMate Strategy domain decomposition; per
[`framework-tailoring.md`](../phase-preliminary/framework-tailoring.md)
forge organises capabilities hierarchically.
**Verdict.** Missing reference = `WARN`.

### P17 — Test cases have a Reward section per ADR 0015

**Property.** Every `## <ID> When … then …` case in a
`tests/phase-b-business-architecture/roles/test-*.md` file has
either a `### Reward` subsection (per ADR 0015 decision point
2) OR is explicitly marked `PENDING (no mechanical reward
function)`.
**Signal.** Parse case headers and check for the matching
`### Reward` subsection within the case body.
**Rule.** [ADR 0015](../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision points 2 + 3.
**Verdict.** Missing Reward + missing PENDING = `WARN` (newly
required; existing cases transition on next edit).

### P18 — Drivers explicitly influence Goals

**Property.** Every Driver in
`phase-a-architecture-vision/drivers.md` is connected to at
least one Goal in `goals.md` via either an explicit "influences
<Goal>" annotation or a parenthetical Goal reference.
**Signal.** Parse driver bullets; check for Goal name substring
in the bullet text.
**Rule.** ArchiMate Motivation domain (Driver → influences →
Goal); per spec §6.3.2.
**Verdict.** Driver without a Goal trace = `WARN` (the linkage
is currently implicit-prose).

### P19 — Goals have at least one realising Capability trajectory

**Property.** Every Goal listed in
`phase-a-architecture-vision/goals.md` has at least one
catalog row in `phase-requirements-management/catalog.md`
whose Source cell cites that Goal — i.e., the Goal is being
worked on, not aspirational-orphan.
**Signal.** Parse Goal names from goals.md; for each, search
catalog.md Source cells for the Goal name.
**Rule.** ArchiMate Motivation chain (Goal → realized by →
Capability trajectory) + architecture-method requirement
that goals decompose into trajectories.
**Verdict.** Goal with no realising trajectory = `WARN` (a Goal
may legitimately be deferred — see R-A-PTS / R-A-EB rows that
explicitly note their blockers; those are exempt).

### P20 — Token-density / no-bloat in operational md

**Property.** Operational md has no obvious token-bloat patterns:
no restate-context filler phrases ("As mentioned above", "As
stated earlier", "As we have seen", "To recap", "It is worth
noting that", "Please note that", "Needless to say", "In
conclusion"), no orphan headers (a `## ` or `### ` header
followed only by blank lines and then the next header — empty
section), and the file's own H1 title not restated as plain text
in the body.
**Operational md** = files under `phase-*/`, `tests/`, `scripts/`,
`tools/`, and lab paths whose contents drive an LLM agent's
behaviour or describe forge-authored architecture. Excludes the
carve-out below.
**Signal.** For each operational md path, regex-grep the filler-
phrase blacklist (case-insensitive); AST-scan for orphan headers;
re-search the H1 title text in the body.
**Carve-out.** Two carve-outs:

1. *Downloaded standards* — files under `**/standards/**`,
   `**/vendor/**`, `**/external/**`, or any md whose first
   non-blank line is the HTML comment
   `<!-- standard: external -->`. These are reference material,
   not forge-authored operational text.
2. *Synthetic test fixtures* — files under
   `tests/**/synthetic/**`, or any md whose first non-blank
   line is the HTML comment `<!-- p20: deliberate-bloat-fixture -->`.
   Such files exist precisely to violate P20 so the runner can
   test the predicate algorithm; flagging them in live walks
   would be permanent noise.
**Rule.** [Driver "Token-count bloat in operational md"](../phase-a-architecture-vision/drivers.md);
realises *Architect-velocity* (every additional minute the agent
spends re-reading filler is a minute not spent on real work) and
*TTS* (more tokens per task = more latency).
**Verdict.** ≥ 1 hit in operational md = `WARN` (file-level;
should be tightened on next edit). ≥ 3 hits in a single file =
`FAIL` (file is a bloat outlier and must be tightened in the
same commit that introduces or edits it). Hits inside fenced
code blocks are ignored — quoted prose is allowed to contain
the literal phrases.

### P21 — Score-history regression detection

**Property.** No agentic-behaviour test case has regressed since
its previous logged run. A regression is either a *verdict
regression* (PASS → PASS-italian-strike, PASS → FAIL, or
italian-strike → FAIL — the verdict ladder going the wrong way)
or a *score drop* (the case's normalised score `score/score_max`
dropped by ≥ 10% from the previous run, even if the verdict
held).
**Operational scope.** Walks the JSONL files under
`scripts/test-runners/.score-history/` (one per runner). A case
present in only one logged run cannot regress — first-run cases
are skipped.
**Signal.** For each runner-log file, parse rows; for each
`test_id` with ≥ 2 rows, compare the latest to the immediately-
previous. If verdict regressed OR score dropped ≥ 10%, emit a
finding naming the test_id, the two rows' verdicts, and the
score delta.
**Rule.** [ADR 0015 dec 5](../phase-preliminary/adr/0015-verifiable-agent-rewards.md):
"Score history tracked, not just current. Scores over time make
regression visible: a role whose corpus-observations.md goes
from 0.95 to 0.65 is regressing in quality even if PASS verdict
holds."
**Verdict.** Verdict regression (PASS → italian-strike, PASS →
FAIL, italian-strike → FAIL) = `WARN`. Score drop ≥ 10% with
verdict held = `INFO` (worth noting; not yet a quality
emergency). A case dropping below its declared threshold (FAIL)
is also caught by the runner's normal exit-code; P21 makes the
*trend* visible.

**Operational note.** Score-history rows are added only when a
runner is invoked with `--log-scores`. Interactive dev runs do
NOT pollute history. The architect's discipline: log scores at
the same cadence the audit walks (today, ~5 days under active
development; before & after each material edit to a role md or
runner).

### P22 — Aggregate scores per agentic-md unit reported in audit

**Property.** Each audit md carries a section
`## Aggregate scores per agentic-md unit` listing the latest
per-runner / per-lab aggregate score (ADR 0015 dec 6). The table
covers 11 units today: Architect, Auditor, Wiki PM, Developer,
DevOps, Source-author, Concept-curator, and each of the 4
lab AGENTS.md files (rl-2048, wiki-bench, wiki-compiler, wiki-ingest).
Each row carries: unit name, cases scored / total, aggregate
score (sum / max = normalised), band (`PASS` / `italian-strike` /
`FAIL`), per-verdict counts.
**Signal.** Grep the latest audit md for `^## Aggregate scores
per agentic-md unit$`; verify a markdown table follows with
≥ 11 data rows and ≥ 5 columns; verify the unit names are the
11 canonical ones.
**Helper.** The architect runs
`python3 scripts/test-runners/aggregate-scores.py` and pastes
the output into the audit. The helper reads
`scripts/test-runners/.score-history/<runner>.jsonl` (one row per
case, latest-only) — so the table reflects the most recently
*logged* run, not necessarily the most recent dev run. Discipline
per ADR 0015 dec 5: log scores at audit cadence.
**Rule.** [ADR 0015 dec 6](../phase-preliminary/adr/0015-verifiable-agent-rewards.md):
"A role's overall score is the per-case average. The Auditor
reports each role's aggregate score in audit findings."
**Verdict.** Missing section in latest audit = `WARN`. Section
present but row count < 6 or unit names don't match the canonical
list = `WARN` (drift from the agentic-md set).

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
Predicate: P<NN>  |  meta  |  P<NN>+P<MM>. Path(s): <forge-relative path(s)>.
**Symptom.** <what was observed>
**Note.** <why this is noteworthy but not a violation; predicate
refinement, documented exception, etc.>

(INFO findings may omit **Rule.** and **Proposed fix.** because
they do not represent rule violations; the **Note.** paragraph
captures both why it's noteworthy and any follow-up action.

The Predicate cell on INFO findings may be `P<NN>` (a specific
predicate hit), `meta` (an observation about the audit
process / predicate set itself, not about a specific rule
violation), or a list / sum of predicates (e.g. `P14+P19`)
when the finding spans multiple predicates.)

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
