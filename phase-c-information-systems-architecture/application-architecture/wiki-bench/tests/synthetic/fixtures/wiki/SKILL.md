---
name: synth-benchmark
description: |
  Synthetic minimal skill for wiki-bench TDD test of harness
  capabilities (web search, prior-source reading). Run when the operator
  says "run the synthetic benchmark skill".
---

# synth-benchmark — TDD test skill

You operate inside a sandbox with two pre-mounted git working trees:

- `/workspace/raw` — input transcripts (read-only intent: do not commit
  or push; just read)
- `/workspace/wiki` — output workspace, where you write articles +
  index. Local git only — DO NOT push to any remote.

## Mission

Process two test sources from
`/workspace/raw/data/ТестКурс/999 Тестовый модуль/`:

- `001 Парето и Мур/raw.json`
- `002 Парето и Эверест/raw.json`

For each source, produce one source article and update
`concept-index.json`. Process them **in order** (001 then 002).

## Per-source loop

For source N (N = 001, then 002):

### Step 1 — Read the transcript

```
cat "/workspace/raw/data/ТестКурс/999 Тестовый модуль/<src-stem>/raw.json"
```

Use the segments[].text array as the lecture transcript.

### Step 2 — Read all prior source articles

This is **mandatory** for `REPEATED` classification. Before claiming
anything is `NEW`, scan every existing article under
`/workspace/wiki/data/sources/`:

```
ls /workspace/wiki/data/sources/ТестКурс/"999 Тестовый модуль" 2>/dev/null
# Then view each prior source's article via file_editor.view
```

If `REPEATED`, your claim must reference the prior source by slug,
e.g. `REPEATED (from: ТестКурс/999 Тестовый модуль/001 Парето и Мур)`.

### Step 3 — Extract claims and classify

Each substantive claim from the transcript gets one of:

- `NEW` — not stated in any earlier processed source
- `REPEATED (from: <prior-slug>)` — same proposition was in source <prior-slug>
- `CONTRADICTS FACTS` — disagrees with externally-verifiable knowledge

### Step 4 — Fact-check empirical claims (web)

For empirical claims (numbers, dates, attributions), do real web
research:

- Use `web_search` (or any HTTP-fetch tool you have available) to
  find a primary or reference source.
- If external source confirms — no extra marker (still `NEW` /
  `REPEATED`).
- If external source contradicts — mark `CONTRADICTS FACTS` and add
  the citation URL inline on the same bullet.
- If no web tool is available — surface this as a fatal preflight
  error: "no web search tool available; cannot fact-check empirical
  claims".

### Step 5 — Write the source article

Path: `/workspace/wiki/data/sources/ТестКурс/999 Тестовый модуль/<src-stem>.md`

Format (frontmatter + one section):

```markdown
---
slug: ТестКурс/999 Тестовый модуль/<src-stem>
course: ТестКурс
module: 999 Тестовый модуль
extractor: whisper
source_raw: data/ТестКурс/999 Тестовый модуль/<src-stem>/raw.json
fact_check_performed: <true | false>
concepts_touched: [<concept-slug>, ...]
concepts_introduced: [<concept-slug>, ...]
---

## Claims — provenance and fact-check

1. `NEW` — text of claim. Optional inline citation: [Source title](https://example.com/...).
2. `REPEATED (from: ТестКурс/999 Тестовый модуль/001 Парето и Мур)` — text of claim.
3. `CONTRADICTS FACTS` — text of claim. (refuted by [...](https://...)).

(numbered list, every claim from the transcript)
```

### Step 6 — Local commit

Local commit only. **Do not push.**

```
cd /workspace/wiki
git add -A
git -c user.email=synth@test.local -c user.name=synth commit -m "source: <src-stem>"
```

## Constraints

- Operate on `/workspace/raw` (read) and `/workspace/wiki` (read+write+commit, no push).
- For empirical claims you must either fact-check (with citation) or
  declare you couldn't.
- `concepts_touched`/`concepts_introduced` may stay empty in this
  synthetic test — the test does not assert on concept articles, only
  on `Claims`.

## Begin

Start with source 001. Announce each step out loud before doing it.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
