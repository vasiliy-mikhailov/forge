# Role: Concept-curator

## Purpose

Maintain `kurpatov-wiki-wiki`'s `data/concepts/` graph: create
new concept articles when a [source-author](source-author.md)
introduces a concept (`concepts_introduced` populated in the
source's frontmatter), update existing concept articles when a
new source touches them with new evidence, and keep the
`concept-index.json` consistent. One activation = one concept
slug operation (create OR update).

This role does NOT compile sources (`source-author`'s job).
It does NOT design the concept-graph schema (Wiki PM via
R-NN). It does NOT operate the host (DevOps). It curates the
shared concept graph that every source references.

## Activates from

The wiki-bench skill md
`https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/tree/main/skills/benchmark/SKILL.md`
loaded inside the
[wiki-bench harness](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/),
specifically the **concept-curation sub-Conversation** the
source-author triggers when a source's `concepts_introduced`
list is non-empty (per the SKILL's contract).

The activation hand-off:
`source-author` → emits `concepts_introduced: [slug-1, slug-2]`
→ wiki-bench harness opens a sub-Conversation → loads
`concept-curator` → produces or updates one concept.md per
slug → returns control to the source-author for the next
source.

## Inputs

- **The triggering source's `source.md`** (read-only) — the
  concept article must be consistent with how the source uses
  the concept (definitions, claims, attributions).
- **The existing concept article** at
  `data/concepts/<slug>.md` (read-only; absent for create
  operations).
- **The full `data/concepts/` directory + `concept-index.json`**
  — to detect duplicate slugs (`лимбическая-система` vs
  `limbic-system`) and to backfill cross-references.
- **The Wiki PM's R-NN rows** governing the concept graph
  (R-B-concept-graph-quality, R-B-dedup-correctness when those
  open).

## Outputs

- **One concept.md** at
  `data/concepts/<slug>.md` (create OR update), frontmatter +
  sections per the SKILL's concept schema (Definition / Source
  attributions / Related concepts / Open questions).
- **An updated `concept-index.json`** with the slug's entry
  (or a new entry for create operations). The harness commits
  this with the source.md's commit per K1's pattern.
- **Cross-reference backfills** — when a new concept introduces
  a relationship (`Related concepts: [other-slug]`), the
  concept-curator adds the reciprocal link to the
  `other-slug.md`'s Related concepts list.

No source.md edits (source-author owns those — including the
`concepts_touched` slugs for THIS concept). No grader edits.
No skill rewrites. No commits — the bench harness commits.

## Realises

- **Service operation** of `forge-level.md` — the concept-graph
  is the wiki's spine; without curation, sources either
  duplicate definitions or contradict each other.
- **Concept-graph quality** + **Dedup correctness** quality
  dimensions of [`develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md).

## Decision rights

The role may decide, without consultation:

- Slug naming for a new concept (within the SKILL's slug rules:
  lowercase, kebab-case, Latin or Cyrillic).
- Whether two candidate slugs collide (e.g., create
  `базовые-потребности` vs accept the source's
  `базовые-нужды` — semantically equivalent → create one,
  alias the other).
- Definition phrasing — within the SKILL's word-count budget
  and citation discipline.
- Which Related concepts to link to (bounded by the existing
  `data/concepts/` set; new concepts can introduce new
  Related entries, but only forward-pointing).
- When to escalate vs. resolve a contradiction between two
  source attributions of the same concept.

## Escalates to

- **A genuine concept-graph contradiction** (two sources cite
  conflicting definitions; both are otherwise verified) →
  surface to **Wiki PM** + **Architect** as an
  R-B-concept-graph-quality evidence row. Do NOT pick a side
  silently.
- **A slug-naming collision** that requires a project-wide
  rename → escalate to **Wiki PM** (rename touches every
  source that references the old slug — Wiki PM emits the
  R-NN, Developer ships the find-replace script, DevOps
  deploys via the bench branch).
- **A new schema field** the role wants in concept frontmatter
  (e.g. `confidence_score`) → Wiki PM territory.

## Capabilities (today)

- **OpenHands SDK** — runs as a sub-Conversation inside the
  source-author's parent Conversation (when KV-cache reuse
  lands per R-D-orchestration-kvcache, the sub-Conversation
  reuses the parent's prefix).
- **vLLM client** to wiki-compiler — same model backend as
  source-author.
- **`file_editor`** — writes concept.md to disk under
  `/runs/current/data/concepts/`.
- **`json_editor`** (or `file_editor` on a JSON file) —
  updates `concept-index.json`.
- **`web_search`** — fact-check tool, scoped to definition
  attributions only (the role is more conservative with
  web-search than source-author per the SKILL's tool budget).

The role does NOT have:

- Authority to delete a concept article (that's a Wiki PM call;
  the role can mark a concept stale via a frontmatter flag, but
  the deletion happens via R-NN closure).
- Authority to rename a slug (Wiki PM, see Escalations).
- Direct write access to `kurpatov-wiki-wiki`'s `main` branch.

## Filled by (today)

OpenHands SDK sub-agent inside `forge-kurpatov-wiki:latest`,
spawned from the source-author's parent Conversation per the
SKILL's contract. Today the sub-agent integration is L1 (a
stub that just writes a concept.md placeholder); L2 (real
integration with full concept-graph traversal) is queued as
the wiki-bench AGENTS.md L2 follow-up:

> "L2: real concept-curator OpenHands sub-agent integration.
> Current L1 stub … no agent loop — content quality follows
> claim quality."

## Tests

Transitively covered today by:

- `phase-c-…/wiki-bench/tests/synthetic/test_source_coordinator_integration.py`
  — exercises the source-author → concept-curator hand-off
  with a stub concept-curator that writes a placeholder
  concept.md. The real concept-curator's behaviour is the
  *target* of the next test layer (`test_source_coordinator_e2e.py`'s
  Skipped real-concept-curator block names this gap).
- `phase-c-…/wiki-bench/tests/synthetic/test_source_coordinator_e2e.py`
  Skipped block: real concept-curator OpenHands agent test
  (queued — L2 work).

Direct test md ([`/tests/phase-b-business-architecture/roles/test-concept-curator.md`](../../tests/phase-b-business-architecture/roles/test-concept-curator.md))
ships with 6 CC-NN cases. The runner
[`/scripts/test-runners/test-concept-curator-runner.py`](../../scripts/test-runners/test-concept-curator-runner.py)
scores against the real concept.md files in
`kurpatov-wiki-wiki/data/concepts/` (today 51 files). The
role's aggregate appears in the audit table with a real
number, not transitive `n/a`. Today: 6.98/8.0 = 0.873 PASS
(5 PASS / 1 italian-strike — CC-03's 58/101 forward-only-link
asymmetry surfaces as italian-strike, an honest signal the
graph needs back-link curation).

## Measurable motivation chain (OKRs)
Per [ADR 0015](../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1:

- **Driver**: TTS (a well-curated concept graph means a reader
  follows one link and gets the canonical definition, instead
  of re-reading definitions across 5 sources) + R&D throughput
  (the concept graph IS the wiki's mental model — every
  cross-source claim verification depends on it).
- **Goal**: TTS + Architect-velocity (Phase A).
- **Outcome**: Each concept.md the role ships is consistent
  with the source(s) that introduced or touched it; cross-
  references are bidirectional; no duplicate slugs sneak in;
  concept-index.json round-trips correctly.
- **Measurement source**: runner: test-concept-curator-runner (CC-NN cases against real concept.md graph; PASS band ≥ 0.8)
- **Capability realised**: Service operation
  ([`../capabilities/forge-level.md`](../capabilities/forge-level.md));
  Concept-graph quality + Dedup correctness
  ([`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)).
- **Function**: Curate-the-concept-graph-as-sources-arrive.
- **Role**: Concept-curator (this file).
