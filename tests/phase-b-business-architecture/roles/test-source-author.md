# Test: Source-author role

Agentic-behaviour tests for the
[Source-author role](../../../phase-b-business-architecture/roles/source-author.md)
per [ADR 0013](../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md).
Cases use the When-Then-Set-expected-Arrange-Act-Assert shape
with a Reward function per
[ADR 0015](../../../phase-preliminary/adr/0015-verifiable-agent-rewards.md).

The runner that automates the executable subset lives at
[`/scripts/test-runners/test-source-author-runner.py`](../../../scripts/test-runners/test-source-author-runner.py).

Cases assert against the **real** source.md files the role has
shipped to `kurpatov-wiki-wiki/data/sources/` (today: 2 files
from K1-modules-005 + the K2 lecture-A track).

## SA-01 Each shipped source.md carries the required frontmatter fields

### Set expected result

Every `*.md` under
`kurpatov-wiki-wiki/data/sources/` (excluding `_template.md`)
has YAML frontmatter with at minimum: `slug`, `course`,
`module`, `source_raw`, `language`, `processed_at`,
`concepts_touched`, `concepts_introduced`.

### Reward

**Score components** (each 0/1 per file, averaged):
- C1. Frontmatter present.
- C2. All 8 required fields present (slug, course, module,
  source_raw, language, processed_at, concepts_touched,
  concepts_introduced).

**Aggregate.** Sum across files / file count (range 0..2).
**PASS threshold**: 1.6 (0.8 × max).

## SA-02 Each shipped source.md carries the required body sections

### Set expected result

Every shipped source.md has both a `## TL;DR` section and a
`## Claims` section. (`## Лекция` is queued but missing in
today's outputs; not required yet — flagged as italian-strike
band.)

### Reward

**Score components** (per file, averaged):
- C1. `## TL;DR` present (case-insensitive).
- C2. `## Claims` present.
- C3. `## Лекция` present (italian-strike component — not
  required yet, but lifts the score when present).

**Aggregate.** Sum / file count (range 0..3).
**PASS threshold**: 1.6 (allow C3 to be absent today).
**Italian-strike band**: 1.6 ≤ score < 2.4 (no Лекция).

## SA-03 Each source.md has at least one provenance marker

### Set expected result

Every shipped source.md contains ≥ 1 of: `NEW`, `REPEATED`,
`CONTRADICTS` (the per-claim provenance markers per the SKILL
schema).

### Reward

**Score components** (per file, averaged):
- C1. ≥ 1 NEW marker.
- C2. ≥ 1 REPEATED OR CONTRADICTS marker (cross-source
  provenance — italian-strike if absent).

**Aggregate.** Sum / file count (range 0..2).
**PASS threshold**: 1 (a brand-new source has no REPEATED yet
— C1 alone passes).

## SA-04 Every concepts_touched slug resolves to an existing concept.md

### Set expected result

For every shipped source.md, parse the `concepts_touched` YAML
list. Every slug must have a matching
`kurpatov-wiki-wiki/data/concepts/<slug>.md` file. (Cross-graph
integrity — same gate as wiki-bench's concept-link check.)

### Reward

**Score components** (per file):
- C1. Resolved-slug ratio ≥ 0.95 (allow 1 unresolved as
  in-flight).
- C2. Resolved-slug ratio = 1.000 (perfect).

**Aggregate.** Sum / file count (range 0..2).
**PASS threshold**: 1.

## SA-05 Each source.md path matches the slug-derived layout

### Set expected result

For every shipped source.md at path `data/sources/<X>/<Y>/<Z>.md`,
the frontmatter `slug` field equals `<X>/<Y>/<Z>` (without the
`.md` extension). The slug IS the path, modulo the `data/sources/`
prefix and the `.md` suffix.

### Reward

**Score components** (per file):
- C1. Slug matches path-derived expectation.

**Aggregate.** Sum / file count (range 0..1).
**PASS threshold**: 1.

## SA-06 Each source.md's `source_raw` field resolves to a real raw.json

### Set expected result

For every shipped source.md, the `source_raw` frontmatter
field points at an existing file under
`kurpatov-wiki-raw/`. (Provenance integrity — the source.md
must trace back to an actual transcript.)

### Reward

**Score components** (per file):
- C1. source_raw path resolves under the kurpatov-wiki-raw
  vault. (NFC/NFD-safe lookup.)

**Aggregate.** Sum / file count (range 0..1).
**PASS threshold**: 1.

## Verdict lifecycle

```
PENDING → PASS (real == expected) | FAIL (real ≠ expected)
PASS → FAIL on regression; PASS → STALE if expected is wrong.
```

## Runner

[`/scripts/test-runners/test-source-author-runner.py`](../../../scripts/test-runners/test-source-author-runner.py).
