# ADR 0007 — wiki layer: Mac-side authoring, two-tier structure

## Path map for current readers

This ADR was written before the labs/-restructure (`forge:phase-g/adr/0007-labs-restructure-self-contained-caddy.md`) and predates the TOGAF-phase repo layout. The body below uses the path names that were correct at the time. Map to current paths:

- forge/kurpatov-wiki/prompts/ → forge/phase-c-…/application-architecture/wiki-ingest/prompts/
- forge/kurpatov-wiki/docs/mac-side-wiki-authoring.md → forge/phase-c-…/application-architecture/wiki-ingest/docs/mac-side-wiki-authoring.md
- kurpatov-wiki/SPEC.md → wiki-ingest/SPEC.md (in this lab)
- kurpatov-wiki/vault/wiki/ → ${STORAGE_ROOT}/labs/wiki-ingest/vault/wiki/

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
copies of `per-source-summarize.md`, `concept-article.md`, and the
authoring playbook now live in `kurpatov-wiki-wiki/prompts/` and
`kurpatov-wiki-wiki/docs/authoring.md`. The original concern — not
mixing prompt churn with content churn in one git history — is now
addressed in the wiki repo itself via the `prompt:` commit-subject
convention, which keeps prompt changes independently auditable. The
forge-side `kurpatov-wiki/prompts/*.md` and `kurpatov-wiki/docs/
mac-side-wiki-authoring.md` are kept as the design-trail mirror
that accompanies this ADR; operational editing happens in the wiki
repo.

