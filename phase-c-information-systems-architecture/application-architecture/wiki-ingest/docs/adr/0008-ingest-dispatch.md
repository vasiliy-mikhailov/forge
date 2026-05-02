# 0008 — Ingest dispatch: whisper + HTML extractor behind one daemon

Status: Accepted (2026-04-20)

## Path map for current readers

This ADR was written before the labs/-restructure
(`forge:phase-g/adr/0007-labs-restructure-self-contained-caddy.md`)
and predates the TOGAF-phase repo layout. The body below uses the
path names that were correct at the time. Map to current paths:

- kurpatov-wiki/notebooks/02_ingest_incremental.py → wiki-ingest/notebooks/02_ingest_incremental.py (in this lab).

## Context

[ADR 0003](0003-watcher-reactive-not-cron.md) established a single
reactive watcher on `/workspace/sources` — originally
`kurpatov-transcriber`, a container whose only job was to run
faster-whisper against every audio/video file that landed there.

In practice the course material is not all media. Some lessons arrive
as **getcourse.ru HTML exports** — a saved lesson page that contains
the lecturer's prose alongside an embedded video player, student
self-answers, and a comments section. The prose is the canonical
source text for that lesson; the media file that accompanies it (when
there is one) is a spoken rendition of roughly the same content.

Two questions fell out of that:

1. **Should HTML and media co-mingle in `sources/` or live in parallel
   trees?** We want the wiki-layer renderer and the raw-side pusher to
   stay uniform. A single mirror (`raw/data/<mirror>/<slug>/raw.json`)
   is much easier to reason about than two parallel trees.
2. **Is the "transcriber" a good name any more?** The daemon is about
   to grow a second extractor (HTML → segments[]) that never touches
   the GPU. "Transcription" refers specifically to what faster-whisper
   does to audio — calling the daemon a transcriber will mislead every
   future reader.

## Decision

1. **Co-locate in `sources/`; dispatch by suffix.** Media and HTML
   share the same input tree. The watcher dispatches by file suffix:

   ```
   WHISPER_EXTENSIONS = {mp4, mkv, webm, mov, m4v, avi,
                         mp3, m4a, wav, ogg, flac, opus, aac}
   HTML_EXTENSIONS    = {html, htm}
   INGEST_EXTENSIONS  = WHISPER_EXTENSIONS | HTML_EXTENSIONS
   ```

   Any file outside `INGEST_EXTENSIONS` is ignored (so a README.md
   dropped next to a lecture still costs nothing). The allow-list
   lives in `kurpatov-wiki/notebooks/02_ingest_incremental.py` and
   `03_watch_and_ingest.py` — they must stay in sync.

2. **One raw.json schema for both extractors.** HTML reuses the same
   `info` + `segments[]` envelope whisper produces:

   | field                   | whisper | html |
   |-------------------------|---------|------|
   | `info.language`         | yes     | yes  |
   | `info.source_path`      | yes     | yes  |
   | `info.extractor`        | `"whisper"` | `"html"` |
   | `info.extracted_at`     | yes     | yes  |
   | `info.title`            | —       | yes (from `<h2 class="lesson-title-value">`) |
   | `info.transcribed_at`   | yes (alias of `extracted_at`) | — |
   | `info.duration`, `.model`, `.compute_type`, `.beam_size`, `.language_probability`, `.diarized` | yes | — |
   | `info.paragraph_count`  | —       | yes |
   | `segments[].id`         | 1..N    | 1..N |
   | `segments[].text`       | whisper output | one paragraph of lecturer prose |
   | `segments[].start/.end` | seconds | — |
   | `segments[].speaker`    | null placeholder | — |
   | `segments[].words[]`    | word-level timestamps | — |

   `info.extractor` is the single boolean-in-practice switch downstream
   renderers read when they need to know whether timing fields exist.

3. **HTML extraction scope: only lecturer prose.** The extractor
   (`notebooks/_extract_html.py`) harvests only blocks matching
   `div.text-normal.f-text` — the getcourse.ru page-builder class used
   for lecturer-authored text. It **explicitly drops** `.self-answers`,
   `.answer_wrapper`, `.comments-tree`, `.comment-list`, `.comment`,
   `.gc-comment-form`, and the embedded player — so student
   self-reflections, forum comments, and "likes" never leak into the
   vault.

   The page title comes from `h2.lesson-title-value` (falling back to
   `<title>`); it lives in `info.title`, not in `segments[]`, because
   it's metadata, not lecture content.

4. **Output path strips the extension for every extractor.**
   All kinds use the historical stem-only form (ADR 0004):

   ```
   sources/<m>/<stem>.mp4   → raw/data/<m>/<stem>/raw.json
   sources/<m>/<stem>.html  → raw/data/<m>/<stem>/raw.json
   ```

   Uniqueness within a module is guaranteed by the zero-padded `NNN`
   prefix every file carries (see ADR 0004) — `000 Intro.mp4` and
   `000 Intro.html` colliding would be an authoring bug, not a path
   concern. Keeping a single slug rule means the pusher, the renderer,
   and the concept indexer never branch on extractor. See the
   2026-04-21 amendment below for why we reversed the original
   decision.

