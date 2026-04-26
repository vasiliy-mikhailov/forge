# D7-rev4 — closing the depth gap to Opus via enriched per-sub-agent context

Active spec. Predecessors: [`D7.md`](D7.md), [`D7-rev2.md`](D7-rev2.md), [`D7-rev3.md`](D7-rev3.md). Architectural decision: [`../adr/0009-per-source-agent-isolation.md`](../adr/0009-per-source-agent-isolation.md). How-to skills: [`../../.agents/skills/openhands-sdk-orchestration.md`](../../.agents/skills/openhands-sdk-orchestration.md), [`../../.agents/skills/tdd-on-synthetic-fixtures.md`](../../.agents/skills/tdd-on-synthetic-fixtures.md).

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we keep D7-rev3's 3-level orchestration (top → source-author → per-claim
> classifier + fact-checker + concept-curator) but pass the **full lecture
> transcript** as input context to each sub-agent invocation (instead of just
> the claim text), and ask sub-agents to return **paragraph-level structured
> output** (classifier returns `verdict + thematic_category`; fact-checker
> returns `marker + url + Notes` where Notes combines speaker caveats from
> transcript + Wikipedia/scientific status + optional journal reference),
> AND we fact-check ONLY those claims where the source-author has doubts
> (specific dates, attributions, numbers, controversial claims) — confident
> claims (general anatomy, speaker's own concept definitions, well-known
> psychology paradigms) skip the fact-checker delegation entirely and get
> `[NEW]` without a URL,
> **THEN** the source.md output will close the depth gap to Opus baseline —
> body sections 3-6× longer with thematic grouping in `## New ideas`,
> Notes-style commentary under each claim, and inline concept-links throughout
> prose,
> **BECAUSE** D7-rev3 source 0 comparison vs Opus showed that per-claim
> sub-agents currently see only ~150-300 chars of input (claim text alone)
> while the 27B model has 128K context window — 99.7% of the budget is unused.
> The depth Opus produces comes from seeing the full lecture in the same
> context as the claim being reasoned about. We can give sub-agents the same
> lecture-level context without changing the architecture.

## Architecture: as-is vs. to-be

### As-is (D7-rev3, partial — 4/7 sources written, ~80% structural compliance vs Opus)

```
top orchestrator → source-author (full transcript via terminal cat raw/N.json)
                                ↓
                    ┌───────────┼───────────┐
                    ↓           ↓           ↓
              classifier   fact-checker  concept-curator
              ────────     ───────────   ───────────────
              input:       input:        input:
                claim_text   claim_text    concept_slug
                (~200ch)     (~200ch)      definition (~500ch)
                prior_json
                (~3-5K)
              output:      output:       output:
                NEW or       URL: <u>      "concept ready"
                REPEATED     or NO_MATCH
                (~30 chars)  (~80 chars)
```

D7-rev3 source 0 (12 claims, atomic):

```
1. Внутренний конфликт — основа невротических состояний… [NEW] — https://…
2. Базовые биологические потребности трансформируются через структуры мозга… [NEW] — https://…
…
```

Each claim ~150-200 chars + URL. No Notes per claim. No thematic grouping in `## New ideas`. No inline concept-links in body bullets.

Opus source 0 same lecture (25 claims, ~319 chars/claim, 4 Notes, thematic groups, inline concept-links): ~3.2× richer body, ~6× richer `## New ideas`.

### To-be (D7-rev4, depth-enriched per-sub-agent input)

```
top orchestrator → source-author (full transcript)
                                ↓
                    ┌───────────┼───────────┐
                    ↓           ↓           ↓
              classifier   fact-checker  concept-curator
              ─────────    ───────────   ───────────────
              input:       input:        input:
                claim_text   claim_text    concept_slug
                full_lecture full_lecture  definition
                (~10-15K)    (~10-15K)     full_lecture
                prior_json   factcheck.py  (~10-15K)
                (~3-5K)      output (~2K)  related_claims
              output:      output:       output:
                verdict +    marker +      proper concept .md
                thematic     url +         (with touched_by +
                category     paragraph     ## Definition section)
                (~60 chars)  Notes
                             (~400-800 chars)
```

