---
name: synth-benchmark
description: |
  Synthetic minimal skill for wiki-bench TDD test of harness
  capabilities (web search, prior-source reading) — v2 with
  helper-script tools as the contract for REPEATED detection and
  fact-checking. Run when the operator says "run the synthetic
  benchmark skill v2".
---

# synth-benchmark v2 — TDD test skill (tool-driven)

You operate inside a sandbox with two pre-mounted git working trees:

- `/workspace/raw` — input transcripts (read-only intent)
- `/workspace/wiki` — output workspace, where you write articles +
  index. Local git only — DO NOT push.

This v2 skill differs from v1 by **mandating helper-script calls** for
two operations that are otherwise unreliable in a long agent session:

1. `python3 /workspace/wiki/skills/synth-benchmark/scripts/get_known_claims.py`
   → returns JSON with every claim from every existing source article,
   including the source slug. This is the **only** legitimate way to
   know what slug to put in `REPEATED (from: <slug>)`.

2. `python3 /workspace/wiki/skills/synth-benchmark/scripts/factcheck.py "<claim>"`
   → returns Wikipedia OpenSearch results (RU+EN) with URLs and
   descriptions. This is the **only** legitimate source of fact-check
   citations.

Both scripts live in `/workspace/wiki/skills/synth-benchmark/scripts/`.

## Mission

Process four test sources from
`/workspace/raw/data/ТестКурс/999 Тестовый модуль/`:

  - `001 Парето и Мур/raw.json`
  - `002 Парето и Эверест/raw.json`
  - `003 Мур и Сатурн/raw.json`
  - `004 Эверест и Пи/raw.json`

Process them **in order** (001 → 002 → 003 → 004). Each source goes
through the same 12-step ritual.

## Per-source ritual (mandatory)

For source N, in this exact order:

### Step 1 — Read the transcript

```
file_editor view /workspace/raw/data/ТестКурс/999 Тестовый модуль/<src-stem>/raw.json
```

### Step 2 — Get the inventory of known claims

```
cd /workspace/wiki && python3 skills/synth-benchmark/scripts/get_known_claims.py
```

(For source 001 the output will be empty — that's fine, no priors.)

Save the output mentally (or to a temp variable) — you'll need the
slugs for `REPEATED (from: ...)` markers in step 5.

### Step 3 — Refresh the spec

Re-read the skill before starting work, to combat context drift:

```
file_editor view /workspace/wiki/skills/synth-benchmark/SKILL.md
```

### Step 4 — Extract every substantive claim from the transcript

A "claim" is one factual or interpretive proposition. Don't merge
multiple ideas into one bullet. Aim for ~1 claim per 60 seconds of
transcript (or ~1 claim per 100 words).

### Step 5 — Classify each claim

For each claim, decide:

  - `NEW` — the claim is **not** present in `get_known_claims.py`'s
    output. Default for unique propositions.
  - `REPEATED (from: <slug>)` — the claim **is** present in some
    earlier source. The `<slug>` MUST come verbatim from
    `get_known_claims.py`'s output (do not invent slugs).
  - `CONTRADICTS FACTS` — set in step 6 only, never here.

### Step 6 — Fact-check every empirical claim

An "empirical claim" is one that mentions: a number, a date, a
person's name and attribution, or a statement about the physical
world that can be checked against an external reference.

For each empirical claim:

```
cd /workspace/wiki && python3 skills/synth-benchmark/scripts/factcheck.py "<claim text>"
```

Inspect the JSON output. From the top results:

  - If the descriptions support the claim → keep its current marker
    (NEW or REPEATED) and append `[<title>](<url>)` from the most
    relevant top result as inline citation.
  - If a description **contradicts** the claim → change the marker to
    `CONTRADICTS FACTS` and append the contradicting URL inline,
    plus a one-sentence note explaining the discrepancy.

URLs you cite **must** come from this script's output. Do not
fabricate URLs from memory. The synthetic test asserts URL provenance.

### Step 7 — Write the source article

Path:
`/workspace/wiki/data/sources/ТестКурс/999 Тестовый модуль/<src-stem>.md`

Required shape:

```markdown
---
slug: ТестКурс/999 Тестовый модуль/<src-stem>
course: ТестКурс
module: 999 Тестовый модуль
extractor: whisper
source_raw: data/ТестКурс/999 Тестовый модуль/<src-stem>/raw.json
fact_check_performed: true
concepts_touched: []
concepts_introduced: []
---

## Claims — provenance and fact-check

1. `NEW` — Текст утверждения. [Title](https://en.wikipedia.org/wiki/...)
2. `REPEATED (from: ТестКурс/999 Тестовый модуль/001 Парето и Мур)` —
   Текст утверждения, который уже встречался в указанном источнике.
3. `CONTRADICTS FACTS` — Текст утверждения. (refuted by
   [Title](https://...): one-sentence note about the actual fact).
```

### Step 8 — Self-verify before commit (deterministic, via terminal)

```
SRC="/workspace/wiki/data/sources/ТестКурс/999 Тестовый модуль/<src-stem>.md"

# 8.a — file exists
[ -f "$SRC" ] || echo "FAIL: file missing"

# 8.b — frontmatter present and parseable (look for the closing ---)
head -30 "$SRC" | grep -q "^---$" && echo "frontmatter OK"

# 8.c — Claims section is present
grep -q "^## Claims" "$SRC" && echo "Claims section OK"

# 8.d — every numbered claim has a marker
awk '/^## Claims/,/^## /' "$SRC" \
  | grep -E '^[0-9]+\.' \
  | grep -vE 'NEW|REPEATED|CONTRADICTS' \
  && echo "FAIL: unmarked claims" \
  || echo "all claims marked"
```

If any check fails — fix the source.md and re-verify before continuing.

### Step 9 — Commit

```
cd /workspace/wiki
git add -A
git -c user.email=synth@test.local -c user.name=synth commit -m "source: <src-stem>"
```

Local commit only. **Do not push.**

### Step 10 — Move to next source

Increment N (001 → 002 → 003 → 004). Restart at step 1.

After source 004 — done. Call the `finish` tool.

## Constraints

- `get_known_claims.py` MUST be called once per source (step 2).
- `factcheck.py` MUST be called once per empirical claim (step 6).
- `REPEATED (from: <slug>)` marker MUST use a slug returned by
  `get_known_claims.py`. Do not improvise slugs.
- URL citations MUST be from `factcheck.py` output. Do not fabricate.
- Do NOT skip the 12-step ritual. Do NOT collapse multiple steps
  into one tool call.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