Amended (2026-04-20 — working copies in the session's sandbox
workspace, not the Mac's home). The "Mac-side" shorthand in this
ADR's title and body means "Cowork session running on the
operator's Mac, not a server-side daemon". The original body
placed the session's working clones under `~/forge-wikiwork/` on
the Mac's filesystem — i.e. paths in the operator's actual
`$HOME`. That has changed: the Cowork session now keeps its
clones in its own persistent sandbox workspace (concretely
`~/repos/kurpatov-wiki-raw` and `~/repos/kurpatov-wiki-wiki` where
`~` is the session's home inside its Linux sandbox, not the
operator's Mac home). The operator's Mac home no longer has a
`~/forge-wikiwork/` directory; it was removed as part of this
amendment. GitHub push auth is the session's own ed25519 SSH key
(registered once on the operator's GitHub account as a user SSH
key, title `kurpatov-wiki-cowork-session`) — not a deploy key on
the Mac. The follow-up "Deploy key and SSH config for the wiki
repo on the Mac" below is correspondingly obsolete. The
invariants are unchanged: the session is the pusher, no
server-side daemon authors the wiki, the human-in-the-loop stays.


Amended (2026-04-20/2026-04-21 — HTML sources reach the wiki as
first-class source articles). The ingest pipeline (server-side)
grew a second extractor for getcourse.ru HTML lesson pages; see
[ADR 0008](0008-ingest-dispatch.md). The wiki layer treats them
the same as media-derived raw.json: one source article per
`raw/data/<mirror>/<stem>/raw.json` — the slug is the source
filename minus its extension, for every extractor (the earlier
`<stem>.html`-for-HTML carve-out was reversed on 2026-04-21). The
renderer keys off
`info.extractor` to decide whether the source article should
include timing-based affordances (clickable timestamps) or not
(HTML has no timing). The 2026-04-20 rename
`kurpatov-transcriber` → `kurpatov-ingest` is a server-side
change; the Mac-side prose below still calls it "the
server's ingest side" and is unaffected. The invariant
"no server-side daemon authors the wiki" holds: the ingest
daemon still only writes raw.json.

Amended (2026-04-20 — videos/ → sources/ rename). In both the wiki
repo and in this ADR's prose, the former tier name `videos/` has
been renamed to `sources/`, and `video article` → `source article`.
The rename follows the upstream broadening of accepted input media
(video + audio; see ADR 0004's 2026-04-20 amendment). Corresponding
renames applied downstream: `processed_videos` →
`processed_sources` in `data/concept-index.json`;
`prompts/per-source-summarize.md` →
`prompts/per-source-summarize.md`; commit subject `video:` →
`source:` for per-source authoring passes; "Contributions by video"
log heading in concept articles → "Contributions by source". The
invariants below (ordering via zero-padded module/stem prefixes;
append-only concept articles; `concept-index.json` as authoritative
state; meta-at-root / content-under-data) are unchanged. This ADR's
body has been updated in place; the pre-rename wording survives
only in git history.

Amended (2026-04-24 — provenance + fact-check pass in per-source
authoring). The per-source authoring loop now runs every claim in
the lecture through a mandatory four-way classification pass:
`NEW` (not in any previously-processed source), `REPEATED (from:
<slug>)` (already in an earlier source), `CONTRADICTS EARLIER (in:
<slug>)` (disagrees with a prior source — both sides quoted), or
`CONTRADICTS FACTS` (disagrees with current external evidence —
primary-source citation attached). The priority order for
fact-checking is peer-reviewed paper → textbook → reference site
(Stanford Encyclopedia of Philosophy, NIH MedlinePlus, …) →
high-quality journalism; Wikipedia is allowed only as a pointer
to primary sources. When the web evidence is inconclusive, the
claim falls back to `NEW` / `REPEATED` with a `Notes` caveat —
the `CONTRADICTS FACTS` marker is reserved for cases where a
clear primary-source contradiction is in hand.

The shape of the source article under "Decision" below changes
accordingly: three required sections become four. A new mandatory
`## Claims — provenance and fact-check` section sits between
`## TL;DR` and the new filtered `## New ideas (verified)` section
(which contains only pure-`NEW`, fact-check-clean claims — the
renamed "fast reader's path" that was previously `## New ideas`).
`## All ideas` retains every claim but tags each bullet with its
provenance marker. Frontmatter gains `fact_check_performed:
true | false`. Concept articles stay strictly append-only:
contradictions with earlier sources are recorded inside the *new*
source's Contributions entry by quoting both sides — the earlier
entry is not rewritten. The human-in-the-loop invariant from the
Decision below is unchanged and, if anything, reinforced: the
operator is the escalation path for editorial judgment calls,
including inconclusive fact-checks.

Rationale: a Kurpatov lecture reprises prior material, occasionally
contradicts earlier lectures, and occasionally states empirical
claims that disagree with the current scientific consensus. The
original "new ideas" design silently blended all three categories
into the reader's fast path, which degrades reader trust on first
encounter. Splitting the output into an auditable `Claims` section
and a trusted `New ideas (verified)` section keeps the fast-path
property without letting contamination flow through. The cost is
real authoring time per source (the fact-check pass takes
non-trivial web lookups); it is accepted because the wiki is
cheaper to read correctly than to re-verify at read time.

Backfill note: three source articles authored before this
amendment (module 005, stems 000/001/002 of the
Психолог-консультант course) predate the new spec and lack both
the `## Claims — provenance and fact-check` section and the
`fact_check_performed` frontmatter field. They will be backfilled
in a dedicated `prompt-v2 pass:` when the operator schedules it;
the wiki repo's `CLAUDE.md` → Status and `docs/authoring.md` →
Known gaps carry the reminder.

The authoritative prose of the pass (procedure, citation priority,
example) lives in `kurpatov-wiki-wiki/prompts/per-source-summarize.md`;
the wiki repo's `CLAUDE.md`, `docs/design.md`, and
`docs/authoring.md` are kept in lockstep. The forge-side mirror is
`kurpatov-wiki/SPEC.md` → WIKI layer section and this amendment.

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
   deciding which idea is "new" in source N if a previous source's
   phrasing was slightly different.

Option 3 removes an entire operational surface (a new service, a new
GPU budget, a new secret) and buys better output quality. The trade-off
is that summarization is no longer a cron job — it only happens when
the operator opens a session. That's not a regression; given the
current cadence (a few lectures per week, manually curated course
structure), it's actually right-sized.

### Two-tier wiki structure

Kurpatov's lectures are concept-heavy. The naïve "one summary per
source" layout loses the most useful property we can give a reader:
the ability to **read only the delta**. If a reader watched sources
1..N-1, what's genuinely new in source N? And when the reader hits an
unfamiliar concept in that delta, where do they go for depth?

Two article types, two directories, one shared concept registry:

```
kurpatov-wiki-wiki/               (repo root)
├── CLAUDE.md                     ← session entrypoint (meta)
├── README.md                     ← reading protocol (meta)
├── .gitignore                    ← (meta)
├── prompts/                      ← authoring prompts (meta)
│   ├── per-source-summarize.md
│   └── concept-article.md
├── docs/                         ← design + playbook (meta)
│   ├── design.md
│   └── authoring.md
└── data/                         ← all content lives under here
    ├── index.md                  ← course / module / source order, concept A-Z
    ├── concept-index.json        ← machine-readable concept registry (authoring state)
    ├── concepts/
    │   ├── _template.md          ← boilerplate for a new concept article
    │   ├── neocortex.md          ← one article per concept
    │   ├── defense-mechanism.md
    │   └── ...
    └── sources/
        ├── _template.md          ← boilerplate for a new source article
        └── <course>/<module>/<stem>.md
```

The split is deliberate. Course names and concept slugs are
unconstrained content-addressed strings; a future source called
`prompts` or a concept called `readme` would collide with a tooling
file if everything lived at the repo root. Keeping meta at the root
and content under `data/` removes that failure mode at the cost of
one `data/` segment in every cross-repo path reference. The sibling
`kurpatov-wiki-raw` repo mirrors the split — transcripts live under
`data/<course>/<module>/<stem>/raw.json`.

A **source article** has four load-bearing sections (the
2026-04-24 amendment above added `## Claims — provenance and
fact-check` and split the former `## New ideas` into an audit
trail + a filtered fast-reader path):

- `## TL;DR` — 1-2 sentences: what this lecture is about at the
  top level.
- `## Claims — provenance and fact-check` — every substantive
  claim in the lecture, each tagged with exactly one of `NEW`,
  `REPEATED (from: <slug>)`, `CONTRADICTS EARLIER (in: <slug>)`,
  or `CONTRADICTS FACTS` (with a primary-source citation). Both
  sides are quoted for `CONTRADICTS EARLIER`; the external
  citation is explicit for `CONTRADICTS FACTS`. See the
  amendment for the citation priority list.
- `## New ideas (verified)` — the filtered output: only claims
  tagged pure-`NEW` that survived the fact-check. The reader's
  fast-track. Each item is either a new concept (add to
  `concepts/`) or a new claim about an existing concept (add to
  that concept's contribution log).
- `## All ideas` — the full ideational content, grouped by concept,
  each bullet tagged with its provenance marker (`[NEW]`,
  `[REPEATED]`, `[CONTRADICTS EARLIER]`, `[CONTRADICTS FACTS]`)
  and cross-linked to its concept article. Includes things that
  aren't new — for completeness, for readers who don't walk the
  lecture sequence in order, and as the audit trail behind the
  filtered `## New ideas (verified)` above.

A **concept article** is an ever-growing article about one concept
(neocortex, defense mechanism, transactional analysis, etc.), with a
"Contributions by source" log appended to on each pass. Concepts
are never rewritten destructively; each pass appends. When a new
source's claim contradicts an earlier contribution, the new entry
quotes both sides side-by-side — the earlier entry is not edited.

### State: concept-index.json

The "new ideas" section is a function of the **cumulative concept set
at time of writing**. To make sessions resumable across machines and
days, we pin that state explicitly rather than inferring it by
re-reading every source article every time.

`data/concept-index.json` lives in the wiki repo and contains:

```json
{
  "generated_at": "2026-04-19T12:00:00Z",
  "processed_sources": [
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

### Authoring happens in a Mac-hosted Claude Desktop (Cowork) session

A Cowork session — a process running on the operator's Mac as part
of Claude Desktop — clones two repos into its own persistent
sandbox workspace under `~/repos/` (where `~` is the session's
sandbox home, not the Mac's user home — see the 2026-04-20
amendment above):

- `kurpatov-wiki-raw` (read-only for this flow — content is written
  by the server-side raw-pusher, ADR 0005).
- `kurpatov-wiki-wiki` (read-write).

Per session, all steps run by the Cowork session via its Bash tool
(the operator orchestrates and reviews, but does not type the git
commands):

1. `git -C ~/repos/kurpatov-wiki-raw  pull --ff-only`.
2. `git -C ~/repos/kurpatov-wiki-wiki pull --ff-only`.
3. Load `data/concept-index.json`.
4. Pick the next unprocessed source in course order (the playbook in
   `docs/authoring.md` defines the ordering rule).
5. Read `data/<course>/<module>/<stem>/raw.json` from the raw repo
   for that video; produce
   `data/sources/<course>/<module>/<stem>.md` in the wiki repo + any
   new concept files under `data/concepts/` + any concept updates +
   an updated `data/concept-index.json`.
6. `git -C ~/repos/kurpatov-wiki-wiki add -A && git -C ~/repos/kurpatov-wiki-wiki
   commit -m "source: <slug>" && git -C ~/repos/kurpatov-wiki-wiki push`.
7. Loop to step 4 until the session ends or the operator is tired.

No automation. No daemon. No server-side pusher for the wiki layer.
But also no Mac-side commit scripts: the session handles its own
git flow end-to-end, because the editorial work and the push are
the same action.

### The prompts are part of the wiki repo

`kurpatov-wiki-wiki/prompts/per-source-summarize.md` and
`kurpatov-wiki-wiki/prompts/concept-article.md` are the prompts the
Mac-side session reads at the start of authoring, alongside the
playbook at `kurpatov-wiki-wiki/docs/authoring.md`. They are prose,
version-controlled, reviewed in-tree. Prompt changes ride the same
history as content changes but are kept independently auditable via
the `prompt:` commit-subject convention (distinct from `source:`,
`concept:`, `index:`, `docs:`). If a prompt changes, a new pass
over prior sources may be warranted; the decision to re-process is
explicit, not implicit, and is recorded as a `prompt-v2 pass: <slug>`
commit on each re-processed source.

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

- **Source ordering.** Sources MUST be processed in course order. The
  source naming convention encodes this order at every level —
  modules are zero-padded (`01-intro`, `05-conflicts`), stems carry
  zero-padded numeric prefixes (`005 Conflict nature`) — so
  sorted-path order equals course order with no manual annotation.
  Source-article frontmatter therefore does **not** carry a numeric
  `order:` field; the slug (path) is the order. "New ideas" is only
  meaningful against the already-processed prefix.
- **`concept-index.json` is authoritative state.** A session MUST
  read it before authoring, and MUST commit the updated version at
  the end of every push. Drift between the JSON and the `concepts/`
  files on disk is a bug; the session is expected to detect and fix
  it (the playbook spells out how).
- **Concept articles are append-only.** A later source adds to a
  concept article; it does not rewrite prior contributions, because
  that would silently invalidate the "new ideas" determinations of
  earlier sources. Fixes to genuinely wrong prior content are
  explicit edits with a commit message spelling out why.
- **No server writes to `vault/wiki/`.** The server mounts
  `${STORAGE_ROOT}/labs/wiki-ingest/vault/` into the transcriber and
  jupyter containers for access to `raw/`, but neither service
  writes into `vault/wiki/`. If a future service needs to, that's a
  new ADR.
- **Meta at the root, content under `data/`.** The wiki repo keeps
  `CLAUDE.md`, `README.md`, `prompts/`, and `docs/` at the repo
  root; `index.md`, `concept-index.json`, `concepts/`, and
  `sources/` live under `data/`. The raw repo mirrors this: transcripts
  are under `data/<course>/<module>/<stem>/raw.json`. A future source
  slug or concept slug must never be able to collide with a tooling
  filename.
- **Commit subjects distinguish prompt churn from content churn.**
  Prompt edits use the `prompt:` subject; content authoring uses
  `source:`, `concept:`, `index:`. `prompt-v2 pass: <slug>` marks a
  re-processing of an existing source against a revised prompt. This
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
- **One article per source, no concept tier.** Rejected — loses the
  "fast reader reads only new ideas" property, which is the main
  reason to build a wiki at all instead of just reading the
  transcripts.
- **Concept tier only, no per-source articles.** Rejected — loses
  the chronological record of how Kurpatov himself builds up a
  concept across lectures. The source article's "new ideas" section
  is also what makes the concept article's "Contributions by source"
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
- ~~Deploy key and SSH config for the wiki repo on the Mac. Mirrors the
  server-side key file for the raw repo but lives on the Mac; not
  committed to git.~~ **Obsolete (2026-04-20):** the wiki repo is
  pushed from the Cowork session's sandbox using the session's own
  ed25519 SSH key, registered on the operator's GitHub account.
  See the 2026-04-20 amendment under Status.
- If/when the wiki volume outgrows a weekly Mac session, revisit:
  could a server-side daemon (local vLLM or API) produce *draft*
  articles that the operator reviews in-session? That would be a
  new ADR, not a change to this one.
- Translation of "ideas" / "concepts" vocabulary across English and
  Russian. The concept slugs are English (kebab-case). The article
  prose is whichever language reads best for the concept — the
  playbook captures how to resolve ambiguity.
