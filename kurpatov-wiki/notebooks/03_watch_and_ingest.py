"""
Ingest daemon for the Kurpatov-wiki vault.

Watches /workspace/sources recursively for new source files and ingests
them into /workspace/vault/raw/data/<mirror>/<slug>/raw.json. Three
extractors run behind one scheduler, dispatched by file suffix:

  * WHISPER_EXTENSIONS — audio / video the faster-whisper model can
    decode via ffmpeg. Writes segments[] with word-level timestamps.
  * HTML_EXTENSIONS — getcourse.ru-style lesson-page exports. The
    extractor (`_extract_html.py`) harvests only lecturer prose and
    writes the same segments[] shape with no timing fields.
  * PDF_EXTENSIONS — PDF exports of lesson materials. The extractor
    (`_extract_pdf.py`) tries the embedded text layer first and falls
    back to Qwen2.5-VL-7B-Instruct OCR (GPU) on image-only PDFs.

See [ADR 0008](../docs/adr/0008-ingest-dispatch.md) for why the daemon
handles both and why it was renamed from "transcriber" to "ingest".
The output schema is documented at the top of 02_ingest_incremental.py
and formalised in ADR 0002.

The `data/` prefix separates content from future repo-root meta files
(CLAUDE.md, README.md, etc.) in kurpatov-wiki-raw; see ADR 0005's
data/content-split amendment.

Design notes:
  - inotify via watchdog (reactive; not cron polling).
  - Files are only enqueued once they "stabilize": size and mtime unchanged
    for --stable-sec seconds. Protects against WRITE-in-progress for scp,
    rsync.tmp→mv, and similar patterns.
  - Whisper is lazy-loaded: brought to VRAM only when a whisper job runs,
    and evicted after --idle-unload-sec seconds of idleness. HTML jobs
    never touch the GPU — they skip the load entirely. PDF jobs may
    touch the GPU (Qwen2.5-VL-7B) if a page has no text layer; the VLM
    is also lazy-loaded (cached inside `_extract_pdf`).
  - Initial scan at startup is two-way: (a) enqueue every source file
    that doesn't yet have a raw.json ("catch-up" for anything dropped
    in while the daemon was down), and (b) delete raw dirs whose source
    file no longer exists ("reclaim" for anything renamed or removed
    while the daemon was down). The reclaim side can be run in
    dry-run mode with --reclaim-dry-run.
  - Atomic writes: result goes into <slug>.tmp/raw.json, then
    <slug>.tmp → <slug> rename.
  - Graceful shutdown on SIGTERM/SIGINT: current file finishes, then exit.

Run inside the kurpatov-ingest container (service in docker-compose):
  python -u /workspace/notebooks/03_watch_and_ingest.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import json
import logging
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from faster_whisper import WhisperModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# local helpers — non-media extractors
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _extract_html  # noqa: E402
import _extract_pdf   # noqa: E402


log = logging.getLogger("ingest")


# ---------------------------------------------------------------------------
# Supported source extensions — kept in sync with 02_ingest_incremental.py.
#
# We allow-list suffixes (rather than glob) because `sources/` may also
# contain assorted non-ingestable artefacts (README, scratch PDFs, etc.)
# that must be ignored.
# ---------------------------------------------------------------------------

WHISPER_EXTENSIONS: frozenset[str] = frozenset({
    # Video
    ".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi",
    # Audio
    ".mp3", ".m4a", ".wav", ".ogg", ".flac", ".opus", ".aac",
})

HTML_EXTENSIONS: frozenset[str] = frozenset({".html", ".htm"})

PDF_EXTENSIONS: frozenset[str] = frozenset({".pdf"})

INGEST_EXTENSIONS: frozenset[str] = (
    WHISPER_EXTENSIONS | HTML_EXTENSIONS | PDF_EXTENSIONS
)


def extractor_for(path: Path) -> str | None:
    """Return "whisper" | "html" | "pdf" | None for the given source path."""
    suffix = path.suffix.lower()
    if suffix in WHISPER_EXTENSIONS:
        return "whisper"
    if suffix in HTML_EXTENSIONS:
        return "html"
    if suffix in PDF_EXTENSIONS:
        return "pdf"
    return None


def is_ingestable(path: Path) -> bool:
    return extractor_for(path) is not None


# ---------------------------------------------------------------------------
# helpers (same semantics as 02_ingest_incremental.py)
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(path),
        ]
    )
    return float(out.strip())


def clean_tmp_dir(tmp_dir: Path) -> None:
    if not tmp_dir.exists():
        return
    for p in tmp_dir.rglob("*"):
        if p.is_file():
            p.unlink()
    for p in sorted(tmp_dir.rglob("*"), reverse=True):
        if p.is_dir():
            p.rmdir()
    tmp_dir.rmdir()


def out_slug_for(source: Path, sources_root: Path) -> Path:
    """
    Output slug (relative to --out root) for a given source.

    Always strip the extension, regardless of extractor. Stem uniqueness
    within a module is guaranteed by the zero-padded ``NNN`` prefix that
    every source carries (see ADR 0004); two sources with the same stem
    but different extensions would be a data-entry bug.

    Examples:
        sources/a/000 foo.mp4  → a/000 foo
        sources/a/001 bar.html → a/001 bar
        sources/a/002 baz.pdf  → a/002 baz
    """
    rel = source.relative_to(sources_root)
    return rel.with_suffix("")


def out_dir_for(source: Path, out_root: Path, sources_root: Path) -> Path:
    """vault/raw/data/ mirror — see out_slug_for for the naming rule."""
    return out_root / out_slug_for(source, sources_root)


def reclaim_orphan_outputs(
    sources_root: Path,
    out_root: Path,
    dry_run: bool = False,
) -> int:
    """
    Delete <out_root>/<mirror>/<slug>/ directories whose matching source
    file no longer exists under <sources_root>/<mirror>/<slug>.<ext>.

    This is the mirror of ``_initial_scan`` (which finds sources with no
    raw.json and queues them for extraction). Together they keep the
    raw tree in sync with sources — the rename case works
    automatically: the old slug loses its source (we delete its raw),
    the new slug appears without a raw (the forward scan queues it).

    Top-level files under out_root (CLAUDE.md, README.md) are ignored:
    we only ever look at directories that contain a ``raw.json``.

    Second pass: stale ``*.tmp`` staging dirs from the atomic-write
    pattern (``<slug>.tmp/raw.json`` → ``<slug>/``). At startup no
    extraction is mid-flight, so any surviving ``*.tmp`` dir is
    garbage — unless the source itself legitimately has ``.tmp`` in
    its basename, in which case we keep it.

    After removing a slug dir we also rmdir any newly-empty ancestor
    mirror dirs up to (but not including) out_root itself, so the raw
    tree doesn't accumulate empty bookkeeping directories.

    Returns the number of paths reclaimed (orphan raws + stale .tmp
    dirs). Equals what would be reclaimed when dry_run=True.
    """
    if not out_root.exists():
        return 0

    orphans: list[Path] = []
    for raw in out_root.rglob("raw.json"):
        slug_dir = raw.parent
        slug_rel = slug_dir.relative_to(out_root)
        # Slug = stem-without-extension (see out_slug_for). A matching
        # source file is anything whose stem equals slug_rel and whose
        # extension is in INGEST_EXTENSIONS. We use string concat
        # (not ``with_suffix``) because filenames may legitimately
        # contain periods in their stem.
        has_source = any(
            (sources_root / (str(slug_rel) + ext)).exists()
            for ext in INGEST_EXTENSIONS
        )
        if not has_source:
            orphans.append(slug_dir)

    for slug_dir in orphans:
        slug_rel = slug_dir.relative_to(out_root)
        verb = "would remove" if dry_run else "removing"
        log.info("[reclaim] %s orphan %s", verb, slug_rel)
        if dry_run:
            continue
        shutil.rmtree(slug_dir)
        # Rmdir newly-empty ancestor dirs, stopping at out_root.
        parent = slug_dir.parent
        while parent != out_root and parent.exists():
            try:
                next(parent.iterdir())
            except StopIteration:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
            else:
                break

    # Second pass: stale ``.tmp`` staging leftovers.
    stale_tmp: list[Path] = []
    for tmp_dir in out_root.rglob("*.tmp"):
        if not tmp_dir.is_dir():
            continue
        slug_rel = tmp_dir.relative_to(out_root)
        # Does a source legitimately have this ``.tmp``-suffixed slug?
        # (E.g. ``sources/foo.tmp.mp4`` → slug ``foo.tmp`` → raw
        # ``foo.tmp/``.) If so, keep it.
        has_source = any(
            (sources_root / (str(slug_rel) + ext)).exists()
            for ext in INGEST_EXTENSIONS
        )
        if has_source:
            continue
        stale_tmp.append(tmp_dir)

    for tmp_dir in stale_tmp:
        slug_rel = tmp_dir.relative_to(out_root)
        verb = "would remove" if dry_run else "removing"
        log.info("[reclaim] %s stale .tmp %s", verb, slug_rel)
        if dry_run:
            continue
        shutil.rmtree(tmp_dir)
        parent = tmp_dir.parent
        while parent != out_root and parent.exists():
            try:
                next(parent.iterdir())
            except StopIteration:
                try:
                    parent.rmdir()
                except OSError:
                    break
                parent = parent.parent
            else:
                break

    return len(orphans) + len(stale_tmp)


# ---------------------------------------------------------------------------
# HTML ingest (cheap, no GPU)
# ---------------------------------------------------------------------------

def ingest_html_one(
    source: Path,
    out_root: Path,
    sources_root: Path,
    *,
    language: str,
) -> None:
    stem = source.stem
    out_dir = out_dir_for(source, out_root, sources_root)
    tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"

    if (out_dir / "raw.json").exists():
        log.info("[skip ] %s already has raw.json", stem)
        return

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    clean_tmp_dir(tmp_dir)
    tmp_dir.mkdir(parents=True)

    t0 = time.time()
    payload = _extract_html.build_raw_payload(source, language=language)
    (tmp_dir / "raw.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_dir.rename(out_dir)
    wall = time.time() - t0

    log.info(
        "[html ] %s — %d paragraphs, title=%r, wall %.2fs",
        stem, payload["info"]["paragraph_count"], payload["info"]["title"], wall,
    )


# ---------------------------------------------------------------------------
# PDF ingest (no GPU; may do OCR)
# ---------------------------------------------------------------------------

def ingest_pdf_one(
    source: Path,
    out_root: Path,
    sources_root: Path,
    *,
    language: str,
) -> None:
    stem = source.stem
    out_dir = out_dir_for(source, out_root, sources_root)
    tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"

    if (out_dir / "raw.json").exists():
        log.info("[skip ] %s already has raw.json", stem)
        return

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    clean_tmp_dir(tmp_dir)
    tmp_dir.mkdir(parents=True)

    t0 = time.time()
    payload = _extract_pdf.build_raw_payload(source, language=language)
    (tmp_dir / "raw.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_dir.rename(out_dir)
    wall = time.time() - t0

    info = payload["info"]
    log.info(
        "[pdf  ] %s — %d paragraphs, %d pages, source=%s, wall %.2fs",
        stem, info["paragraph_count"], info["page_count"],
        info["pdf_text_source"], wall,
    )


# ---------------------------------------------------------------------------
# Whisper ingest (GPU-bound)
# ---------------------------------------------------------------------------

def ingest_whisper_one(
    model: WhisperModel,
    source: Path,
    out_root: Path,
    sources_root: Path,
    *,
    language: str,
    beam: int,
    model_name: str,
    compute: str,
) -> None:
    stem = source.stem
    out_dir = out_dir_for(source, out_root, sources_root)
    tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"

    if (out_dir / "raw.json").exists():
        log.info("[skip ] %s already has raw.json", stem)
        return

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    clean_tmp_dir(tmp_dir)
    tmp_dir.mkdir(parents=True)

    try:
        duration = probe_duration(source)
    except Exception:
        duration = 0.0
    log.info("[whisp] %s (%.0fs audio)", source.name, duration)

    t0 = time.time()
    segments, info = model.transcribe(
        str(source),
        language=language,
        beam_size=beam,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        word_timestamps=True,
    )

    raw_segments = []
    for i, seg in enumerate(segments, 1):
        raw_segments.append({
            "id": i,
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "speaker": None,
            "words": [
                {"start": w.start, "end": w.end,
                 "word": w.word, "prob": w.probability}
                for w in (seg.words or [])
            ],
        })

    now = utc_now_iso()
    payload = {
        "info": {
            "language": info.language,
            "duration": info.duration,
            "language_probability": info.language_probability,
            "source_path": str(source),
            "extractor": "whisper",
            "model": model_name,
            "compute_type": compute,
            "beam_size": beam,
            "extracted_at": now,
            "transcribed_at": now,   # backward-compat alias
            "diarized": False,
        },
        "segments": raw_segments,
    }
    (tmp_dir / "raw.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    tmp_dir.rename(out_dir)

    wall = time.time() - t0
    rtf = wall / max(info.duration, 1e-6)
    log.info(
        "[done ] %s — %d segs, audio %.0fs, wall %.0fs, RTF %.3f",
        stem, len(raw_segments), info.duration, wall, rtf,
    )


# ---------------------------------------------------------------------------
# stability tracker
# ---------------------------------------------------------------------------

class StabilityTracker:
    """Promotes a file to the work queue only after its size+mtime have been
    unchanged for `stable_sec`."""

    def __init__(
        self,
        out_root: Path,
        sources_root: Path,
        stable_sec: float,
        enqueue: Callable[[Path], None],
    ):
        self.out_root = out_root
        self.sources_root = sources_root
        self.stable_sec = stable_sec
        self.enqueue = enqueue
        self._lock = threading.Lock()
        # path -> (size, mtime, last_change_ts)
        self._pending: dict[Path, tuple[int, float, float]] = {}

    def _raw_json_for(self, path: Path) -> Path:
        try:
            slug = out_slug_for(path, self.sources_root)
        except ValueError:
            # path is outside sources_root — not our file
            return self.out_root / "__outside__" / "raw.json"
        return self.out_root / slug / "raw.json"

    def touch(self, path: Path) -> None:
        if not is_ingestable(path):
            return
        if self._raw_json_for(path).exists():
            return
        try:
            st = path.stat()
        except FileNotFoundError:
            return
        if not st.st_size:
            # empty file — skip
            return
        now = time.time()
        with self._lock:
            prev = self._pending.get(path)
            if prev is None:
                self._pending[path] = (st.st_size, st.st_mtime, now)
                log.info("[watch] tracking %s (size=%d)", path.name, st.st_size)
            elif (st.st_size, st.st_mtime) != (prev[0], prev[1]):
                self._pending[path] = (st.st_size, st.st_mtime, now)

    def tick(self) -> None:
        now = time.time()
        promote: list[Path] = []
        with self._lock:
            for path, (size, mtime, last_change) in list(self._pending.items()):
                try:
                    st = path.stat()
                except FileNotFoundError:
                    self._pending.pop(path, None)
                    continue
                if (st.st_size, st.st_mtime) != (size, mtime):
                    self._pending[path] = (st.st_size, st.st_mtime, now)
                    continue
                if now - last_change >= self.stable_sec:
                    promote.append(path)
                    self._pending.pop(path, None)

        for p in promote:
            if not self._raw_json_for(p).exists():
                log.info("[stable] %s stable for %.0fs", p.name, self.stable_sec)
                self.enqueue(p)


class WatcherHandler(FileSystemEventHandler):
    def __init__(self, tracker: StabilityTracker):
        self.tracker = tracker

    def on_any_event(self, event) -> None:
        if event.is_directory:
            return
        self.tracker.touch(Path(event.src_path))
        dest = getattr(event, "dest_path", None)
        if dest:
            self.tracker.touch(Path(dest))


# ---------------------------------------------------------------------------
# daemon
# ---------------------------------------------------------------------------

class Daemon:
    def __init__(self, args):
        self.args = args
        self.sources_root = Path(args.sources)
        self.out_root = Path(args.out)
        self.out_root.mkdir(parents=True, exist_ok=True)
        self.reclaim_dry_run: bool = bool(args.reclaim_dry_run)

        self.queue: queue.Queue[Path] = queue.Queue()
        self._in_flight: set[Path] = set()
        self._lock = threading.Lock()

        self.model: Optional[WhisperModel] = None
        self.model_last_used = 0.0

        self.shutdown = threading.Event()
        self.tracker = StabilityTracker(
            self.out_root,
            self.sources_root,
            args.stable_sec,
            self._enqueue,
        )

    # -- queue --

    def _enqueue(self, path: Path) -> None:
        with self._lock:
            if path in self._in_flight:
                return
            self._in_flight.add(path)
        self.queue.put(path)
        log.info(
            "[queue] + %s [%s] (qsize=%d)",
            path.name, extractor_for(path), self.queue.qsize(),
        )

    # -- model lifecycle --

    def _load_model(self) -> None:
        if self.model is not None:
            return
        log.info("[load ] %s cuda %s", self.args.model, self.args.compute)
        t0 = time.time()
        self.model = WhisperModel(
            self.args.model,
            device="cuda",
            compute_type=self.args.compute,
            download_root="/workspace/models",
        )
        log.info("[load ] done in %.1fs", time.time() - t0)

    def _unload_model(self) -> None:
        if self.model is None:
            return
        log.info("[unload] releasing model and VRAM")
        self.model = None
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        except Exception:
            pass
        log.info("[unload] done")

    # -- threads --

    def _stability_loop(self) -> None:
        while not self.shutdown.is_set():
            try:
                self.tracker.tick()
            except Exception:
                log.exception("[stab ] tick failed")
            self.shutdown.wait(1.0)

    def _worker(self) -> None:
        while not self.shutdown.is_set():
            try:
                path = self.queue.get(timeout=0.5)
            except queue.Empty:
                if (
                    self.model is not None
                    and (time.time() - self.model_last_used)
                        > self.args.idle_unload_sec
                ):
                    self._unload_model()
                continue

            kind = extractor_for(path)
            try:
                if kind == "html":
                    # HTML never touches the GPU — run directly.
                    ingest_html_one(
                        path,
                        self.out_root,
                        self.sources_root,
                        language=self.args.language,
                    )
                elif kind == "pdf":
                    # PDF usually skips the GPU (text-layer fast path); may fall back to Qwen2.5-VL.
                    ingest_pdf_one(
                        path,
                        self.out_root,
                        self.sources_root,
                        language=self.args.language,
                    )
                elif kind == "whisper":
                    self._load_model()
                    self.model_last_used = time.time()
                    ingest_whisper_one(
                        self.model,
                        path,
                        self.out_root,
                        self.sources_root,
                        language=self.args.language,
                        beam=self.args.beam,
                        model_name=self.args.model,
                        compute=self.args.compute,
                    )
                    self.model_last_used = time.time()
                else:
                    log.warning("[skip ] %s is not ingestable", path.name)
            except Exception:
                log.exception("[fail ] while processing %s", path)
            finally:
                with self._lock:
                    self._in_flight.discard(path)
                self.queue.task_done()

    # -- initial scan --

    def _initial_scan(self) -> None:
        all_sources = sorted(
            p for p in self.sources_root.rglob("*")
            if p.is_file() and is_ingestable(p)
        )
        pending = [
            p for p in all_sources
            if not (out_dir_for(p, self.out_root, self.sources_root)
                    / "raw.json").exists()
        ]
        whisper_n = sum(1 for p in pending if extractor_for(p) == "whisper")
        html_n = sum(1 for p in pending if extractor_for(p) == "html")
        pdf_n = sum(1 for p in pending if extractor_for(p) == "pdf")
        log.info(
            "[scan ] found=%d  done=%d  pending=%d "
            "(whisper=%d, html=%d, pdf=%d)",
            len(all_sources), len(all_sources) - len(pending),
            len(pending), whisper_n, html_n, pdf_n,
        )
        for p in pending:
            self.tracker.touch(p)

    # -- run --

    def run(self) -> None:
        def _sig(signum, _frame):
            log.info("[shutdown] got signal %d", signum)
            self.shutdown.set()

        for s in (signal.SIGINT, signal.SIGTERM):
            signal.signal(s, _sig)

        observer = Observer()
        observer.schedule(
            WatcherHandler(self.tracker),
            str(self.sources_root),
            recursive=True,
        )
        observer.start()
        log.info("[watch] inotify on %s (recursive)", self.sources_root)

        worker_t = threading.Thread(
            target=self._worker, name="worker", daemon=True,
        )
        worker_t.start()
        stab_t = threading.Thread(
            target=self._stability_loop, name="stability", daemon=True,
        )
        stab_t.start()

        n_reclaimed = reclaim_orphan_outputs(
            self.sources_root, self.out_root,
            dry_run=self.reclaim_dry_run,
        )
        if n_reclaimed:
            log.info("[reclaim] done — %d orphan raw dir(s) %s",
                     n_reclaimed,
                     "dry-run (kept)" if self.reclaim_dry_run else "removed")
        self._initial_scan()

        try:
            while not self.shutdown.is_set():
                time.sleep(1.0)
        finally:
            log.info("[shutdown] stopping observer")
            observer.stop()
            observer.join(timeout=5)

            log.info("[shutdown] waiting for worker to drain current file")
            self.shutdown.set()
            worker_t.join(timeout=3600)
            self._unload_model()
            log.info("[shutdown] bye")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--sources",
        default="/workspace/sources",
        help=(
            "Root directory holding source files (media, HTML, PDF). "
            "Watched recursively. Any suffix in INGEST_EXTENSIONS is "
            "picked up."
        ),
    )
    ap.add_argument(
        "--out",
        default="/workspace/vault/raw/data",
        help=(
            "Root under which raw.json files are written. Defaults to "
            "/workspace/vault/raw/data so that the kurpatov-wiki-raw "
            "repo's top-level `data/` holds content and its root stays "
            "free for meta files. See ADR 0005's data/content-split "
            "amendment."
        ),
    )
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--compute", default="float16",
                    choices=["float16", "bfloat16", "int8_float16"])
    ap.add_argument("--beam", type=int, default=5)
    ap.add_argument("--language", default="ru")
    ap.add_argument("--stable-sec", type=float, default=10.0,
                    help="How long size/mtime must be unchanged before we enqueue.")
    ap.add_argument("--idle-unload-sec", type=float, default=120.0,
                    help="Unload model from VRAM after this many seconds idle.")
    ap.add_argument("--reclaim-dry-run", action="store_true",
                    help="Log orphan raw dirs on startup scan, but do not delete them.")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    Daemon(args).run()


if __name__ == "__main__":
    main()
