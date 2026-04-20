# Mac-side wiki authoring — session runbook

> **Design-trail mirror.** The authoritative working copy of this
> playbook lives at `kurpatov-wiki-wiki/docs/authoring.md` in the
> wiki repo, alongside the prompts it references. Operational
> edits land there (under the `docs:` commit subject). This copy in
> forge is retained as the design trail for ADR 0007 and is kept
> roughly synchronized for cross-repo readability — but if the two
> drift, the wiki repo's version is authoritative.

This is the concrete playbook for a Claude Desktop (Cowork) session
that produces wiki articles from raw transcripts. Design rationale:
[ADR 0007](adr/0007-wiki-layer-mac-side.md). Prompts the session uses
(design-trail mirror): [`../prompts/`](../prompts/); the running
copies live in the wiki repo's `prompts/`.

Scope: everything a new session needs to know to open the
`kurpatov-wiki-wiki` repo, pick up where the last session left off,
process N sources, and push.

**Who runs the git commands.** The Cowork session itself runs
`git pull`, `git add`, `git commit`, and `git push` through its own
Bash tool, using the session's own ed25519 SSH key (registered on
the operator's GitHub account) to authenticate. The session is the wiki pusher — the architectural mirror of
the server-side `kurpatov-wiki-raw-pusher` container, with CLAUDE.md +
this playbook as its program. The operator opens the session, points
at a starting slug, and reviews diffs; typing out git invocations is
not part of the operator's job.

## One-time bootstrap (per session)

Only needed on a fresh Cowork session with an empty sandbox.

### Working directory layout

Two sibling clones under the session's persistent sandbox
workspace:

```
~/repos/
├── kurpatov-wiki-raw    ← git clone of kurpatov-wiki-raw    (read-only use)
└── kurpatov-wiki-wiki   ← git clone of kurpatov-wiki-wiki   (read-write)
```

```bash
mkdir -p ~/repos && cd ~/repos
test -d kurpatov-wiki-raw  || git clone git@github.com:vasiliy-mikhailov/kurpatov-wiki-raw.git
test -d kurpatov-wiki-wiki || git clone git@github.com:vasiliy-mikhailov/kurpatov-wiki-wiki.git
```

### SSH auth

The `kurpatov-wiki-raw` deploy key lives on the **server**, not in
the session's sandbox — the session authenticates to GitHub with
its own ed25519 SSH key (`~/.ssh/id_ed25519`, registered on the
operator's GitHub account as a user SSH key, title
`kurpatov-wiki-cowork-session`). No per-repo deploy key on the
session side.

If the sandbox key rotates between sessions and a push is rejected
with "Permission denied (publickey)", surface the current public
key (`cat ~/.ssh/id_ed25519.pub`) to the operator so they can
update the GitHub entry.

### Sanity check

```bash
ls ~/repos/kurpatov-wiki-raw/data   # should show <course>/<module>/<stem>/raw.json
ls ~/repos/kurpatov-wiki-wiki/data  # should show index.md, concept-index.json, concepts/, sources/
```

If the wiki repo is empty or missing the scaffolding, the operator
should first seed it from
[`outputs/kurpatov-wiki-wiki-seed/`](../../../kurpatov-wiki-wiki-seed/)
(produced alongside ADR 0007 in this commit).

## Per-session checklist

The session (not the operator) runs these four steps via its Bash
tool at the start of every session, before touching any content.
They are the cheap safety net against out-of-date state.

1. **Pull both repos.**
   ```bash
   git -C ~/repos/kurpatov-wiki-raw  pull --ff-only
   git -C ~/repos/kurpatov-wiki-wiki pull --ff-only
   ```
   If either pull is not fast-forward, stop and surface the state to
   the operator — the wiki repo in particular should never have
   non-linear history.

2. **Confirm the wiki working tree is clean.**
   ```bash
   git -C ~/repos/kurpatov-wiki-wiki status --short
   ```
   A dirty tree means the last session ended mid-source. Decide with
   the operator: commit-and-push leftover, or `git restore` to
   discard.

3. **Read `concept-index.json`.** It is the authoritative state:
   which sources have been processed, in what order, and which
   concepts are known. The session starts every authoring pass by
   loading it.

4. **Drift check.** Compare the filesystem against
   `concept-index.json`:
   - Every `sources/<slug>.md` on disk must have a matching entry in
     `processed_sources`.
   - Every `concepts/<slug>.md` on disk must have a matching key in
     `concepts`.
   - Every `processed_sources[].concepts_touched` slug must resolve
     to an existing `concepts/<slug>.md`.
   Discrepancies are either a prior incomplete session or a hand-edit
   outside Claude. Resolve them before adding new content — the
   playbook assumes the index is correct.

## Choosing the next source

Sources are processed in **course order**. The source naming
convention already encodes the ordering: `<module>` is zero-padded
(`01-intro`, `05-conflicts`) and `<stem>` starts with a zero-padded
numeric prefix (`001 Title`, `005 Conflict nature`). Sorted-path
order therefore equals course order with no manual annotation.

The ordering rule is literally:

```bash
# from inside the raw repo root
find . -name raw.json | sort
```

and the next source is the first entry in that output whose slug is
**not** already in `concept-index.json.processed_sources`.