Key changes:
- **Each sub-agent receives full lecture transcript** (~10-15K tokens) in delegate task prompt — well within the 27B's 128K window.
- **source-author when extracting claims also assigns `needs_factcheck: true|false`** — only doubtful claims (specific dates, attributions, numbers, controversial assertions) trigger fact-checker delegation. Confident claims (general anatomy, speaker's own concept definitions, well-known psychology paradigms) skip fact-checker entirely; classifier still runs (for `thematic_category` and REPEATED detection).
- **classifier** also derives `thematic_category` from where the claim sits in lecture flow.
- **fact-checker** (called only on `needs_factcheck=true` claims) writes a 2-3 sentence Notes combining: (a) speaker's own qualifications quoted from the transcript, (b) Wikipedia/scientific status, (c) optional journal reference if the Wikipedia article body cites one.
- **concept-curator** writes the canonical concept template (with `touched_by` field listing related concepts and a `## Definition` section), grounded in the actual lecture content rather than its own training data.
- **source-author at assembly:**
  - Buckets `## New ideas` bullets by `thematic_category` from classifier outputs.
  - For fact-checked claims: adds Notes under each numbered claim in `## Claims` block.
  - For confident claims: marks `[NEW]` with no URL — no fake Wikipedia link from training data.
  - Inserts inline `[concept-slug](../../../concepts/<slug>.md)` links throughout `## Лекция` paragraphs and `## New ideas` bullets.

### `needs_factcheck` heuristic — when to fact-check

source-author at extraction tags each claim with one of two confidence levels:

**`needs_factcheck: false`** (skip fact-checker; mark `[NEW]` without URL):
- Speaker's own conceptual definitions ("Курпатов вводит понятие 'химер' для…")
- Well-established general anatomy / neuroanatomy ("лимбическая система — часть подкорки")
- Well-known psychology paradigms taught at undergraduate level
- Methodological framings ("четыре ракурса психики")
- Claims about the speaker's own framing / synthesis

**`needs_factcheck: true`** (delegate to fact-checker; URL inline):
- Specific dates ("в 1950 году", "в 1976 году опубликовал")
- Specific attributions ("Дарвин сказал…", "впервые описал Адлер…")
- Specific numbers / statistics ("80% от 20%", "150 человек по Данбару")
- Names of laws / theories tied to person ("закон Мура", "число Данбара")
- Claims that cross into other disciplines (economy, history, biology)
- Any claim where the speaker himself caveats it ("на самом деле это не так точно")

The heuristic is intentionally model-driven, not exhaustive — source-author uses judgement on ambiguous cases. **Default = `needs_factcheck: true`** when in doubt; over-checking is recoverable, under-checking risks hallucinated URLs in source.md.

Empirical projection: ~30-50% of claims need fact-check on a Курпатов lecture (most claims are speaker's framing or general anatomy). 7 sources × ~25 claims × 40% = ~70 fact-check calls for full module 005, vs current ~150+ — **about half the Wikipedia API load** which keeps us under HTTP 429 threshold.

Why no `synthesizer` (4-th sub-agent) added: with per-sub-agent enriched context, the cross-claim synthesis happens implicitly — classifier sees the lecture's narrative structure and returns a category that maps to it; fact-checker sees claims in flow and writes Notes that reference adjacent claims when relevant. An explicit synthesizer pass would help further but is deferred to D7-rev5 if the gap to Opus remains after rev4.

## Falsifiability criteria (locked before run)

D7-rev4 is **falsified** if any one of the following holds on the new branch's bench-grade after the experiment:

- Aggregate `claims_total_sum < 100` on 7 sources — sub-agent enrichment did not raise per-source claim count vs D7-rev3's average ~13/source. Opus had ~18/source.
- Aggregate `notes_flagged_sum < 6` — fact-checker's paragraph Notes did not surface as parseable Notes in source.md (parser looks for `Notes.` / `*Notes*` / `⚠`). Opus had 18.
- Any source with body section size < 0.7× Opus's same source — depth gap unchanged or widened.
- `concepts_count < 30` on aggregate — sub-agent enrichment did not raise concept extraction breadth (D7-rev3 had 21 on 4 sources; we want ≥30 on 7 — slightly under Opus's 59 is fine, that's an acceptable shortfall, but ≥30 is needed to demonstrate progress).

D7-rev4 is **partially confirmed** if 3 of 4 above pass. Note any specific shortfall in post-mortem.

D7-rev4 is **fully confirmed** if all 4 pass AND the qualitative comparison
(side-by-side text reading of source 0 vs Opus) shows the enriched output is
recognisably closer to Opus's editorial style — Notes, thematic groups,
inline concept-links present.

## Expected metrics (predictions, locked before run)

Comparison plane:

| metric                            | base  | D7 #1 | D7-rev2 |  opus |  D7-rev3 (4/7 partial)  |  D7-rev4 expected |
| --------------------------------- | ----: | ----: | ------: | ----: | ----------------------: | ----------------: |
| `sources_count` (excl. _template) |     7 |     7 |       5 |     7 |                       4 | 7                 |
| `claims_total_sum`                |    38 |     0 |      80 |   130 |                      52 | ≥ 100             |
| `claims_NEW_sum`                  |    22 |     0 |      69 |    99 |                      47 | ≥ 70              |
| `claims_REPEATED_sum`             |     0 |     0 |      11 |    25 |                       3 | ≥ 8               |
| `claims_CONTRADICTS_FACTS_sum`    |     0 |     0 |       0 |     6 |                       2 | ≥ 4               |
| `claims_unmarked_sum`             |    16 |     0 |       0 |     0 |                       0 | 0                 |
| `notes_flagged_sum`               |     4 |     0 |       1 |    18 |                       0 | ≥ 6               |
| `fact_check_citations_sum`        |     0 |     0 |      87 |    43 |                      52 | ≥ 60              |
| `fact_check_performed_count`      |     7 |     1 |       5 |     7 |                       4 | 7                 |
| `concepts_count`                  |    16 |    27 |      20 |    59 |                      21 | ≥ 30              |
| spec compliance violations        |   ≥ 5 |   145 |       6 |     5 |                      63 | ≤ 15              |

Two D7-rev3 numbers worth highlighting are already strong: `fact_check_citations_sum=52 vs Opus 43` (already over) and `claims_unmarked_sum=0` (perfect compliance). Those carry over. The deltas to close are claim count, Notes, concepts, REPEATED detection, and concept-curator template compliance.

## Methodology

### Branch naming

`experiment/D7-rev4-<YYYY-MM-DD>-<served-name>`. Stale branch from any prior killed attempt purged before run.

### Sub-agent prompt changes (concrete diffs from D7-rev3)

**idea-classifier**:
```
You are idea-classifier. Each task message contains:
  - claim: the empirical claim text
  - lecture_transcript: full lecture transcript (read-only context)
  - prior_claims_json: output of get_known_claims.py

Step 1: Decide NEW vs REPEATED based on prior_claims_json.
Step 2: Look at where this claim sits in lecture_transcript — what cluster
of ideas does it belong to? Pick a thematic_category from this list (or
propose a new one in kebab-case if none fits):
  - architecture-of-the-method
  - neuroanatomy
  - psychology-and-instinct
  - culture-and-society
  - dynamics-and-conflict
  - philosophy-and-method
  - history-and-attribution

Output ONE LINE: <verdict> | category=<thematic-category-slug>
Examples:
  NEW | category=neuroanatomy
  REPEATED from <prior-slug> | category=psychology-and-instinct
```

**fact-checker**:
```
You are fact-checker. Each task message contains:
  - claim: the empirical claim text
  - lecture_transcript: full lecture transcript

Step 1: Run via terminal:
  cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"

Step 2: Inspect Wikipedia OpenSearch result. Pick the BEST topic match.
Then read the result's `description` field for context.

Step 3: Scan `lecture_transcript` for any caveats the speaker (Курпатов)
makes ABOUT THIS SPECIFIC CLAIM. Quote the speaker's own qualifications
verbatim where available.

Step 4: Compose the verdict + Notes.

Output structured text:
  marker: <NEW|CONTRADICTS_FACTS|NO_MATCH>
  url: <best-Wikipedia-URL or none>
  notes: <2-3 sentences combining (a) speaker's own qualifications quoted
          from transcript with «…», (b) Wikipedia/scientific status,
          (c) optional journal reference if the Wikipedia article cites one>

If the speaker's claim contradicts well-known facts AND the speaker did
NOT himself caveat it, set marker=CONTRADICTS_FACTS and explain in Notes.

If the speaker did caveat it (e.g. «модель Маклина не точна, использую её
как каркас»), keep marker=NEW but include the caveat in Notes.
```

**concept-curator** (also touch-up to match canonical concept template):
```
You are concept-curator. Task message contains:
  - concept_slug
  - definition (paragraph in Russian, derived from lecture)
  - source_slug (the source that introduced this concept)
  - lecture_transcript (read-only — for grounding the definition)
  - related_concepts_in_source (list of slugs touched by same source)

Workflow:
1. Check if `wiki/data/concepts/<concept_slug>.md` exists.
2. If NEW:
   a. file_editor create wiki/data/concepts/<concept_slug>.md with:
      ```
      ---
      slug: <concept_slug>
      introduced_in: <source_slug>
      touched_by:
        - <source_slug>
      related:
        - <related-slug-1>
        - <related-slug-2>
      ---
      # <Title in Russian>

      ## Definition

      <2-3 paragraph definition grounded in the lecture content; quote the
      speaker's own framing where relevant>

      ## See also

      - <related-concept-1> — <one line of why related>
      - <related-concept-2>
      ```
   b. Read wiki/data/concept-index.json, append concept_slug to concepts list, write back.
3. If EXISTS, leave it alone for now. (Updating touched_by across sources
   is a future feature; for D7-rev4 each concept only appears once.)

Output: `concept <slug> ready` and finish.
```

**source-author** assembly changes:
- Pass `lecture_transcript` (the full text from Step A) into each delegate call.
- Per-claim delegate task body:
  ```
  classifier:  "claim: <text>\n\nlecture_transcript:\n<full text>\n\nprior_claims_json: ..."
  factchecker: "claim: <text>\n\nlecture_transcript:\n<full text>"
  ```
- After collecting all (claim, marker, url, notes, theme) tuples, when assembling `## Claims` block, write each as:
  ```
  <n>. <claim text> [<marker>]
  <notes paragraph>
  — <url>
  ```
- For `## New ideas`, group bullets by `thematic_category`. Each bullet has inline `[<concept-slug>](../../../concepts/<slug>.md)` for every concept_introduced or concept_touched referenced in that claim.
- For `## Лекция` paragraphs, weave inline concept-links naturally where concepts are first mentioned.

### Slug bug + concepts_touched/introduced cleanup

source-author prompt addition:
```
Frontmatter:
- slug must NOT include "data/sources/" prefix or "wiki/" prefix.
  Derive: take target_path, strip "wiki/data/sources/" prefix, strip ".md".
  Example: target_path="wiki/data/sources/A/B/C.md" → slug="A/B/C"
- concepts_introduced is a STRICT subset of concepts_touched.
  introduced = first-mentioned-in-this-source-of-module-005.
  touched = all concepts referenced (including those introduced earlier).
```

### Wikipedia rate-limit mitigation (infra)

Three changes to `wiki/skills/benchmark/scripts/factcheck.py`:
1. **User-Agent with email contact**: change UA from `kurpatov-wiki-bench-factcheck/1.0` to `kurpatov-wiki-bench-factcheck/1.0 (https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki; contact:vasiliy.mikhailov@gmail.com)`. Wikipedia documents that identified clients get higher quota.
2. **Local in-memory cache** (single run): if same query asked twice in a session, return cached result. Cuts duplicate calls.
3. **Per-source pause**: source-author after each source's processing waits 30-60s before next delegate batch. Spreads load.

Plus: top orchestrator's master prompt adds `time.sleep(60)` between source delegations (in the Python wrapper, not in the conversation).

### Pre-run checklist

1. GPU 0 + vLLM healthy with `qwen3.6-27b-fp8`.
2. `kurpatov-wiki-wiki:skill-v2` HEAD ≥ commit with the factcheck.py UA fix and concept-template helper.
3. `forge:main` HEAD has `orchestrator/run-d7-rev4.py` with new sub-agent prompts.
4. Stale `experiment/D7-rev4-...` branch purged on github.
5. Synthetic `tests/synthetic-orchestrator/step5d_rev_orchestrator.py` passes 4/4 with new prompts before going to production.

### Run plan

1. Implement step5d_rev (TDD on synth, target deeper output).
2. Smoke synth: 4/4 verified=ok with claim count higher than original step5d (target ~20+ claims aggregate, Notes parseable).
3. Implement orchestrator/run-d7-rev4.py (production).
4. Pre-flight verify Wikipedia rate-limit cleared.
5. Production run: 7 sources of module 005.
6. Re-grade vs Opus baseline.

## Execution log

| run_id  | date       | tier | params                                              | status    | artifact                                                    |
| ------- | ---------- | ---- | --------------------------------------------------- | --------- | ----------------------------------------------------------- |
| (pending) | 2026-04-26 | T4 | qwen3.6-27b-fp8 + skill v2 + 3-level + enriched-input | _pending_ | branch `experiment/D7-rev4-2026-04-26-qwen3.6-27b-fp8` |

## Results (filled after run)

_Pending — will record bench-grade table + side-by-side text comparison vs
Opus on source 0._

## Post-Mortem & Insights

_Pending._
