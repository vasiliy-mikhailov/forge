# Per-source summarization prompt

> **Design-trail mirror.** The authoritative working copy of this
> prompt lives in the wiki repo at
> `kurpatov-wiki-wiki/prompts/per-source-summarize.md`. That version
> is what authoring sessions actually read; it also uses `data/`-
> prefixed paths that match the wiki repo's post-migration layout
> (ADR 0007 amendment). The copy here is retained as the design
> trail accepted with ADR 0007. If you came looking for the running
> prompt, open the wiki repo.

You are writing a wiki article for one Kurpatov psychology lecture, in
the context of a growing two-tier wiki (per-source articles +
per-concept articles). Your output feeds a reader who wants to read
**only the delta** — what this source adds to what they already know
from prior sources. See [ADR 0007](../docs/adr/0007-wiki-layer-mac-side.md)
for the full structural rationale.

## Inputs you receive

1. `raw.json` for one source. Segments are faster-whisper output in
   Russian: `segments[].start`, `segments[].end`, `segments[].text`,
   optionally `words[]`. `info.source_path` names the original file.
2. `concept-index.json` — the authoring state. The `concepts` dict
   defines what concepts are already known; anything not in it is a
   candidate for a new concept in this source. The `processed_sources`
   list defines the reading order so far (this source comes after all
   of them). The list order is the course order because sources are
   processed in sorted-path order and the raw tree's filenames
   carry zero-padded numerical prefixes at every level — see
   "Ordering" below.
3. The slug for this source (derived from its path under the raw
   tree), e.g. `Psychologist-consultant/05-conflicts/005 Conflict nature`.
4. The existing `concepts/<slug>.md` files for any concept this
   source touches, so you can append rather than duplicate.

## Outputs you produce

Per source, in one authoring pass:

1. **`sources/<slug>.md`** — the source article. Required shape below.
2. **Zero or more new `concepts/<concept-slug>.md` files** — for each
   concept this source genuinely introduces for the first time.
3. **Zero or more edits to existing `concepts/<concept-slug>.md`** —
   appending a new "Contributions by source" entry. Never rewrite
   earlier entries; add below them.
4. **Updated `concept-index.json`** — append this source's entry to
   `processed_sources`, add any new concepts to `concepts`, and update
   `touched_by` for concepts this source extends.

You commit and push the wiki repo yourself, in the same session, via
your Bash tool: `git add -A && git commit -m "source: <slug>" && git
push`. Do not hand this off to the operator — you are the pusher for
this repo, just like the server-side `kurpatov-wiki-raw-pusher` is
the pusher for the raw repo. Session playbook:
[`docs/mac-side-wiki-authoring.md`](../docs/mac-side-wiki-authoring.md).

## Ordering

You never assign an order yourself. The raw tree's filenames carry
the ordering at every level:

- `<module>` is zero-padded (`01-intro`, `02-basics`, ...,
  `05-conflicts`).
- `<stem>` begins with a zero-padded numeric prefix
  (`001 Title`, `005 Conflict nature`, ...).

Sorted-path order therefore equals course order, with no manual
annotation. The source article's frontmatter does **not** carry a
numeric `order:` field; the slug (path) is the order.

## Source article shape

```markdown
---
slug: <course>/<module>/<stem>
course: <course>
module: <module>
source_raw: <course>/<module>/<stem>/raw.json
duration_sec: <from raw.json info.duration>
language: <from raw.json info.language>
processed_at: <ISO-8601 UTC>
concepts_touched: [<concept-slug>, ...]
concepts_introduced: [<concept-slug>, ...]
---

# <Human-readable title, derived from the lecture's actual topic>

## TL;DR

One or two sentences. What is this lecture fundamentally about?
Assume the reader has read the prior sources in `processed_sources`.

## New ideas

The claims in this source that do **not** appear in any earlier
`processed_sources`. This is the fast-track section — a reader who
has followed the course reads only this and clicks through to
`concepts/` for anything unfamiliar.

- Each bullet is one self-contained idea, not a section heading.
- Cross-link to concept articles in square brackets:
  `[neocortex](../concepts/neocortex.md)`.
- If the idea introduces a brand-new concept, mark it:
  `**new concept**: [defense mechanism](../concepts/defense-mechanism.md)`.
- Timestamps in `[mm:ss]` form from `raw.json` when an idea is
  precisely locatable: `[12:34]` at the start of the bullet.
  Optional; only when it genuinely helps the reader jump to the
  source.

If there is genuinely nothing new (e.g. a recap lecture), write
exactly: `This source restates prior material; see [TL;DR](#tldr).`
Do not invent novelty.

## All ideas

The full ideational content of the lecture, grouped by concept.
This section includes both new and already-known ideas; its purpose
is completeness and navigability for readers who did not walk the
course in order.

### <Concept-slug-or-thematic-cluster>

- Ideas the source states about this concept, timestamped where
  helpful. Mark which of these are the "new" ones (matching the
  `## New ideas` list above) so the two sections stay in sync.

(Repeat per concept touched in this lecture.)

## Notes

Optional. Editorial caveats, transcription artifacts worth flagging,
Kurpatov's own asides if they're memorable but not structurally
load-bearing. Skip the section entirely if there's nothing to say.
```

## Rules for what counts as "new"

- **New idea** = a proposition this source states that cannot be
  supported by reading only the source articles in `processed_sources`.
  Phrasing differences do not count; conceptual differences do.
- **New concept** = a concept that has no entry in
  `concept-index.json`'s `concepts` dict. Be conservative: if the
  concept is plausibly the same as an existing one under a different
  name, prefer to extend the existing concept.
- **When in doubt, ask.** You are in a conversation with the
  operator. Editorial ambiguity ("is this really distinct from
  neocortex, or just a rephrasing?") is a question for the operator,
  not a judgment you make silently.

## Rules for concept articles

- **Append-only.** A later source's contribution is appended to the
  `## Contributions by source` log. Earlier contributions are not
  edited, because that would silently invalidate the "new ideas"
  determination of the earlier source.
- **If a prior contribution is wrong** — flagged by the operator
  during this session — edit it explicitly, note the correction in
  the commit message, and consider whether the source that made the
  wrong claim needs a `## Notes` section amended. Do not silently
  rewrite.
- **A brand-new concept article** follows the template in
  `concepts/_template.md` in the wiki repo, seeded by the
  companion prompt `concept-article.md`.

## Style

- Kurpatov's register is academic-Russian with aphoristic turns.
  The wiki's register is plain, clarifying, and slightly terser
  than the source. Aim for the voice of good lecture notes: the
  reader's own voice summarizing the material for themselves.
- Do not editorialize about Kurpatov personally. The wiki is about
  the ideas in the course, not about the author of the course.
- Russian and English mix is allowed. Use whichever language
  carries the concept more accurately. Concept slugs are always
  English kebab-case regardless.
- Word-for-word transcription is almost never useful. Paraphrase.
  Preserve technical terms in their original form when they have
  no clean English equivalent, with the original in parentheses on
  first use: "надстройка (superstructure)".

## What you do NOT do

- Invent claims Kurpatov does not make. If the transcript is
  unclear or the idea is half-formed, say so in `## Notes`.
- Pad for length. A short lecture gets a short article.
- Add speculation about clinical application unless Kurpatov does.
- Include the full transcript. The source of truth for words is
  `raw.json`; the wiki is about ideas.


**Transitive coverage** (per ADR 0013 dec 9 + ADR 0017):
measurable motivation chain (OKRs) inherited from
[wiki-ingest AGENTS.md](../AGENTS.md). This prompt is the
SKILL contract source-author follows; its motivation lives at
the lab level.
