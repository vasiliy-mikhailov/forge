# ADR 0007 — wiki layer: Mac-side authoring, two-tier structure

## Status
Accepted (2026-04-19). Amends ADR 0005 ("split transcription and git-push
into two containers"): ADR 0005 anticipated a symmetrical server-side
`kurpatov-wiki-wiki-pusher` container. This ADR supersedes that
expectation — there is no server-side pusher for the wiki layer today.
The `kurpatov-wiki-wiki` GitHub repo is authored from the operator's
Mac, in a Claude Desktop (Cowork) session. The **Cowork session itself
is the pusher** — it runs `git pull`, `git add`, `git commit`, and
`git push` via its own Bash tool, guided by CLAUDE.md and the prompts
in the wiki repo's `prompts/` directory (see "Amended" below).
The architectural symmetry with ADR 0005 holds at a different layer:
server-side the pusher is a container, Mac-side the pusher is a
Cowork session. Neither is an operator running commit scripts. The
server's role ends at publishing `raw.json` to the
`kurpatov-wiki-raw` repo.

Amended (2026-04-19 — data/content split). The wiki repo layout
under **Decision** below is now a two-subtree split: `/data/` holds
all content (`index.md`, `concept-index.json`, `concepts/`,
`videos/`); the root holds meta (`CLAUDE.md`, `README.md`,
`prompts/`, `docs/`). The sibling `kurpatov-wiki-raw` repo mirrors
the split — transcripts live under `data/<course>/<module>/<stem>/
raw.json`, not at the repo root. Rationale: course names and concept
slugs are unconstrained content-addressed strings; a future video
called `prompts` or a concept called `readme` would collide with a
tooling file in the same namespace. Cost: every cross-repo path
reference gains a `data/` segment. The ADR body below has been
updated in place; the pre-amendment layout survives only in git
history.

Amended (2026-04-19 — prompts migrate to the wiki repo). The
invariant "Prompts live in `forge`, content lives in
`kurpatov-wiki-wiki`" is superseded. The authoritative working
copies of `per-video-summarize.md`, `concept-article.md`, and the
authoring playbook now live in `kurpatov-wiki-wiki/prompts/` and
`kurpatov-wiki-wiki/docs/authoring.md`. The original concern — not
mixing prompt churn with content churn in one git history — is now
addressed in the wiki repo itself via the `prompt:` commit-subject
convention, which keeps prompt changes independently auditable. The
forge-side `kurpatov-wiki/prompts/*.md` and `kurpatov-wiki/docs/
mac-side-wiki-authoring.md` are kept as the design-trail mirror
that accompanies this ADR; operational editing happens in the wiki
repo.

## Context

Once `vault/raw/<stem>/raw.json` started accumulating (ADR 0002,
ADR 0005), the next layer is turning those transcripts into something
a human actually wants to read. Three candidate architectures were on
the table:

1. **Local vLLM daemon**, riding either `KURPATOV_WIKI_GPU_UUID`
   (shared with the transcriber via ADR 0003 idle-unload) or
   `RL_2048_GPU_UUID` (pausing RL while summarizing). Both variants
   add a GPU-bound service with its own watchdog, model checkpoints
   on disk, and a scheduling story. Quality on Russian
   psychology-lecture prose is an open question for every candidate
   open-weights model we'd run locally — and running a benchmark
   across Qwen / DeepSeek / Yi / Mistral just to pick one is its own
   multi-day project.
2. **API (Anthropic Claude) called from a server daemon.** Solves
   quality, adds `ANTHROPIC_API_KEY` to `.env`, introduces per-lecture
   cost (~dollars per hour of lecture at current pricing), and moves
   the summarization data outside the home lab.
3. **Mac-side Claude Desktop session.** The operator already has
   Claude Desktop (Cowork) with the same Claude that would be called
   via API — but with zero marginal API cost, full conversation
   history retained in the Claude account, and the ability to have a
   genuine back-and-forth with the model about edge cases ("is this
   really a new concept, or a rephrasing of neocortex?"). The
   human-in-the-loop is not a cost here: it is the point. Deciding
   what constitutes a "concept" in psychology is a human call; so is
   deciding which idea is "new" in video N if a previous video's
   phrasing was slightly different.

Option 3 removes an entire operational surface (a new service, a new
GPU budget, a new secret) and buys better output quality. The trade-off
is that summarization is no longer a cron job — it only happens when
the operator opens a session. That's not a regression; given the
current cadence (a few lectures per week, manually curated course
structure), it's actually right-sized.

### Two-tier wiki structure

Kurpatov's lectures are concept-heavy. The naïve "one summary per
video" layout loses the most useful property we can give a reader:
the ability to **read only the delta**. If a reader watched videos
1..N-1, what's genuinely new in video N? And when the reader hits an
unfamiliar concept in that delta, where do they go for depth?

Two article types, two directories, one shared concept registry:

```
kurpatov-wiki-wiki/               (repo root)
├── CLAUDE.md                     ← session entrypoint (meta)
├── README.md                     ← reading protocol (meta)
├── .gitignore                    ← (meta)
├── prompts/                      ← authoring prompts (meta)
│   ├── per-video-summarize.md
│   └── concept-article.md
├── docs/                         ← design + playbook (meta)
│   ├── design.md
│   └── authoring.md
└── data/                         ← all content lives under here
    ├── index.md                  ← course / module / video order, concept A-Z
    ├── concept-index.json        ← machine-readable concept registry (authoring state)
    ├── concepts/
    │   ├── _template.md          ← boilerplate for a new concept article
    │   ├── neocortex.md          ← one article per concept
    │   ├── defense-mechanism.md
    │   └── ...
    └── videos/
        ├── _template.md          ← boilerplate for a new video article
        └── <course>/<module>/<stem>.md
```

The split is deliberate. Course names and concept slugs are
unconstrained content-addressed strings; a future video called
`prompts` or a concept called `readme` would collide with a tooling
file if everything lived at the repo root. Keeping meta at the root
and content under `data/` removes that failure mode at the cost of
one `data/` segment in every cross-repo path reference. The sibling
`kurpatov-wiki-raw` repo mirrors the split — transcripts live under
`data/<course>/<module>/<stem>/raw.json`.

A **video article** has three load-bearing sections:

- `## TL;DR` — 1-2 sentences: what this lecture is about at the
  top level.
- `## New ideas` — ideas this lecture introduces **that do not
  appear in any previously-processed video**. The reader's
  fast-track. Each new idea is either a new concept (add to
  `concepts/`) or a new claim about an existing concept (add to
  that concept's contribution log).
- `## All ideas` — the full ideational content, grouped by concept,
  each item cross-linking to its concept article. Includes things
  that aren't new — for completeness and for readers who don't walk
  the lecture sequence in order.

A **concept article** is an ever-growing article about one concept
(neocortex, defense mechanism, transactional analysis, etc.), with a
"Contributions by video" log appended to on each pass. Concepts are
never rewritten destructively; each pass appends.

### State: concept-index.json

The "new ideas" section is a function of the **cumulative concept set
at time of writing**. To make sessions resumable across machines and
days, we pin that state explicitly rather than inferring it by
re-reading every video article every time.

`data/concept-index.json` lives in the wiki repo and contains:

```json
{
  "generated_at": "2026-04-19T12:00:00Z",
  "processed_videos": [
    {
      "slug": "Psychologist-consultant/05-conflicts/005-something",
      "processed_at": "2026-04-19T12:00:00Z",
      "concepts_touched": ["neocortex", "defense-mechanism"],
      "concepts_introduced": ["defense-mechanism"]
    },
    ...
  ],
  "concepts": {
    "neocortex": {
      "first_introduced_in": "Psychologist-consultant/01-intro/001-brain",
      "touched_by": ["...", "..."]
    },
    ...
  }
}
```

Every Mac-side session starts by reading this file. The "new ideas"
determination for video N uses `concepts` as the baseline: anything
NOT in that dict is a candidate for a new concept; anything in there
is old.

## Decision

### Authoring happens on the Mac, in a Claude Desktop session

A Mac-side Cowork session clones two repos into a working directory
(e.g. `~/forge-wikiwork/`):

- `kurpatov-wiki-raw` (read-only for this flow — content is written
  by the server-side raw-pusher, ADR 0005).
- `kurpatov-wiki-wiki` (read-write).

Per session, all steps run by the Cowork session via its Bash tool
(the operator orchestrates and reviews, but does not type the git
commands):

1. `git -C ~/forge-wikiwork/raw pull --ff-only`.
2. `git -C ~/forge-wikiwork/wiki pull --ff-only`.
3. Load `data/concept-index.json`.
4. Pick the next unprocessed video in course order (the playbook in
   `docs/authoring.md` defines the ordering rule).
5. Read `data/<course>/<module>/<stem>/raw.json` from the raw repo
   for that video; produce
   `data/videos/<course>/<module>/<stem>.md` in the wiki repo + any
   new concept files under `data/concepts/` + any concept updates +
   an updated `data/concept-index.json`.
6. `git -C ~/forge-wikiwork/wiki add -A && git -C ~/forge-wikiwork/wiki
   commit -m "video: <slug>" && git -C ~/forge-wikiwork/wiki push`.
7. Loop to step 4 until the session ends or the operator is tired.

No automation. No daemon. No server-side pusher for the wiki layer.
But also no Mac-side commit scripts: the session handles its own
git flow end-to-end, because the editorial work and the push are
the same action.

### The prompts are part of the wiki repo

`kurpatov-wiki-wiki/prompts/per-video-summarize.md` and
`kurpatov-wiki-wiki/prompts/concept-article.md` are the prompts the
Mac-side session reads at the start of authoring, alongside the
playbook at `kurpatov-wiki-wiki/docs/authoring.md`. They are prose,
version-controlled, reviewed in-tree. Prompt changes ride the same
history as content changes but are kept independently auditable via
the `prompt:` commit-subject convention (distinct from `video:`,
`concept:`, `index:`, `docs:`). If a prompt changes, a new pass
over prior videos may be warranted; the decision to re-process is
explicit, not implicit, and is recorded as a `prompt-v2 pass: <slug>`
commit on each re-processed video.

The copies under `forge/kurpatov-wiki/prompts/` and
`forge/kurpatov-wiki/docs/mac-side-wiki-authoring.md` are kept as
the design-trail mirror tied to this ADR. They are not edited for
operational use — edits go to the wiki repo.

### No server-side wiki service

The server does not read or write `vault/wiki/`. `${STORAGE_ROOT}/
kurpatov-wiki/vault/wiki/` is not created by `make setup`; it stays
empty unless the operator manually clones the wiki repo there for
backup (which is optional and out of scope for this ADR). The
canonical location of the wiki is GitHub; the canonical author is
the Mac.

## Consequences

- Plus: zero new server infrastructure. No GPU contention, no new
  container, no new secret, no new deploy key on the server. Smoke
  test unchanged.
- Plus: best available quality for Russian psychology prose, because
  the same Claude that would otherwise be called via API is directly
  in the loop with the operator.
- Plus: editorial disputes ("is this really a new concept?") are
  resolved in real conversation, not by prompt tuning.
- Plus: the wiki's authoring state (`concept-index.json`) is just a
  committed JSON file. Anyone with a clone of the wiki repo can
  resume where the last session left off — including on a second Mac.
- Minus: summarization does not happen on its own. If no session is
  opened for a month, no wiki is produced for a month. This matches
  the actual cadence of the project; if it ever stops matching, that
  is a trigger to revisit (not an emergency).
- Minus: single human bottleneck. Mitigated by the `concept-index.json`
  state file: if a second operator helps, they start from the same
  state.
- Minus: the ADR 0005 expectation of a symmetrical
  `kurpatov-wiki-wiki-pusher` is now stale. This ADR is the
  supersession record.

## Invariants

- **Video ordering.** Videos MUST be processed in course order. The
  source naming convention encodes this order at every level —
  modules are zero-padded (`01-intro`, `05-conflicts`), stems carry
  zero-padded numeric prefixes (`005 Conflict nature`) — so
  sorted-path order equals course order with no manual annotation.
  Video-article frontmatter therefore does **not** carry a numeric
  `order:` field; the slug (path) is the order. "New ideas" is only
  meaningful against the already-processed prefix.
- **`concept-index.json` is authoritative state.** A session MUST
  read it before authoring, and MUST commit the updated version at
  the end of every push. Drift between the JSON and the `concepts/`
  files on disk is a bug; the session is expected to detect and fix
  it (the playbook spells out how).
- **Concept articles are append-only.** A later video adds to a
  concept article; it does not rewrite prior contributions, because
  that would silently invalidate the "new ideas" determinations of
  earlier videos. Fixes to genuinely wrong prior content are
  explicit edits with a commit message spelling out why.
- **No server writes to `vault/wiki/`.** The server mounts
  `${STORAGE_ROOT}/kurpatov-wiki/vault/` into the transcriber and
  jupyter containers for access to `raw/`, but neither service
  writes into `vault/wiki/`. If a future service needs to, that's a
  new ADR.
- **Meta at the root, content under `data/`.** The wiki repo keeps
  `CLAUDE.md`, `README.md`, `prompts/`, and `docs/` at the repo
  root; `index.md`, `concept-index.json`, `concepts/`, and
  `videos/` live under `data/`. The raw repo mirrors this: transcripts
  are under `data/<course>/<module>/<stem>/raw.json`. A future video
  slug or concept slug must never be able to collide with a tooling
  filename.
- **Commit subjects distinguish prompt churn from content churn.**
  Prompt edits use the `prompt:` subject; content authoring uses
  `video:`, `concept:`, `index:`. `prompt-v2 pass: <slug>` marks a
  re-processing of an existing video against a revised prompt. This
  replaces the earlier "prompts live in a different repo" invariant
  — the separation is now semantic (via subject) rather than physical
  (via repo boundary).

## Alternatives considered

- **Local vLLM daemon (shared kurpatov-wiki GPU).** Rejected —
  doubles GPU contention on the already-shared card, introduces a
  model-selection benchmark, adds a new failure surface (vLLM OOM,
  model reload) for a workload that only runs a few times a week.
- **Local vLLM daemon (rl-2048 GPU).** Same problems; also creates a
  priority conflict between "summarize a lecture now" and "continue
  the RL run that's been going for 6 hours." No good resolution
  that doesn't require manual intervention — at which point the
  "manual" part of option 3 is doing the same work with better
  output.
- **Anthropic API from a server daemon.** Rejected — the Mac-side
  session uses the same model without the cost-per-run, and the
  human-in-the-loop step is actually valuable for this editorial
  task, not a bottleneck to engineer around.
- **One article per video, no concept tier.** Rejected — loses the
  "fast reader reads only new ideas" property, which is the main
  reason to build a wiki at all instead of just reading the
  transcripts.
- **Concept tier only, no per-video articles.** Rejected — loses
  the chronological record of how Kurpatov himself builds up a
  concept across lectures. The video article's "new ideas" section
  is also what makes the concept article's "Contributions by video"
  log populable without re-reading every transcript.

## Follow-ups

- Playbook: `kurpatov-wiki-wiki/docs/authoring.md` — the concrete
  session runbook, including the ordering rule and the concept-index
  drift-detection procedure. Lives in the wiki repo because it churns
  with operator experience; the forge-side
  `kurpatov-wiki/docs/mac-side-wiki-authoring.md` is the
  design-trail mirror.
- First seed commit of `kurpatov-wiki-wiki`: CLAUDE.md, README,
  prompts, playbook, `data/` scaffolding (empty `concept-index.json`,
  templates). Produced under `outputs/kurpatov-wiki-wiki-seed/` in
  the earlier session and pushed via
  `outputs/seed-wiki-repo.sh`. The subsequent `data/` refactor was
  applied via `outputs/migrate-wiki-to-data.sh`.
- Raw-side `data/` migration: the transcriber's
  `03_watch_and_transcribe.py` now writes to
  `/workspace/vault/raw/data/<course>/<module>/<stem>/raw.json`;
  the pusher's `04_watch_raw_and_push.py` watches the same subtree
  while keeping its `--vault` (git working tree) at
  `/workspace/vault/raw/`. Existing content was moved via the
  server-side migration script referenced in ADR 0005's amendment.
- Deploy key and SSH config for the wiki repo on the Mac. Mirrors the
  server-side key file for the raw repo but lives on the Mac; not
  committed to git.
- If/when the wiki volume outgrows a weekly Mac session, revisit:
  could a server-side daemon (local vLLM or API) produce *draft*
  articles that the operator reviews in-session? That would be a
  new ADR, not a change to this one.
- Translation of "ideas" / "concepts" vocabulary across English and
  Russian. The concept slugs are English (kebab-case). The article
  prose is whichever language reads best for the concept — the
  playbook captures how to resolve ambiguity.