5. **Rename `kurpatov-transcriber` → `kurpatov-ingest`.** The service
   in `docker-compose.yml`, its container name, the watchdog script
   (`03_watch_and_transcribe.py` → `03_watch_and_ingest.py`), the
   batch/catch-up script (`02_transcribe_incremental.py` →
   `02_ingest_incremental.py`), the smoke check label, and the
   operator-facing docs all use "ingest" now. The word "transcribe"
   is reserved for the whisper-specific code path.

6. **GPU stays lazy for HTML.** The ingest worker only calls
   `_load_model()` when it pulls a whisper-typed job off the queue.
   HTML jobs run inline on the CPU worker thread — no GPU allocation,
   no idle-unload cycle, no waiting behind a warm whisper model. This
   falls out naturally from dispatch; we note it here so it's not
   accidentally regressed.

## Consequences

- **Cheap to grow a third extractor.** Adding PDF, DOCX, plain text
  later is a matter of extending the allow-list, writing
  `_extract_<kind>.py`, and adding one `elif` in the dispatcher. The
  downstream schema (segments[] + info.extractor) absorbs new kinds
  without forking the renderer.
- **Existing raw.json stays valid.** Older whisper outputs lacked
  `info.extractor` and `info.extracted_at`. Readers must treat both
  as optional when parsing historical data; the absence of
  `info.extractor` means whisper. New whisper writes carry both
  fields so a future sweep can normalise.
- **Rename cascade already paid.** The "videos → sources" rename
  (previous session) hit most of the same files; layering "ingest
  over transcriber" on top while the memory is fresh keeps the churn
  amortised. [ADR 0003](0003-watcher-reactive-not-cron.md),
  [ADR 0005](0005-split-transcribe-and-push.md), and
  [ADR 0007](0007-wiki-layer-mac-side.md) all carry 2026-04-20
  amendments pointing at this ADR.
- **Pusher is unaffected.** `04_watch_raw_and_push.py` already treats
  `raw/data/**/raw.json` as opaque content and mirrors it to GitHub
  verbatim; it does not care which extractor produced it.

## Rejected alternatives

- **Separate `html-extractor` container.** Clean single-responsibility,
  but the operational cost is real (second systemd-like lifecycle,
  second log stream, second image or second copy of the existing one)
  and the benefit is marginal — HTML extraction is tens of
  milliseconds per file, not a meaningful resource competitor for the
  GPU. Rejected in favour of dispatch-in-the-same-daemon.
- **Parallel `raw-html/` tree.** Would have kept schemas "obviously
  distinct", but every downstream consumer (pusher, Mac-side renderer,
  concept-index.json, per-source-summarize prompt) would need two
  code paths. Rejected in favour of unified segments[].
- **Drop timing fields from whisper to match html.** Symmetric, but
  destroys word-level timestamps that downstream concept authoring
  relies on. Rejected.
- **Keep the name "transcriber" and broaden its behaviour.** Minimal
  churn, maximal lie. Rejected — names that mislead are a recurring
  source of onboarding bugs.

## 2026-04-21 amendment — unify output slug

**Change.** Decision #4 originally specified that HTML sources keep
their `.html` suffix in the output slug
(`.../Intro.html/raw.json`) while media sources strip it
(`.../Intro/raw.json`). That asymmetry has been removed: every
extractor now writes to `<stem>/raw.json`.

**Reason.** The collision concern that motivated the original rule
was real in the abstract but doesn't occur in practice. Every source
in the curriculum is authored with a zero-padded `NNN` prefix
(`000 Intro.mp4`, `001 First lesson.html`, …) per ADR 0004. Two
files in the same module with the same `NNN` and the same title but
different extensions would already be an authoring mistake that the
module table would flag. The uniformity buys clearer code
downstream — neither the pusher (`04_watch_raw_and_push.py`) nor the
Mac-side renderer needs to care which extractor produced a
`raw.json`.

**Migration.** On 2026-04-21 the single existing `.html/` directory
in `vault/raw/data/` was renamed via `git mv` inside the pusher
container; the ingest daemon's boot-scan then treated the renamed
path as "done" and did not re-ingest. Code changes:
`notebooks/02_ingest_incremental.py` and
`notebooks/03_watch_and_ingest.py` — `out_slug_for()` now
unconditionally returns `rel.with_suffix("")`.


## 2026-04-21 amendment — PDF extractor added

