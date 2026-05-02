# ADR 0003 — reactive watcher (not cron), lazy-load model

## Status
Accepted (2026-04-19).

## Amended (2026-04-20 — dispatched ingest, not just transcription)

Since this ADR was written the watcher has grown a second extractor
for HTML sources (getcourse.ru lesson-page exports) alongside
faster-whisper. The container was renamed `kurpatov-transcriber` →
`kurpatov-ingest`, the scripts renamed `02_transcribe_incremental.py`
→ `02_ingest_incremental.py` and `03_watch_and_transcribe.py` →
`03_watch_and_ingest.py`, and dispatch is now by file suffix:
media → whisper (GPU, same lazy-load behaviour as below),
`.html` / `.htm` → `_extract_html.py` (CPU, never loads the model).
The reactive-watcher design below applies unchanged to both paths.
See [ADR 0008](0008-ingest-dispatch.md) for the full dispatch
rationale.

## Context
I drop new mp4s unevenly — one or two at a time, batches once a day.
Transcribing one lecture takes a couple of minutes on an RTX 5090. What I
want:

- Automation: I drop a file, I see `raw.json` minutes later, no manual
  runs.
- Don't keep the model in VRAM 24/7 if nobody is using it — I
  simultaneously experiment on this same GPU in jupyter.

Options:

1. cron every N minutes runs `02_transcribe_incremental.py`.
2. systemd-timer + batch script.
3. Daemon + inotify (watchdog), model loaded on demand, unloaded after
   idle.
4. Manual run from inside jupyter.

## Decision
Option 3. A dedicated service `kurpatov-transcriber` in compose, running
`03_watch_and_transcribe.py`. Inside:

(Later renamed to `kurpatov-ingest` / `03_watch_and_ingest.py` when
HTML extraction joined; see the 2026-04-20 amendment above and
[ADR 0008](0008-ingest-dispatch.md).)

- `watchdog.observers.Observer` on `/workspace/sources/`, recursive.
- `StabilityTracker` waits until an mp4 file's size+mtime stop changing
  for `--stable-sec` seconds (default 10), then pushes it into the
  processing queue.
- A worker thread lazy-loads the model on the first task and unloads it
  after `--idle-unload-sec` seconds (default 120) of idle. Unload is
  `del model; gc.collect(); torch.cuda.empty_cache()`; ~500 MB of CUDA
  context stays reserved, but the main model (~4 GB) is released.

## Consequences
- Plus: "drop an mp4 — get a json", no involvement from me.
- Plus: while idle, jupyter sees free VRAM and can run heavy experiments.
- Plus: reactive → no race with a cron job processing the same file.
- Minus: ~500 MB of CUDA context remains reserved (inevitable CUDA + cudnn
  + driver overhead). Fine on a 32 GB RTX 5090.
- Minus: more complex than cron. Needs watchdog, needs care about
  races on in-flight uploads.
- Minus: runs 24/7 — have to keep an eye on fd leaks.

## Invariants
- Container restart resets in-memory state → if at restart some mp4 was
  "stable but not yet taken", the next start still picks it up (it scans
  `sources/` and diffs against `vault/raw/`). Same behavior as
  `02_transcribe_incremental.py`.
- No double-processing: the `raw.json` existence check is the first guard;
  the `.tmp` directory makes the write atomic.
- The transcriber does not invoke `git`. Mirroring `raw/` to GitHub is a
  separate container's responsibility (`kurpatov-wiki-raw-pusher`, see
  [ADR 0005](0005-split-transcribe-and-push.md)). A failed push must
  never stall a transcription and vice versa.

## Alternatives considered
- **cron**: no "immediacy", and if a source file lands seconds after the tick
  we wait a full cycle. Plus cron can start on a file that's still being
  written.
- **Model always loaded**: ~4 GB of VRAM unavailable for parallel
  experiments.
- **Load model on event, never unload**: model lives forever after the
  first file, for as long as the container runs. Unacceptable for my
  shared-GPU with jupyter setup.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain inherited from the lab's AGENTS.md.
