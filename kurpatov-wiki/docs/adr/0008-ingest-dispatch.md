# 0008 — Ingest dispatch: whisper + HTML extractor behind one daemon

Status: Accepted (2026-04-20)

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

4. **Output path keeps HTML's `.html` suffix to avoid collisions.**
   Media continues to use the historical stem-only form (ADR 0004):

   ```
   sources/<m>/<stem>.mp4   → raw/data/<m>/<stem>/raw.json
   sources/<m>/<stem>.html  → raw/data/<m>/<stem>.html/raw.json
   ```

   This way a media file and an HTML page that happen to share a stem
   (common, because getcourse.ru and YouTube often name lessons
   identically) never overwrite each other.

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
