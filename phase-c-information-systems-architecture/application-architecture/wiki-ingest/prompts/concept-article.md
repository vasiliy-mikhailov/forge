# Concept article prompt (first-introduction only)

> **Design-trail mirror.** The authoritative working copy of this
> prompt lives at `kurpatov-wiki-wiki/prompts/concept-article.md`.
> Authoring sessions read that one; it uses `data/`-prefixed paths
> matching ADR 0007's amended wiki layout. The copy here documents
> the prompt shape as accepted with ADR 0007.

Used when a source introduces a concept that is not yet in the wiki —
no existing `data/concepts/<slug>.md`, no entry in
`data/concept-index.json`'s `concepts` dict. This prompt produces the
seed article. Every later source that touches the concept **appends**
to the existing article; it does not re-run this prompt.

See [ADR 0007](../docs/adr/0007-wiki-layer-mac-side.md) and
[per-source-summarize.md](per-source-summarize.md) for surrounding
context.

## Inputs you receive

1. The concept slug (English kebab-case, e.g. `defense-mechanism`).
2. The source slug that introduces it, e.g.
   `Psychologist-consultant/05-conflicts/003-defenses`.
3. The relevant excerpts from that source's `raw.json` (not the whole
   transcript — the segments where the concept is actually
   discussed).
4. The already-drafted "New ideas" section of the source article, so
   the concept article can align with it.

## Output

One file: `concepts/<concept-slug>.md`.

## Article shape

```markdown
---
slug: <concept-slug>
first_introduced_in: <course>/<module>/<stem>
touched_by:
  - <course>/<module>/<stem>
---

# <Human-readable concept name>

## Definition

One or two paragraphs. What is this concept, in plain terms, as
Kurpatov uses it? This is the top-of-article piece a reader hits
first, so it must stand on its own without requiring a click to
any source article.

If Kurpatov's definition differs from mainstream usage (textbook
psychology, neuroscience, etc.), note the divergence here in a
short paragraph labeled **How Kurpatov uses this**. Do not try to
reconcile or adjudicate — describe the difference.

## Contributions by source

Ordered log. Each entry names one source and summarizes what that
source adds to this concept. The **first entry is this one** —
produced by this prompt. All later entries are produced by
per-source-summarize.md and appended.

### <course>/<module>/<stem>

- What this source says about the concept, in bullets.
- Cross-links back to the source article:
  `See [<short title>](../sources/<course>/<module>/<stem>.md).`
- Timestamps `[mm:ss]` from that source's raw.json when they help a
  reader locate the source statement.

## Related concepts

Optional. Short bulleted list of concept slugs this one leans on or
is commonly confused with. One sentence each.

- [other-concept](other-concept.md) — one-sentence relationship.
```

## Rules

- **Stand-alone definition.** A reader who arrives at
  `concepts/neocortex.md` from Google must be able to read the
  `## Definition` section and leave with a correct mental model,
  without clicking anything.
- **Lean on Kurpatov's framing.** This is a wiki of his course, not
  a psychology textbook. If he uses a term idiosyncratically, the
  article reflects his usage, with the mainstream divergence noted
  once in **How Kurpatov uses this**.
- **No citations to external sources.** Kurpatov's lectures are the
  only authority this wiki defers to. If a claim would benefit from
  an external reference, put it in `## Related concepts` as a
  gentle nudge, not as a footnote.
- **Slug discipline.** Kebab-case, English, lowercase, ASCII. The
  slug is the filename, the anchor, and the index key — renaming it
  later is costly. Pick carefully on first introduction; ask the
  operator if unsure.
- **Append-only going forward.** After this prompt seeds the file,
  later sources add `### <slug>` entries below. They do not edit
  the `## Definition` or earlier contributions without an explicit
  correction note in the commit message.

## What you do NOT do

- Write an exhaustive academic entry. This is lecture notes, not
  Wikipedia.
- Import standard-psychology definitions wholesale. If Kurpatov
  hasn't said it, the wiki doesn't assert it as his view.
- Pre-populate the "Contributions by source" log with future
  guesses. Only the source that is currently being processed appears
  there.


**Transitive coverage** (per ADR 0013 dec 9 + ADR 0017):
measurable motivation chain (OKRs) inherited from
[wiki-ingest AGENTS.md](../AGENTS.md). This prompt is the
SKILL contract concept-curator follows; its motivation lives
at the lab level.