The "cheap to grow" claim above now has a second datapoint. The PDF
extractor (image-only scans primary, typeset text layer secondary)
lives in `_extract_pdf.py`; dispatch, schema additions, and the
OCR-vs-text-layer decision are documented in
[ADR 0009](0009-pdf-extractor.md). `INGEST_EXTENSIONS` is now
`WHISPER_EXTENSIONS | HTML_EXTENSIONS | PDF_EXTENSIONS`;
`extractor_for()` returns one of `"whisper" | "html" | "pdf" | None`.

## Amendment — 2026-04-21: two-way startup scan (orphan reclaim)

The startup scan was originally one-way: walk `sources/`, enqueue
every file without a matching `raw.json`. This left a gap — if the
operator renamed or removed a source, the old `raw.json` was never
cleaned up and the wiki layer kept a dangling citation target.

The scan is now two-way:

1. **Forward (unchanged):** sources without a raw.json → enqueue for
   extraction.
2. **Reverse (new):** `data/<mirror>/<slug>/raw.json` whose matching
   source `sources/<mirror>/<slug>.<ext>` (for any `ext ∈
   INGEST_EXTENSIONS`) no longer exists → delete the whole slug dir.
   Ancestor mirror dirs are rmdir'd if they become empty.

This makes the rename case work automatically: the old slug loses its
source (reverse pass deletes the raw), the new slug appears
source-only (forward pass queues it). No operator action needed
between a rename and the next daemon boot — just restart the
container, or wait for the reverse pass if you bake it into a periodic
job (future).

Escape hatch: `--reclaim-dry-run` logs what would be deleted without
touching the tree. Useful on first rollout to verify the matcher
agrees with the operator's intent.

Safety notes:

* Only paths that contain a `raw.json` are considered. Top-level
  files like `data/CLAUDE.md` are never touched.
* Slug stems with periods (e.g. `Ст. 14 закона`) are matched via
  string concatenation (`str(slug) + ext`), not `Path.with_suffix`,
  so the period in the stem is preserved.
* The pusher (separate container, `kurpatov-wiki-raw-pusher`) picks up
  the removals on its next quiet-period sweep and commits them to
  GitHub exactly like any other change — no special coordination.

Second startup pass: stale `*.tmp` staging dirs. The extractors write
to `<slug>.tmp/raw.json` first and rename `<slug>.tmp → <slug>` only
on success (atomic-write pattern). If the process is killed between
those two steps (container restart, OOM, SIGKILL), the `.tmp` dir is
orphaned. The orphan-raw pass above misses it because there's no
`raw.json` inside. Reclaim therefore does a second rglob over
`*.tmp` directories and deletes any whose slug has no matching
source. The edge case of a source whose basename legitimately ends
in `.tmp` (e.g. `sources/foo.tmp.mp4`) is preserved: the matcher
finds `sources/foo.tmp.<ext>` for the `.tmp`-suffixed slug and keeps
it. Smoke-tested locally with 5 mixed cases — completed raws with
and without period-in-stem, orphan raw + its own stale staging,
stale staging for a still-live slug, and the legitimate-`.tmp`
source case.


## 2026-04-21 amendment — strict slug-order processing

All ingest processing — both the daemon (`03_watch_and_ingest.py`) and
the batch script (`02_ingest_incremental.py`) — now processes sources
in strict lexicographic slug order, regardless of extractor type.

**Why it matters.** Sources are named with a zero-padded `NNN_` prefix
(ADR 0004). Lecture 001 may cite lecture 000; a PDF companion for
lecture 002 may cite both. If ingest processes PDFs before audio (or
vice versa), or worse, processes `002/000` before `000/000` because a
whisper file happens to be in flight when the second arrives, the
downstream rendering/summarisation step sees references to raws that
don't exist yet. The pipeline tolerates this (it'll catch up on the
next pass) but the intermediate Wiki state is broken and confusing.

**Daemon (03).** `queue.Queue` replaced with
`queue.PriorityQueue[tuple[slug_str, seq, path]]`. Workers pull the
smallest pending slug, so a newly-dropped `000/003.mp4` jumps ahead of
`005/000.mp4` already enqueued. `seq` is a monotonic tie-breaker so
`Path` objects with identical slugs (different extensions) still have
a deterministic pop order.

**Batch (02).** The previous three-phase loop (all HTML → all PDF →
all Whisper) is replaced by a single unified loop over `sorted(
pending, key=lambda p: str(out_slug_for(p, sources_root)))`. Whisper
model is still lazy-loaded on the first whisper item encountered;
audio duration probing and the outer progress bar are unchanged (they
still only fire when whisper work is present). Atomic `<slug>.tmp →
<slug>` rename applies to all three extractor types, so the reclaim
pass above handles partial work from any of them uniformly.

Tested: dropped `000/003` while `005/*` was in flight, daemon log
shows `000/003` processed next. Batch script run on a mixed pending
set produces output timestamps in slug order (not grouped by type).


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
