# Prompts for the wiki layer

> **Design-trail mirror.** The authoritative working copies of these
> prompts now live in the wiki repo at
> `kurpatov-wiki-wiki/prompts/`, alongside the authoring playbook at
> `kurpatov-wiki-wiki/docs/authoring.md`. Operational edits happen
> there and ride the wiki's git history under the `prompt:` commit
> subject. The copies in *this* directory are retained as the design
> trail tied to ADR 0007 — they document the prompt shape the ADR was
> accepted against. If you want the current operational version, read
> the wiki repo.
>
> The earlier "prompts live in forge, content lives in
> `kurpatov-wiki-wiki`" invariant is superseded by ADR 0007's
> amendment (2026-04-19). See the ADR for the rationale — in short,
> the separation is now semantic (via the `prompt:` subject) rather
> than physical (via repo boundary), which is what the invariant was
> really about.

Design context: [ADR 0007 — wiki layer: Mac-side authoring, two-tier
structure](../docs/adr/0007-wiki-layer-mac-side.md).

Session runbook (design-trail mirror):
[../docs/mac-side-wiki-authoring.md](../docs/mac-side-wiki-authoring.md).

## Files

- [`per-video-summarize.md`](per-video-summarize.md) — the primary
  prompt. Given one `raw.json`, the current `concept-index.json`, and
  the list of prior video slugs, produces a video article plus the
  set of concept-article deltas the video implies.
- [`concept-article.md`](concept-article.md) — the prompt used when a
  concept is newly introduced (no existing file under `concepts/`).
  Seeds the concept article with a definition + first contribution
  entry. Later videos append to the existing article; they do not
  re-run this prompt.

## Why prompts and not code

The only "code" needed on the authoring side is a small amount of
glue for reading `raw.json`, updating `concept-index.json`, writing
markdown, and `git add/commit/push`. That's operator-level scripting
(or direct tool calls inside a Cowork session), not a library.

The interesting IP of the pipeline is the prompts — the instructions
for "what does a good video article look like, what qualifies as
'new', how do concept contributions read." Keeping them as prose
files means a new operator (or a later model) can read them directly
and understand what the wiki is supposed to feel like without
excavating Python.

## Changing a prompt

A prompt change is a decision about the wiki's voice. Minor tweaks
(fixing a typo, clarifying an example) go in on a normal commit.
Substantive changes (adding a new required section, changing the
"new ideas" definition) should be accompanied by a note in the
commit message about whether prior articles need to be re-visited.
Re-visiting is never silent: if we decide older articles should be
regenerated against a new prompt, that's its own batch of commits in
the wiki repo, with a clear "prompt-v2 pass" subject line.