Because ordering is implicit in the path, source frontmatter does
not carry a numeric `order:` field. The slug *is* the order.

If the next-to-process source's numeric position jumps (e.g. 003 is
done, 004 is missing, 005 is pending), stop and ask the operator
whether 004 is intentionally skipped. "New ideas" semantics assume
no gaps.

## One-source authoring loop

Per source, in one session cycle:

1. **Read inputs.**
   - `raw/<slug>/raw.json`.
   - `wiki/concept-index.json`.
   - For every concept slug in the likely-touched set (the operator
     or Claude guesses based on skimming the transcript), read the
     existing `wiki/concepts/<concept-slug>.md` so the new
     contribution can be appended rather than duplicated.

2. **Apply the prompt.** Use
   [`../prompts/per-source-summarize.md`](../prompts/per-source-summarize.md).
   Claude produces (in one conversation):
   - The new `sources/<slug>.md`.
   - Zero or more new `concepts/<concept-slug>.md` files — for each
     concept genuinely introduced by this source. Seed prompt:
     [`../prompts/concept-article.md`](../prompts/concept-article.md).
   - Zero or more append-only edits to existing
     `concepts/<concept-slug>.md` files.
   - An updated `concept-index.json`.

3. **Review before committing.** `git diff` the wiki working tree.
   Things to watch for:
   - `concept-index.json` reflects every file change (no orphans,
     no missing entries).
   - No existing concept article had its earlier entries rewritten
     (append-only invariant, ADR 0007).
   - Frontmatter of the new source article is complete and matches
     `concept-index.json`.
   - "New ideas" section is non-empty unless Kurpatov is genuinely
     recapping; in which case the recap sentinel from the prompt
     is used verbatim.

4. **Commit and push.** The session runs these via its Bash tool
   (not the operator):
   ```bash
   git -C ~/repos/kurpatov-wiki-wiki add -A
   git -C ~/repos/kurpatov-wiki-wiki commit -m "source: <slug>"
   git -C ~/repos/kurpatov-wiki-wiki push
   ```
   One commit per source. The commit subject is always `source: <slug>`
   unless the work is something else (see below). If `git push` fails
   (network, auth, non-fast-forward), surface the error to the
   operator rather than retrying blindly.

5. **Loop or stop.** Go back to "Choosing the next source" or wrap
   up the session.

## Commit subject conventions

Keep git history legible at a glance:

- `source: <slug>` — a standard per-source authoring pass, producing a
  source article and cascading concept updates.
- `concept: <slug> — <reason>` — a manual correction to a concept
  article outside the per-source flow (e.g. fixing a definition
  error flagged by the operator). The reason must be human-readable.
- `index: <short reason>` — manual edits to `index.md` or
  `concept-index.json` that are not a side-effect of a source pass.
  These should be rare; if you're running them often, something is
  wrong upstream.
- `prompt-v2 pass: <range>` — a bulk regeneration of prior articles
  against an updated prompt. These are rare and deliberate (see
  `../prompts/README.md` → "Changing a prompt").

## Resuming across sessions

State that carries across sessions lives in git. Nothing on the
Mac's local filesystem is authoritative once pushed. A second
operator, a second Mac, or the same Mac a month later — all pick
up the same state by pulling both repos and reading
`concept-index.json`.

The `touched_by` lists in `concept-index.json.concepts` are what
make "what's new in source N" decidable across sessions without
re-reading every source article.

## Drift — detection and repair

If the drift check in the per-session checklist turns up
discrepancies, resolve in this order of trust:

1. **File-on-disk over index.** If
   `wiki/sources/<slug>.md` exists and `concept-index.json` does not
   list it in `processed_sources` — the file is the truth; amend the
   index to match. Prior session probably crashed before committing
   the index update.
2. **Index over file-on-disk** only in reverse: if
   `processed_sources` lists a slug that has no file on disk — the
   index is wrong. A missing file on disk cannot be an authoring
   artifact; it's an accidental delete. Remove the entry and
   investigate.
3. **If the concepts sets disagree** — every concept slug in
   `concept-index.json.concepts` must have a file; every concept
   file must be in the index. Same rule: file is truth; amend
   index. Opposite direction is suspect.

After any drift repair, commit it with subject
`index: repair drift after <cause>` before processing new content.
Content commits on top of a drift-repair commit are cheap to audit;
mixed commits are not.

## Known gaps

Things this playbook does not yet cover, by design:

- **Multi-operator coordination.** Two operators pulling and pushing
  concurrently can conflict on `concept-index.json`. Low risk today
  (one operator); if it becomes real, add a "reserve a source" step
  (e.g. push an empty `processed_sources` entry first, then fill in).
- **Prompt versioning.** When a prompt changes substantively, prior
  articles may be inconsistent with the new voice. The
  `prompt-v2 pass` convention exists; the decision to run such a
  pass is manual.
- **Translation of concept slugs.** Slugs are English kebab-case;
  article prose is Russian or English as needed. The playbook does
  not mandate a translation for slugs because some Kurpatov terms
  have no clean English rendering. In those cases prefer
  transliteration over mistranslation.
- **Quality review.** No one reads the wiki critically after each
  commit. A periodic re-read pass (every N sources) with the
  operator is healthy but not formalized.
