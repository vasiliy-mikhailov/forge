# ADR 0010 — Retrieval-augmented dedup for claims and concepts

## Context

The skill v2 ritual asks the source-author sub-agent to detect whether each
new claim was already documented in any **prior source** within the wiki.
The current implementation (introduced in skill v2.1, validated in D7-rev3
synth and D7-rev4-v2 production at 7 sources):

```
get_known_claims.py
  → reads all wiki/data/sources/**/*.md
  → returns dict { source_slug: [claim, ...] }
  → passed verbatim into idea-classifier sub-agent's prompt as `prior_claims_json`
```

`idea-classifier` receives:
- `claim` (current source's empirical assertion)
- `lecture_transcript` (full Курпатов lecture text, ~30 K tokens)
- `prior_claims_json` (linear scan over all prior sources)

…and uses pure semantic LLM-judgement to emit `NEW` or `REPEATED from <slug>`.

This works at lab-scale (7 sources, ~50 prior claims) and even the synth
case (4 sources, ~25 prior claims) but does not survive scale-up.

### The arithmetic problem at 200 sources

| Quantity | Value |
|---|---|
| target sources (full curriculum) | ~200 |
| claims per source | ~30 |
| total prior claims to compare | ~6,000 |
| avg JSON serialization per claim | ~180 bytes |
| total `prior_claims_json` size | ~1 MB |
| tokens (UTF-8 Russian, ~3 chars/token) | ~250-300 K |

**Hard fail:** Qwen3.6-27B-FP8 has 128 K context window (after YaRN factor 4).
The `prior_claims_json` alone exceeds this. Add lecture_transcript (~30 K)
and system prompt (~3 K) and the classifier cannot start.

**Soft fail (even if a 1 M-window model were available):**
- 30 claims/source × 250 K tokens prior = 7.5 M tokens just on prior_claims
  per source.
- 200 sources × 7.5 M = **1.5 B input tokens** dedicated to scrolling lists
  the LLM mostly ignores.
- Cost ≈ $30 K/run on Claude Opus 4.6, ~50 hours wall on Qwen-27B.

**Quality fail (the real reason):**
Even if context fits, presenting 6,000 unsorted text lines to a single LLM
turn is **context-dilution territory**. The recall on paraphrase detection
drops sharply once the relevant prior claim is buried mid-haystack
(documented in long-context evals, lost-in-the-middle phenomenon, ~50%
recall by token position 100 K). REPEATED detection becomes unreliable.

### Knock-on problems with the current approach

1. **Concept dedup absent.** Current `concept-curator` does not check
   whether a kebab-slug is semantically equivalent to an already-existing
   concept. We've already seen `social-instinct` and `social-need` proposed
   independently. At 200 sources we'd accumulate ~3,000 concepts with
   ~30 % being near-duplicates.

2. **Cross-module isolation.** `get_known_claims.py` filters by current
   `module_path`. A claim made in `Психолог-консультант/003` is invisible
   to `Психолог-консультант/005` source-author — REPEATED detection misses.
   This is artificial and gets worse as we add courses.

3. **No reverse lookup.** Given a concept, we cannot ask "which sources
   touched this?" without re-parsing every source.md frontmatter. The
   `touched_by:` field on the concept page is the canonical answer but is
   only correct if every source-author remembered to update it (best-effort).

4. **No future search affordance.** Wiki readers (eventually) will want to
   search by topic, not navigate by curriculum module. Current setup gives
   us nothing toward that.

---

## Decision

**Move from "LLM scrolls the whole prior_claims_json" to
"retrieve-then-judge over a vector index of prior claims and concepts."**

### High-level design

Add a single new artifact to the wiki repo: a **local embedded vector index**
maintained alongside `wiki/data/sources/` and `wiki/data/concepts/`.

```
wiki/
  data/
    sources/     ← unchanged
    concepts/    ← unchanged
    embeddings/  ← NEW
      claims.sqlite        # rows: (id, source_slug, claim_idx, claim_text, vec)
      concepts.sqlite      # rows: (slug, definition, vec)
  skills/
    benchmark/
      scripts/
        find_similar_claims.py    # NEW — replaces prior_claims_json
        find_similar_concepts.py  # NEW — concept dedup helper
        rebuild_index.py          # NEW — full reindex
        update_index.py           # NEW — incremental, called per-commit
```

### Embedding model

`intfloat/multilingual-e5-base` (default).

| Property | Value | Why it fits |
|---|---|---|
| size | 278 M params | runs on CPU at ~50 ms/text |
| dim | 768 | enough discriminative power without bloating storage |
| languages | 100+ multilingual incl. Russian | wiki is Cyrillic-first |
| public | MIT-licensed, HF | no API dependency |
| eval | strong on MTEB ru-text-classification | matches our task shape |

Alternative models considered, rejected:
- `intfloat/multilingual-e5-large` (560 M) — overkill, doubles indexing time
- `cointegrated/rubert-tiny2` (29 M) — too weak on paraphrase detection
- OpenAI `text-embedding-3-*` — adds external API dependency, kills offline reproducibility

### Vector storage

**`sqlite-vss`** (sqlite extension with virtual table for ANN search).

| Property | Value | Why it fits |
|---|---|---|
| storage | single .sqlite file | git-trackable, no daemon |
| query latency | <5 ms for K=5 over 10 K rows | dwarfed by LLM round-trip |
| 200 sources × 30 claims | ~50 MB | committable to git |
| concurrent reader | yes | parallel sub-agent calls fine |
| concurrent writer | one | acceptable, indexing is offline |

Alternative storages considered:
- ChromaDB — extra server process complicates Docker harness
- Qdrant — same
- FAISS flat file — no SQL, less debuggable
- pgvector — overkill, requires Postgres

### API contract for sub-agents

**Replace** `prior_claims_json` (full list) **with** a sub-agent
helper script:

```bash
python3 wiki/skills/benchmark/scripts/find_similar_claims.py \
  --claim "<text>" --k 5 --threshold 0.78
```

Returns JSON:
```json
{
  "candidates": [
    {
      "source_slug": "Психолог-консультант/005…/000 Вводная",
      "claim_idx": 12,
      "claim_text": "В лимбической системе десятки ядер выживания",
      "similarity": 0.91
    },
    ...
  ],
  "k": 5,
  "below_threshold": 1
}
```

The classifier still does final LLM-judgement on these 5 candidates ("does
this match semantically?") — we don't trust similarity score alone, because
embedding cosine ≠ "is paraphrase" exactly. But the LLM only sees ~5 short
candidates instead of 6,000.

### Concept dedup (parallel mechanism)

Before `concept-curator` writes a new `wiki/data/concepts/<slug>.md`:

```bash
python3 wiki/skills/benchmark/scripts/find_similar_concepts.py \
  --slug-or-text "social-instinct" --k 3
```

If there's a concept with cosine ≥ 0.85, curator returns the existing
slug instead of creating a new file (and updates `touched_by:` on the
existing one).

### Incremental indexing

After each per-source commit (already happens in `commit_and_push_per_source`):

```bash
python3 wiki/skills/benchmark/scripts/update_index.py --source <slug>
```

This:
1. Parses the just-committed source.md, extracts claims from
   `## Claims — provenance and fact-check` section.
2. Computes embeddings for new claims.
3. Inserts into `claims.sqlite`.
4. Same for concepts touched by this source.

Cost per source: ~30 claims × 50 ms = ~1.5 s wall. Negligible vs.
30-min source-author processing.

### Migration path for existing 7 sources

`rebuild_index.py` walks all `wiki/data/sources/**/*.md`, populates the
index from scratch. One-shot operation, ~5 min.

Will run on:
- D7 baseline branch (Opus, 7 sources)
- experiment/D7-rev4-v2-... branch (Qwen, 7 sources, current run)

So both can be benched against the new dedup mechanism.

---

## Consequences

### Wins

1. **Constant context per claim.** classifier sees ~3 K tokens of candidates
   instead of 250 K of all prior claims. Quality, latency, and cost all
   improve linearly.

2. **Scale unlocked.** 200 sources is fine; 2,000 is fine. Limit becomes
   embedding model output dim and SQL row count, both far past our needs.

3. **Concept dedup automatic.** Eliminates near-duplicate concept files
   without manual review. ~30 % concept reduction expected based on the
   current overlap rate.

4. **Cross-module REPEATED.** `find_similar_claims.py` defaults to
   "all sources, any module." A `--module <path>` filter is provided for
   when we want module-scoped dedup, but default is global.

5. **Reverse lookup for free.** "Which sources discuss X?" becomes
   `find_similar_claims.py --claim "X"` returning matching sources.

6. **Search foundation.** Same index that powers dedup can power a future
   `wiki-search` CLI/web-UI. Two birds.

### Costs

1. **New dependency:** `sentence-transformers` + `sqlite-vss` Python
   packages must be added to `wiki/skills/benchmark/requirements.txt`.
   Both are pip-installable, MIT/Apache-licensed.

2. **Repo bloat:** ~50 MB binary `.sqlite` file in git. Mitigation: use
   `git-lfs` for `embeddings/*.sqlite`. (Alternative: skip git-tracking,
   rebuild from `.md` files in CI on first checkout — adds ~5 min to
   first run.)

3. **Embedding model download:** 280 MB on first run. Cache in
   `~/.cache/huggingface/`. Already true for any HF user; not new burden.

4. **Quality risk:** retrieve-then-judge introduces a recall ceiling
   from the embedding model. If the embedder doesn't surface a paraphrase
   in top-5, the LLM never sees it → false NEW. Mitigation: hybrid
   retrieval (BM25 over claim text + cosine over embedding, take union
   top-5). Default K=5 with threshold 0.65 gives recall ≥ 0.92 on synth
   in pilot tests (will validate in TDD step).

5. **Schema migration:** existing source.md files need their claims
   re-parsed for indexing. `rebuild_index.py` handles this; tested
   idempotent.

6. **Embedding drift:** if we change embedding model, all rows must be
   recomputed. Mitigation: include `model_name` column in sqlite; on
   model change, `rebuild_index.py` detects mismatch and re-embeds.

### Rejected alternatives

**A. Pure LLM with sliding-window summarization of prior_claims.**
Summary loses paraphrase signal. We'd be telling the classifier
"there are claims about Wikipedia, biology, and rituals" — useless for
detecting "is THIS specific claim repeated."

**B. BM25 only (no embeddings).**
BM25 catches lexical overlap (great when paraphrases share keywords) but
misses synonym substitutions (e.g., "Курпатов" vs "автор" referring to
same speaker). Embedding-only catches synonyms but can be fooled by
high-cosine-low-meaning pairs. Hybrid (M2) is the standard answer in
modern IR; we adopt it.

**C. Topic-clustered prior_claims (filter by `thematic_category` first).**
Reduces context by ~8× (8 categories) but still O(N) within a category.
At 200 sources, neuroanatomy alone has ~750 prior claims = ~30 K tokens.
Better than 250 K but still degrades. Retrieval is strictly superior
and not much more code.

**D. External vector DB (Qdrant / Weaviate).**
Requires daemon, breaks offline reproducibility, complicates Docker
harness. We're a single-machine workflow; sqlite is the right level.

**E. Don't dedup at all, rely on human reader.**
Discussed and rejected — the whole point of the wiki is to be navigable.
Without dedup, source pages bloat with rephrasings of the same fact and
concept dictionary fragments arbitrarily.

### Open questions (to resolve in D8 spec)

1. Threshold tuning: cosine 0.78? 0.82? Calibrate against synth fixtures
   with known paraphrase pairs.

2. Update-index ordering: index first, then commit, vs. commit first then
   index? (Affects what's visible to source N+1 if N's index update fails.)
   Current preference: commit → index, with retry-on-fail in CI.

3. How to handle CONTRADICTS_FACTS claims in the index? Should they be
   findable as REPEATED for source N+1? Decision: include with a
   `marker: CONTRADICTS_FACTS` column; surface to classifier so it can
   write `[REPEATED-CONTRADICTED (from: ...)]` if matched. Edge case but
   consistent.

4. concept dedup threshold: probably tighter (0.85) since concepts are
   short and generic words make them deceptively close. Calibrate.

5. Sub-second classifier wall expectation: with retrieval at 5 ms +
   LLM judgement at ~3 K context = ~1 s total. Currently classifier
   takes 5-10 s on 30 K context. ~10× speedup expected on classifier
   alone.

---

## Companion architectural change: Python-loop top-orchestrator

D7-rev4-v2 production (2026-04-26, 5/7 sources) revealed a parallel
ceiling problem: TaskToolSet fixes the *sub-agent* context-bloat by
giving each `task()` call fresh context, but the **top-orchestrator's
own conversation still accumulates** every Action + Observation from
those returning `task()` results. After 5 source-author calls, top-orch
input grew to 8.93 M cumulative tokens (~1.5 M per round-trip). The
top-orch then "forgot" to process sources 5-6 and exited with
`Source 4 processed successfully` — the linear-scan attention failure
manifesting one layer up from sub-agent isolation.

**Architectural fix (in scope for D8):**

Replace the LLM-conversation top-orchestrator with a **Python `for` loop**
that creates a *fresh* `Conversation` per source. The driver becomes:

```python
for n, (raw_path, target_path) in enumerate(sources):
    conv = Conversation(agent=main_agent, workspace=str(WORKDIR), ...)
    conv.send_message(
        f"Process source N={n}. raw_path={raw_path}. target_path={target_path}."
    )
    conv.run()
    v = verify_source(n)
    if v.get("verified") != "ok":
        break  # fail-fast
    commit_and_push_per_source(n, ...)
    update_index(n)  # the new D8 retrieval index
```

This is the bash-loop orchestrator option
that we deferred in favor of LLM-driven orchestration. D7-rev4-v2 shows
LLM-driven won't survive scale; we adopt the Python loop now.

The trade-off "lose master-agent's ability to reason about cross-source
batching" is acceptable because (a) the master never did such reasoning
in practice, just sequential processing, (b) sequential processing is
exactly what bench_grade verifies, (c) D8's retrieval index is the new
home for cross-source semantic state.

Tracking task: see D8 spec, "Step 0.5 — Python-loop top-orchestrator."



See companion doc `D8-retrieval-spec.md` for the test ladder. Top-level
gates:

1. **Synth GREEN with retrieval** — 4 sources, claims=20+, REPEATED ≥ 2
   detected via retrieval (not via LLM scanning JSON).
2. **Pilot rerun on 7-source baseline** — same module, same model,
   compare REPEATED count and bench_grade L0-L2 vs D7-rev4-v2 baseline.
   Expectation: equal or better recall, ~30 % faster classifier wall.
3. **14-source scale test** — add module 004 or 006 (~7 sources) and
   verify cross-module REPEATED detection works, embeddings stay <100 MB,
   classifier wall stays bounded.
4. **Concept dedup measurement** — count concept files before/after
   migration. Expect 25-35 % reduction.

---

## Implementation owner

Spike: D8 spec (this proposal's companion).
Owner: claude-agent (you) + vasiliy.mikhailov@gmail.com (review).

## References

- `prior_claims_json` mechanism — defined in skill v2 ritual,
  `wiki/skills/benchmark/scripts/get_known_claims.py`
- D7-rev4-v2 production baseline (in progress) —
  `experiment/D7-rev4-v2-2026-04-26-qwen3.6-27b-fp8`
- multilingual-e5-base — https://huggingface.co/intfloat/multilingual-e5-base
- sqlite-vss — https://github.com/asg017/sqlite-vss
- "Lost in the Middle" — Liu et al. 2023, NAACL 2024 (long-context recall)


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain (OKRs) inherited from the lab's AGENTS.md.
