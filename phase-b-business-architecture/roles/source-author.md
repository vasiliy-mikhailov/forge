# Role: Source-author

## Purpose

Compile a single raw transcript (`raw.json` from `kurpatov-wiki-raw`)
into a single source-level wiki article (`source.md` on
`kurpatov-wiki-wiki`'s `data/sources/<course>/<module>/<stem>.md`).
One raw → one source, with the structural-compliance contract
the [Wiki PM's R-NN trajectories](../../phase-requirements-management/catalog.md)
specify (TL;DR / Лекция / Claims / Concepts / Notes; provenance
markers; concepts_touched + concepts_introduced).

This role does NOT design the schema (Wiki PM's territory). It
does NOT operate the host (DevOps). It does NOT decide whether
the source is shippable (Auditor surfaces; Architect calls).
It compiles content. One source per activation.

## Activates from

The wiki-bench skill md
`https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/tree/main/skills/benchmark/SKILL.md`
loaded inside the
[wiki-bench harness](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/)
running the OpenHands SDK with the
[wiki-compiler vLLM endpoint](../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/)
as the model backend. One activation = one `<stem>` to compile.

## Inputs

- **Single `raw.json`** for the source under compilation
  (read-only from the bind-mounted `kurpatov-wiki-raw` vault).
- **`SKILL.md`** — workflow + output schema + tool repertoire +
  pass condition.
- **Concept-graph context** — already-published
  `data/concepts/*.md` and prior `data/sources/*.md` on the
  current bench branch (read-only). The role consults this to
  emit `REPEATED (from: …)`, `CONTRADICTS EARLIER (in: …)`, and
  `concepts_touched` slugs that are already in the graph.
- **The Wiki PM's R-NN rows** that govern the wiki under
  compilation (e.g. R-B-voice-preservation, R-B-compact-restore
  if shipping a compact-form source).

## Outputs

- **One `source.md`** at
  `data/sources/<course>/<module>/<stem>.md` on the bench
  branch, frontmatter + sections per the schema, with
  per-claim provenance markers (`NEW` / `REPEATED (from: …)` /
  `CONTRADICTS EARLIER (in: …)` / `CONTRADICTS FACTS`).
- **Updates to `concepts_touched`** in the new source's
  frontmatter — the slugs of concept articles the source
  references but does not introduce.
- **A pass-condition self-report** the bench harness's
  `verify_source.py` then independently confirms (per ADR 0010
  the artefact-on-disk wins over the agent's self-report).

No new concept articles (that's `concept-curator`'s job).
No grader edits. No skill rewrites (Architect / Wiki PM
territory). No commits — the bench harness commits under the
configured identity per K1's pattern.

## Realises

- **Service operation** of `forge-level.md` — the act of
  compiling one source-per-raw is the operational unit of wiki
  production.
- **Voice preservation** + **Reading speed** + **Concept-graph
  quality** quality dimensions of
  [`develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)
  — the role's output IS the wiki readers consume.

## Decision rights

The role may decide, without consultation:

- TL;DR phrasing within the schema's word-count budget.
- Section ordering inside Лекция (when the source's natural
  arc differs from the default).
- Whether a claim is `NEW` or `REPEATED` based on the
  concept-graph context the role read.
- Which `concepts_touched` slugs to emit — bounded by the
  existing `data/concepts/` set; coining a new slug is
  `concept-curator`'s call.
- Whether to run a web-search tool for fact-check on a single
  claim (within the SKILL's tool repertoire and rate limits).

## Escalates to

- **Schema violations** — if the SKILL is ambiguous on a
  structural point, surface to **Wiki PM** (who emits an R-NN
  to clarify; Architect approves).
- **A claim that should have a new concept article** — surface
  to **concept-curator** (the activation hand-off; the bench
  harness does this automatically when concepts_introduced is
  populated).
- **Voice-preservation regression** spotted during compile
  (e.g., the source reads as a generic summary, no Курпатов
  voice signature) — surface to **Wiki PM** + **Architect** as
  an R-B-voice-preservation evidence row; do NOT silently ship.
- **A pass-condition self-report that disagrees with
  verify_source's verdict** — escalate to **Developer** (the
  bench harness owner) as a possible test-fidelity gap.

## Capabilities (today)

- **OpenHands SDK** — runs inside the bench harness's
  sandboxed Docker container per
  [P3](../../phase-preliminary/architecture-principles.md).
- **vLLM client** to wiki-compiler — issues completion +
  tool-call requests against the served model
  (Qwen3.6-27B-FP8 / Llama-70B per the active
  `models.yml` config).
- **`file_editor`** — writes the source.md to disk under
  `/runs/current/`.
- **`task_tracker`** — multi-step compile workflow checkpointing
  per the SKILL's contract.
- **`web_search`** — fact-check tool, scoped to the claims with
  `fact_check_performed: true` in the source frontmatter.

The role does NOT have:

- Direct write access to `kurpatov-wiki-wiki`'s `main` branch
  (the bench harness commits to a per-run branch; the
  Mac-side curation Cowork session per [ADR 0007](../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0007-wiki-layer-mac-side.md)
  reviews + merges).
- Authority to change the SKILL md (Architect-only edit).
- Authority to add a new concept article — escalate to
  concept-curator.

## Filled by (today)

OpenHands SDK agent inside `forge-kurpatov-wiki:latest` on
mikhailov.tech, running the SKILL md activation. Tomorrow:
any LLM agent harness that supports the OpenHands tool-call
contract — the role definition is harness-agnostic on
purpose.

The role is filled per-activation, not continuously: each
`<stem>` to compile is a fresh Conversation; KV-cache reuse
across activations is an open R-D trajectory
(R-D-orchestration-kvcache).

## Tests

Transitively covered today by:

- `phase-c-…/wiki-bench/tests/synthetic/test_source_coordinator_*.py`
  — unit + integration + e2e tests against a stub source-author
  agent. The real source-author agent's behaviour is the
  *target* of these tests; the source-author role spec (this
  file) is what they're testing against.
- `phase-c-…/wiki-bench/tests/synthetic/test_verify_source_*.py`
  — pass-condition contract per ADR 0010-0011.

Direct test md ([`/tests/phase-b-business-architecture/roles/test-source-author.md`](../../tests/phase-b-business-architecture/roles/test-source-author.md))
ships with 6 SA-NN cases. The runner
[`/scripts/test-runners/test-source-author-runner.py`](../../scripts/test-runners/test-source-author-runner.py)
scores against the real source.md files in
`kurpatov-wiki-wiki/data/sources/` — the role's aggregate
appears in the audit table with a real number, not transitive
`n/a`. Today: 9.0/11.0 = 0.818 PASS (4 PASS / 1 italian-strike
/ 1 FAIL — the FAIL is a real artefact gap surfaced by SA-01:
the production source.md is missing the `language` frontmatter
field the template requires).

## Measurable motivation chain
Per [ADR 0015](../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1:

- **Driver**: TTS (each well-compiled source saves a reader's
  88-min lecture-watching time) + R&D throughput (every
  compiled source is a data point for the SKILL's quality
  measurements).
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: Each source.md the role ships matches the SKILL
  schema, preserves voice, marks provenance honestly, and
  passes verify_source.py without manual fix-up.
- **Measurement source**: runner: test-source-author-runner (SA-NN cases against real wiki source.md; PASS band ≥ 0.8)
- **Contribution**: runner: test-source-author-runner pass rate (per-test-case aggregate); each PASS reduces a pre-prod bug class for the source-author role; aggregate contributes to Quality KR pre_prod_share via the audit catch-rate side of the formula.
- **Capability realised**: Service operation + Product
  delivery ([`../capabilities/forge-level.md`](../capabilities/forge-level.md));
  Voice preservation + Reading speed + Concept-graph quality
  ([`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)).
- **Function**: Compile-one-raw-into-one-source.
- **Role**: Source-author (this file).
