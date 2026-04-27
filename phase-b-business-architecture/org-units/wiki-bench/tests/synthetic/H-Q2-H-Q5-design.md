# Hypotheses H-Q2 and H-Q5 — TDD verification on synthetic data

After bench-grade L0–L2 measurement on Qwen3.6-27B-FP8 vs Opus-baseline
(commit 369c503), two of the four observed quality gaps point to
**harness deficiencies**, not model deficiencies. We're going to
verify both via TDD on a synthetic minimal example before investing
in fixes.

## H-Q2 — agent has no WebSearch tool

> **IF** the OpenHands agent in our bench sandbox lacks a `web_search`
> (or equivalent) tool, **THEN** even when the skill instructs
> "fact-check empirical claims via web search" the agent cannot do
> it; it will silently produce zero `CONTRADICTS_FACTS` markers and
> zero URL citations. **BECAUSE** instructions without tool capability
> are unactionable; the model produces compliance-shaped output
> (`fact_check_performed: true` in frontmatter) without the underlying
> action.

**Observation that motivates the hypothesis** (bench-grade on
qwen3.6-27b-fp8 vs Opus, 7 sources of module 005):

| metric                      | qwen | opus |
| --------------------------- | ---: | ---: |
| `claims_CONTRADICTS_FACTS`  |    0 |    6 |
| `fact_check_citations`      |    0 |   43 |
| `fact_check_performed=true` |    7 |    7 |

Frontmatter says fact-check happened on every source; output shows
zero citations and zero contradictions caught. False attestation.

## H-Q5 (NEW) — agent doesn't read prior sources

> **IF** the agent doesn't read previously-written source articles
> (under `data/sources/`) when processing the next source, **THEN** it
> cannot tell which claims are `NEW` vs `REPEATED (from: <slug>)`,
> so all claims get marked `NEW` (or unmarked). **BECAUSE** REPEATED
> classification requires comparison with prior source-article texts
> — the `concept-index.json` lists slugs but not claim contents, and
> the agent's working memory does not span sources within one
> OpenHands run.

**Observation that motivates the hypothesis** (same data):

| metric                | qwen | opus |
| --------------------- | ---: | ---: |
| `claims_REPEATED_sum` |    0 |   25 |

Across 7 sources of one module, Qwen never marked anything as
REPEATED. Opus did so 25 times. The skill explicitly defines the
REPEATED classification — the model is following the spec it sees,
just blind to the comparison material.

## TDD design

Build a minimal synthetic test that exercises both hypotheses in
under a minute:

### Synthetic input

Two raw transcripts mounted at `/workspace/raw/data/ТестКурс/999/`:

**Source 001 transcript:**
- claim α: «Принцип Парето: 80% результатов от 20% усилий» → expected NEW
- claim β: «Принцип Парето сформулирован Альфредо Парето в 1950 году»
  → **factually wrong** (correct: 1896, in *Cours d'économie politique*)
  → expected `CONTRADICTS FACTS` with citation
- claim γ: «Закон Мура: транзисторы удваиваются каждые 2 года» → expected NEW

**Source 002 transcript:**
- claim α': «Принцип Парето известен … 80% от 20%» → expected
  `REPEATED (from: <001 slug>)` (same as α)
- claim δ: «Эверест 8849 м, в Гималаях» → expected NEW (factually correct)

### Assertions

| id | hypothesis | check                                                                       |
| -- | ---------- | --------------------------------------------------------------------------- |
| A1 | H-Q2       | `events.jsonl` shows a tool_call with name like `web_search`/`browse`/`fetch_url`, OR a `terminal` command running `curl`/`wget` against an external URL (not localhost / not GitHub auth). |
| A2 | H-Q5       | `events.jsonl` shows a `file_editor` view (or `terminal cat`) on `data/sources/.../001 *.md` BEFORE the agent emits the create for source 002. |
| A3 | H-Q5       | The final `data/sources/.../002 *.md` article contains at least one `[REPEATED` (or ``REPEATED``) marker. |
| A4 | H-Q2       | The final source 001 article contains at least one URL citation in `## Claims`. |
| A5 | H-Q2       | The final source 001 article marks the Парето-1950 claim with `CONTRADICTS FACTS`. |

### TDD red → green

1. **Red** — run the synthetic test against current bench harness.
   Hypothesis: A1, A4, A5 fail (no web tool), A2, A3 fail (no read of
   prior). Capture findings.
2. **Green-Q2** — wire a web tool into OpenHands SDK config (Tavily /
   Serper / built-in browser tool, depending on what the SDK exposes).
   Re-run synthetic. Hypothesis: A1, A4, A5 pass.
3. **Green-Q5** — amend the benchmark skill to explicitly instruct
   "before processing source N, read all prior sources via
   `file_editor view` and pass them as context for REPEATED
   classification." Re-run synthetic. Hypothesis: A2, A3 pass.
4. **Stable** — both green, no regressions on full Kurpatov module 005
   bench (re-measure with `bench_grade.py`, expect non-zero
   `CONTRADICTS_FACTS`, non-zero `REPEATED`, non-zero
   `fact_check_citations`).

This document captures the red-phase plan. A separate result document
will record what the synthetic run actually shows.
