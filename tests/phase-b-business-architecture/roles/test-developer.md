# Test: Developer role

Agentic-behaviour tests for the
[Developer role](../../../phase-b-business-architecture/roles/developer.md)
per [ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md).
Cases use the When-Then-Set-expected-Arrange-Act-Assert shape
with a Reward function per
[ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md).

The runner that automates the executable subset lives at
[`/scripts/test-runners/test-developer-runner.py`](../../../scripts/test-runners/test-developer-runner.py).
Cases that require LLM-judgement-on-PR-text are PENDING until the
LLM-as-judge harness lands (mirrors the WP-07..14 path).

## DV-01 When the Developer commits, then the commit message names the experiment ID or R-NN row it serves

### Set expected result

The most recent commit on `main` whose author identity is
`vasiliy-mikhailov` AND whose changes touch any lab path under
`phase-c-…/application-architecture/<lab>/` carries one or more
of these substrings in its message body:

- `K[0-9]+` (Kurpatov-wiki experiment id)
- `G[0-9]+` (governance / GPU-experiment id)
- `R-[A-Z]-[a-z\-]+` (R-NN catalog row id)
- `ADR\s*\d+` (ADR cross-reference)

### Arrange

- **Input data.** `git log -1 --format='%s%n%b'` for the most
  recent commit that touched a lab path.
- **Agent.** Runner reads the git history directly (no agent
  invocation needed for this inspection).

### Act

- The runner extracts the commit message and runs the substring
  check.

### Assert

- **Expected.** ≥ 1 match against the substrings above.
- **Real.** Set of matches found.
- **Verdict.** PASS if ≥ 1 match.

---

### Reward

**Motivation reference.** Realises the *Outcome* "every shipped
diff traces back to its driver (R-NN row or experiment id)" —
rolls up to the *Architect-velocity* Goal: forge's audit can
trace work to its rationale without architect eye-read.

**Score components** (each 0/1):

- C1. ≥ 1 R-NN / experiment / ADR substring match in commit
  message.
- C2. The cited id resolves to an existing artefact (catalog
  row, experiment file, or ADR file).

**Aggregate.** Sum (range 0..2). **PASS threshold**: 2.
**Italian-strike band**: 1 (cited id but doesn't resolve).

## DV-02 When the Developer adds a feature, then a corresponding test was added in the same commit (TDD)

### Set expected result

For the most recent commit that touched a lab path, the diff
contains both:

- ≥ 1 added file under the lab's source tree (NOT under
  `tests/`), AND
- ≥ 1 added file under the lab's `tests/` tree

OR the commit message explicitly names a previously-existing
test that the new code makes green (`closes test:` or
`tests:` line).

### Arrange + Act

- Runner inspects `git diff-tree --name-status --no-commit-id
  -r HEAD` against the lab paths.

### Assert

- **Verdict.** PASS if (added source ∧ added test) OR commit
  message names existing test.

---

### Reward

**Score components** (each 0/1):

- C1. Added source file in lab.
- C2. Added test file in lab tests/ directory.

**Aggregate.** Sum (range 0..2). **PASS threshold**: 1.
**Italian-strike band**: 1 ≤ score < 2 (source without test or
test without source — TDD discipline broken).

## DV-03 When the Developer writes Python in a lab, then the file passes pytest collection

### Set expected result

Every `.py` file added to `phase-c-…/<lab>/{compact_restore,
tests/synthetic}` in the most recent lab-touching commit imports
without error AND `pytest --collect-only` finds it (when under
`tests/`) or imports it (when under source).

### Arrange + Act

- Runner walks added .py files; runs `python3 -c 'import …'`
  for source modules; runs `pytest --collect-only` for test
  files.

### Assert

- **Verdict.** PASS if all added files import / collect cleanly.

---

### Reward

**Score components** (each 0/1):

- C1. All added source modules import cleanly.
- C2. All added test files collect cleanly under pytest.

**Aggregate.** Sum (range 0..2). **PASS threshold**: 2 (binary —
broken Python ships nothing).

## DV-04 When the Developer ships a metric-producing change, then a score-history row was logged

### Set expected result

If the commit touches `scripts/test-runners/<runner>.py` OR
adds a `*_runner.py` file, then the corresponding
`scripts/test-runners/.score-history/<runner>.jsonl` shows
≥ 1 new row whose `git_commit` matches HEAD's short commit
hash.

### Arrange + Act

- Runner inspects `git log --name-only -1`; if a runner file
  was touched, reads the matching .jsonl, checks for HEAD
  short hash in the latest rows.

### Assert

- **Verdict.** PASS if no runner touched (vacuous), OR new row
  logged with matching commit hash.

---

### Reward

**Score components** (each 0/1):

- C1. If a runner was touched, ≥ 1 row in its .jsonl carries
  HEAD's short hash. (Vacuous PASS if no runner touched.)

**Aggregate.** Sum (range 0..1). **PASS threshold**: 1 (binary).

## DV-05 When the Developer's diff crosses lab boundaries, then it must be escalated (no silent cross-lab edits)

### Set expected result

The most recent commit's set of `.py` / `.md` paths under
`phase-c-…/application-architecture/<lab>/` involves AT MOST
ONE lab. Cross-lab edits in a single commit are forbidden
without an explicit `cross-lab:` annotation in the commit
message body referencing an ADR.

### Arrange + Act

- Runner inspects `git diff-tree HEAD --name-only -r`; counts
  distinct lab roots touched.

### Assert

- **Verdict.** PASS if ≤ 1 lab touched, OR commit message has
  `cross-lab: ADR\s*\d+`.

---

### Reward

**Score components** (each 0/1):

- C1. Single-lab edit, OR cross-lab ADR cited.

**Aggregate.** Sum (range 0..1). **PASS threshold**: 1 (binary).

## DV-06 When the Developer commits, then the author identity is `vasiliy-mikhailov`

### Set expected result

Every commit on `main` is authored by `vasiliy-mikhailov` —
single-architect-of-record principle (architecture-principles.md
P1).

### Arrange + Act

- Runner reads `git log -1 --format='%an'`.

### Assert

- **Verdict.** PASS if author == `vasiliy-mikhailov`.

---

### Reward

**Score components** (each 0/1):

- C1. Author identity = `vasiliy-mikhailov` on most-recent
  commit.

**Aggregate.** Sum (range 0..1). **PASS threshold**: 1.

## Verdict lifecycle

```
PENDING → PASS (real == expected) | FAIL (real ≠ expected)
PASS → FAIL on regression; PASS → STALE if expected is wrong.
```

## Runner

[`/scripts/test-runners/test-developer-runner.py`](../../../scripts/test-runners/test-developer-runner.py).
