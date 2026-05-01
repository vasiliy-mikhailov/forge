# Test: Concept-curator role

Agentic-behaviour tests for the
[Concept-curator role](../../../phase-b-business-architecture/roles/concept-curator.md)
per [ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md).
Cases use the When-Then-Set-expected-Arrange-Act-Assert shape
with a Reward function per
[ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md).

The runner that automates the executable subset lives at
[`/scripts/test-runners/test-concept-curator-runner.py`](../../../scripts/test-runners/test-concept-curator-runner.py).

Cases assert against the **real** concept.md files the role has
shipped to `kurpatov-wiki-wiki/data/concepts/` (today: 51 files).

## CC-01 Each shipped concept.md has the required frontmatter

### Set expected result

Every `*.md` under `kurpatov-wiki-wiki/data/concepts/` has YAML
frontmatter with at minimum: `slug`, `first_introduced_in`,
`touched_by` (list).

### Reward

**Score components** (per file, averaged):
- C1. Frontmatter present.
- C2. All 3 required fields present.

**Aggregate.** Sum / file count (range 0..2).
**PASS threshold**: 1.6.

## CC-02 Each shipped concept.md has a Definition section

### Set expected result

Every concept.md has a `## Definition` section (the role's
core output — the canonical definition the concept-graph
serves).

### Reward

**Score components** (per file):
- C1. `## Definition` heading present.

**Aggregate.** Sum / file count (range 0..1).
**PASS threshold**: 0.95 (allow 1 in-flight stub out of 51).

## CC-03 Concept-graph cross-references are bidirectional

### Set expected result

For every concept A whose `## Related concepts` section links
to concept B, B's `## Related concepts` (when present) must
contain a link to A.

### Reward

**Score components**:
- C1. Bidirectional ratio ≥ 0.5 (half of links round-trip;
  forward-only links allowed when B is more general than A).
- C2. Bidirectional ratio ≥ 0.8 (most links round-trip).

**Aggregate.** Sum (range 0..2).
**PASS threshold**: 1.
**Italian-strike band**: 1 ≤ score < 1.6 (some links round-
trip but the graph is asymmetric).

## CC-04 Every `first_introduced_in` slug resolves to a real source.md

### Set expected result

For every concept.md, the `first_introduced_in` frontmatter
field is a slug (`<course>/<module>/<stem>`); the matching
file at
`kurpatov-wiki-wiki/data/sources/<first_introduced_in>.md`
must exist.

### Reward

**Score components** (per file):
- C1. first_introduced_in slug resolves to existing source.md.

**Aggregate.** Sum / file count (range 0..1).
**PASS threshold**: 0.95.

## CC-05 No duplicate slugs across the concept directory

### Set expected result

`len(concept-md-files) == len({slug for each frontmatter})` —
no two files claim the same slug.

### Reward

**Score components**:
- C1. No duplicate slugs.

**Aggregate.** range 0..1.
**PASS threshold**: 1 (binary).

## CC-06 Self-attestation is consistent: the concept's own slug is in `touched_by`'s sources

### Set expected result

For every concept.md, the `first_introduced_in` value should
appear in the `touched_by` list (the introducing source touched
it by definition).

### Reward

**Score components** (per file):
- C1. first_introduced_in is in touched_by.

**Aggregate.** Sum / file count (range 0..1).
**PASS threshold**: 0.9 (allow 5 stubs out of 51).

## Verdict lifecycle

```
PENDING → PASS (real == expected) | FAIL (real ≠ expected)
PASS → FAIL on regression; PASS → STALE if expected is wrong.
```

## Runner

[`/scripts/test-runners/test-concept-curator-runner.py`](../../../scripts/test-runners/test-concept-curator-runner.py).
