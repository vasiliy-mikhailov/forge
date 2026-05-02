# D8 pilot — results & post-mortem

**Date:** 2026-04-26
**Branch:** `experiment/D8-pilot-2026-04-26-qwen3.6-27b-fp8`
**Wall:** 100.5 min for 7 sources (module 005, "Психолог-консультант")
**Driver:** `outputs/run-d8-pilot.py` (Python-loop top-orch + concept template v3)

---

## TL;DR

D8 pilot — **first end-to-end production GREEN** of module 005 on Qwen3.6-27B-FP8:
- 7/7 sources verified=ok
- Both architectural invariants hold (Python-loop top-orch bounded; concept template v3 produced)

Quality gap to Opus baseline:
- **claims -31% (90 vs 130)**, REPEATED **-64% (9 vs 25)**, fact-check citations **-33% (29 vs 43)**
- 34 cross-ref violations vs 5 for Opus — modelled `concepts_touched` slugs without backing concept files
- One unique advantage: video timestamps `[≈ MM:SS]` in concept articles (Opus doesn't produce these)

The architectural foundation works at production scale; quality gap is calibration territory + retrieval (D8 Steps 1-7).

---

## Architectural invariants — both PASS

### Invariant A — top-orchestrator context bounded

```
per-source orch events: [6, 6, 6, 6, 6, 6, 6]
```

Each iteration of the Python `for` loop creates a fresh `Conversation`,
state.events stays at 6 events per source (bound is 30; our limit is
99.8% headroom).

This is the regression test for D7-rev4-v2's 5/7 ceiling
(top-orch's task() returns accumulated to 8.93M cumulative tokens). The
Python-loop driver fixes it permanently.

### Invariant B — concept template v3 produced

```
concepts: 43 (template v3 violations: 1)
```

42/43 concepts pass the regex validator (`## Touched in sources` with
markdown back-link + 30-400 char excerpt + optional `[≈ MM:SS]`
timestamp). The single violation is `_template.md` baseline (`touched_by`
empty by design).

---

## Functional metrics vs Opus baseline (bench `2026-04-25-claude-opus-4-6-cowork`)

| Metric                      | Opus | D8 pilot | Δ      |
|-----------------------------|-----:|---------:|--------|
| sources_count               |    7 |        7 | =      |
| **claims_total**            |  **130** |  **90** | **-31 %** |
| claims_NEW                  |   99 |       77 | -22 %  |
| **claims_REPEATED**         |  **25** |   **9** | **-64 %** |
| claims_CONTRADICTS_FACTS    |    6 |        4 | -33 %  |
| claims_unmarked             |    0 |        0 | = ✅   |
| **fact_check citations**    |  **43** |  **29** | **-33 %** |
| **concepts_count**          |  **59** |  **42** | **-29 %** |
| notes_flagged               |   18 |        0 | -100 % |
| fact_check_performed_count  |    7 |        7 | = ✅   |
| **all_violations**          |   **5** |   **34** | **+580 %** |

### Where Qwen-27B closes/passes Opus
- `claims_unmarked = 0` — every claim marked, no orphans
- `fact_check_performed = 7/7` — every source ran factcheck
- `verified_ok = 7/7` — every source structurally compliant
- **Architectural invariants A+B** — entirely new wins not present in any Opus run

### Where Qwen-27B trails Opus

**Claim density** (-31 %).
Opus extracts ~1 claim per 35 s of transcript; we extract ~1 per 50 s.
Likely cause: source-author prompt asks for "all distinct claims" without
hard density target. The 27B model defaults to coarser bucketing on long
production transcripts. Mitigation: explicit `aim ≈ 1 claim per 60 s`
already in prompt; need to add
`for a 50-min lecture this is ≈ 50 claims, not 13`.

**REPEATED detection** (-64 %).
Opus catches 25 cross-source repeats; we catch 9. Root cause is the
core motivator for **D8 retrieval** (Steps 1-7): linear-scan of
`get_known_claims.py` doesn't surface paraphrases reliably even at
7-source scale. Embedding-based retrieval is expected to lift this
significantly (see D8-retrieval-spec.md).

**Wikipedia citations** (-33 %).
We ran factcheck.py on every empirical claim, but Opus emitted ~1.5
citations per claim while we emitted ~1. Likely the Opus run cites both
RU and EN Wikipedia URLs when both are returned; we pick best-only.
Cheap fix: source-author prompt — "if factcheck returns both ru.wiki
and en.wiki for same topic, cite both."

**Concepts and notes_flagged** are downstream of claims; closing the
claims gap should pull these along.

---

## 34 violations breakdown

### 24 cross-ref violations: `concepts_touched references missing concept '<slug>'`

Sources list slugs in `concepts_touched` frontmatter that have no
corresponding `wiki/data/concepts/<slug>.md` file. Examples:

```
000 Вводная: 'four-behavioral-perspectives', 'dominance-principle',
            'reticular-formation', 'self-preservation-instinct',
            'sexual-instinct', ...
002 1.1: 'three-instincts-model', 'instinct-terminology', ...
006 разбор: 'survivorship-bias', 'cause-effect-trap'
```

**Root cause:** source-author calls concept-curator only for
**newly-introduced** concepts (its own definition of "new"). But it
lists in `concepts_touched` *every* concept the lecture mentions, even
those that are paraphrases of an existing concept or that source-author
*could* have introduced but ran out of attention budget.

**Fix paths:**
- (a) source-author calls curator for **every** concept in
      `concepts_touched`, not just the introduced subset. If concept
      already exists in `wiki/data/concepts/`, curator's idempotent
      append-touched_by branch fires.
- (b) Source-author drops slugs from `concepts_touched` that don't have
      a real concept file by Step F.
- (c) **Best path (D8 retrieval):** before listing in
      `concepts_touched`, source-author runs `find_similar_concepts.py
      <slug>` — if found, use the existing slug; if not, create via
      curator. This closes the loop.

### 8 cross-ref violations: source slug not in `concept-index.processed_sources`

`concept-index.json` has a `processed_sources` array that source-author
should append to after writing source.md. Currently this isn't being
done.

**Fix:** add explicit step F.6 to source-author prompt:
```
After writing source.md to target_path, append the source slug to
wiki/data/concept-index.json's processed_sources list.
```

### 4 violations: `_template.md` is incomplete

The baseline `wiki/data/concepts/_template.md` doesn't have
`fact_check_performed`, `## Лекция`, etc — because it's a *concept*
template, not a *source* template. bench_grade.py mistakenly grades
`_template.md` as a source. **bench_grade fix:** skip `_template.md`
or filter `glob` to non-underscore-prefixed files.

---

## Sample audit (qualitative)

### Source 0 — high quality

`000 Вводная лекция. Базовые биологические потребности…md` (~21 KB):

- Frontmatter valid, slug correct
- `## TL;DR` — coherent paragraph (no bullets)
- `## Лекция` — 4 connected paragraphs with inline `[<concept-slug>](../../../concepts/<slug>.md)` references throughout
- `## Claims` — every claim ends with `[NEW]`, many have
  `Проверено: CONFIRMED/UNCERTAIN` notes paragraphs and Wikipedia URLs
- `## New ideas (verified)` — bullet list grouped by thematic_category
- `## All ideas` — flat bullet list

**Artifacts found:**
- One duplicate concept-link: `[трёхэтажная модель Маклина](.../triune-brain-model.md) ([triune-brain-model](.../triune-brain-model.md))` — model wrote two link instances back-to-back.
- `concepts_touched ≡ concepts_introduced` (19 each) — should be a
  strict subset; source-author treats every touched concept as
  introduced.

### Concept `dunbar-number.md` — template v3 working

vs Opus's `dunbars-number.md`:

| Aspect              | D8 pilot                           | Opus                                                                                                |
|---------------------|------------------------------------|-----------------------------------------------------------------------------------------------------|
| frontmatter         | `introduced_in` + `touched_by:1`   | `first_introduced_in` + `touched_by:3 (001, 003, 004)`                                              |
| Definition          | formal + 1 speaker quote           | formal + **journal citation** *Dunbar 1992, J. Human Evolution* 22(6):469–493 + Russian context     |
| Per-source coverage | 1 bullet (label + excerpt + `[≈ 18:52]`) ✓ | **3 sub-sections** `### <source-slug>` with multiple bullets per source on what each contributed    |
| Custom sections     | —                                  | `## How Kurpatov uses this`                                                                         |
| Related concepts    | inline list                        | inline + cross-links                                                                                |
| **Timestamps**      | **`[≈ MM:SS]` ✓**                  | **none**                                                                                            |

D8 wins on timestamps (Opus has none). Opus wins on multi-source breadth
(touched_by:3 vs 1), journal citations, per-source detail.

The 3-vs-1 touched_by gap maps directly to the 24 cross-ref violations
above and is the architectural fix for D8 next iteration.

---

## Calibration backlog (next iteration before D8 retrieval)

Sorted by impact:

1. **Curator update-existing-concept fix.** Source-author must call
   curator with the existing concept path even when not introducing —
   to add new `## Touched in sources` entry + extend `touched_by:`
   frontmatter. Closes 24 cross-ref violations and lifts touched_by
   coverage 3-fold.

2. **`processed_sources` update.** Step F.6 in source-author prompt.
   Closes 8 cross-ref violations.

3. **Density target in source-author prompt.**
   `Aim for ~1 claim per 60s. For a 50-minute lecture, that's ≈ 50 claims,
   not 13.` Targets the -31 % claims gap.

4. **Cite both ru/en Wikipedia URLs when both returned.** +33 % citation
   density expected.

5. **`concepts_introduced ⊂ concepts_touched`** — separate them
   explicitly. Source-author prompt should enumerate "introduced (new)"
   vs "touched (mentioned)" lists.

6. **bench_grade L1.5 patch:** skip `_template.md` from source grading.
   Closes 4 violations.

7. **Promote concept-template-v3 into `wiki/skills/benchmark/SKILL.md`.**
   Closes the original spec gap that motivated D7-rev4 audit. Should
   become section "Concept article template (mandatory)".

---

## What we proved at production scale

- **Python-loop top-orchestrator solves** D7-rev4-v2's 5/7 ceiling.
  Confirmed: 7/7 sources written, top-orch events constant per source.

- **Concept template v3 (backlinks + excerpts + timestamps) is
  achievable on Qwen-27B-FP8.** All 42 created concepts conform.

- **TaskToolSet (current OpenHands SDK) + 3-level orchestration
  (top → source-author → idea-classifier/fact-checker/concept-curator)
  scales to 7-source production runs.** No max_children cap, no
  spawn-once-reuse workarounds, no DelegateTool deprecations.

---

## Out-of-container caveat

This pilot ran on host Python venv
(`forge/labs/wiki-bench/tests/synthetic-orchestrator/.venv/`),
not inside the bench Docker image. This violates the forge-wide
"all work runs in containers" invariant (see
`outputs/forge-containers-policy.md` and lab AGENTS.md "Forge-wide
invariant" section).

The pilot's results (7/7 verified=ok, 90 claims, 9 REPEATED, 4 CF, 43
concepts, 100.5 min wall) are **valid as a TDD spike** — they prove the
Python-loop top-orch + concept template v3 architecture works end-to-end
on Qwen-27B-FP8. They are **NOT a canonical bench result** because:

- system packages (libssl, libblas, glibc, fonts) come from the host,
  not from a pinned Dockerfile;
- the venv has been mutated across iterations
  (`pip install` of openhands-sdk, sentence-transformers) without a
  lockfile;
- a fresh reviewer cannot replay this run in <30 min.

The branch `experiment/D8-pilot-2026-04-26-qwen3.6-27b-fp8` is therefore
a **spike artifact**, not a canonical experiment branch. It stays for
diff comparison.

**Canonical D8 pilot v2** must run inside the bench Docker image (D8
spec Step 0.3). Expected delta: ±5 % wall time from container overhead;
content identical (same vLLM endpoint).

## Sequencing for next steps

This order minimizes risk:

1. Calibration #1, #2, #3, #4, #5, #6 (above) — small prompt edits +
   one bench_grade patch. ~30 min coding, 80 min wall to validate.
2. Promote concept-template-v3 into SKILL.md (item #7).
3. **Re-run pilot** with calibrations applied. Expect: 0 cross-ref
   violations, claims_total ~110-120 (close to Opus 130), REPEATED
   ~12-15 (still trailing — wait for retrieval).
4. **D8 Steps 1-7 (retrieval)** — only after #3 lands. Solves the
   REPEATED -64 % gap and unlocks 200-source scale.

---

## Outputs (deliverables shipped this run)

- `outputs/0010-retrieval-augmented-dedup.md` — ADR
- `outputs/D8-retrieval-spec.md` — spec (Steps 0-7)
- `outputs/concept-template-v3.md` — concept template spec
- `outputs/step6_orchestrator.py` — Python-loop validation (synth)
- `outputs/step7_orchestrator.py` — Python-loop + concept v3 (synth GREEN)
- `outputs/run-d8-pilot.py` — production driver (this pilot)
- `outputs/AGENTS.md` — both invariants documented in lab memory
- `outputs/openhands-sdk-orchestration.md` — both invariants documented in skill
- **`outputs/D8-pilot-results.md`** — this document


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain inherited from the lab's AGENTS.md.
