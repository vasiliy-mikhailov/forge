# Test: DevOps role

Agentic-behaviour tests for the
[DevOps role](../../../phase-b-business-architecture/roles/devops.md)
per [ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md).
Cases use the When-Then-Set-expected-Arrange-Act-Assert shape
with a Reward function per
[ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md).

The runner that automates the executable subset lives at
[`/scripts/test-runners/test-devops-runner.py`](../../../scripts/test-runners/test-devops-runner.py).

## DO-01 The operations log exists and is non-empty

### Set expected result

[`phase-g-implementation-governance/operations.md`](../../../phase-g-implementation-governance/operations.md)
exists and has ≥ 100 non-blank lines.

### Arrange + Act

- Runner stat()s the file and counts non-blank lines.

### Assert

- **Verdict.** PASS if file exists and ≥ 100 non-blank lines.

---

### Reward

**Score components** (each 0/1):
- C1. File exists.
- C2. ≥ 100 non-blank lines.

**Aggregate.** Sum (0..2). **PASS threshold**: 2.

## DO-02 The operations log carries dated entries in chronological order

### Set expected result

`operations.md` contains ≥ 1 line matching `^[*\-]\s*\d{4}-\d{2}-\d{2}` (a dated bullet) — DevOps writes one per
operational action.

### Arrange + Act

- Runner greps for the date pattern.

### Assert

- **Verdict.** PASS if ≥ 1 dated bullet found.

---

### Reward

**Score components** (each 0/1):
- C1. ≥ 1 dated entry present.
- C2. Latest dated entry is within 90 days of the audit walk
  (operational log is current, not archaeological).

**Aggregate.** Sum (0..2). **PASS threshold**: 1.
**Italian-strike band**: 1 (entries exist but stale).

## DO-03 Every host-level decision in operations.md cites an ADR

### Set expected result

For each line in `operations.md` that mentions one of the
governing keywords (`deploy`, `restart`, `rebuild`, `power-cap`,
`gpu`, `key`, `ssh`), the same paragraph contains an `ADR\s*\d+`
substring OR an explicit `R-[A-Z]-\S+` substring.

### Arrange + Act

- Runner walks paragraphs; for each governing-keyword paragraph,
  runs a substring check.

### Assert

- **Verdict.** PASS if ≥ 80 % of governing-keyword paragraphs
  cite an ADR or R-NN.

---

### Reward

**Score components** (each 0/1):
- C1. Citation rate ≥ 0.8.
- C2. ≥ 1 paragraph cites an ADR (not just R-NN).

**Aggregate.** Sum (0..2). **PASS threshold**: 1.
**Italian-strike band**: 1 ≤ score < 1.6 (some citation but
under-disciplined).

## DO-04 The operations log respects the ArchiMate vocabulary discipline

### Set expected result

`operations.md` does NOT contain forbidden ArchiMate-violation
phrases per [ADR 0014](../../../phase-preliminary/adr/0014-archimate-across-all-layers.md):
no `operations stack`, `capability stack`, `is responsible
for`, `<noun> drives the <noun>`, `<noun> owns the <noun>`,
`The X agent <verbs>`.

### Arrange + Act

- Runner runs the same `p6_findings(text)` regex set the
  Auditor uses (per `test-auditor-runner.py`).

### Assert

- **Verdict.** PASS if `p6_findings()` returns empty.

---

### Reward

**Score components** (each 0/1):
- C1. Zero P6 hits in operations.md.

**Aggregate.** Sum (0..1). **PASS threshold**: 1.

## DO-05 DevOps doesn't write app code (separation-of-duties from Developer)

### Set expected result

Commits whose message body contains `devops:` or `ops:` prefix
do NOT modify `.py` files under any `phase-c-…/<lab>/` source
tree (only allowed: lab compose files, lab Make targets, the
`operations.md` log, deploy scripts under `scripts/deploy/` if
present).

### Arrange + Act

- Runner walks recent commits; for each `devops:`-prefixed
  commit, checks the file list.

### Assert

- **Verdict.** PASS if no `devops:`-prefixed commit modifies
  app `.py` files. (Vacuous PASS if no `devops:` commits in
  history.)

---

### Reward

**Score components** (each 0/1):
- C1. No app-code modification under a `devops:` commit.

**Aggregate.** Sum (0..1). **PASS threshold**: 1.

## DO-06 The operations log respects token-density discipline (P20 carve-out doesn't apply)

### Set expected result

Per [P20](../../../phase-h-architecture-change-management/audit-process.md),
`operations.md` is operational md (not a downloaded standard,
not a synthetic test fixture). It must have 0 P20 hits today
(or ≤ 2; chronological logs accumulate filler over time, but
not at FAIL-rate).

### Arrange + Act

- Runner imports `p20_findings` from `test-auditor-runner.py`
  and runs it against `operations.md`.

### Assert

- **Verdict.** PASS if hits ≤ 2 (WARN band).

---

### Reward

**Score components** (each 0/1):
- C1. P20 hits ≤ 2 in operations.md.
- C2. P20 hits = 0 (preferred).

**Aggregate.** Sum (0..2). **PASS threshold**: 1.

## Verdict lifecycle

```
PENDING → PASS (real == expected) | FAIL (real ≠ expected)
PASS → FAIL on regression; PASS → STALE if expected is wrong.
```

## Runner

[`/scripts/test-runners/test-devops-runner.py`](../../../scripts/test-runners/test-devops-runner.py).
