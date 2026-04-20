"""
Transcription daemon for the Kurpatov-wiki vault.

Watches /workspace/sources recursively for new media files (video or audio)
and transcribes them into /workspace/vault/raw/data/<course>/<module>/
<stem>/raw.json, matching the schema of 02_transcribe_incremental.py.
The `data/` prefix separates content from future repo-root meta files
(CLAUDE.md, README.md, etc.) in the kurpatov-wiki-raw repo; see ADR
0005's data/content-split amendment.

Supported inputs are any audio/video format faster-whisper (via ffmpeg)
can decode — see MEDIA_EXTENSIONS below. The directory name used to be
"videos/" but was generalized to "sources/" once audio-only lectures
and other source materials entered scope.

Design notes:
  - inotify via watchdog (reactive; not cron polling).
  - Files are only enqueued once they "stabilize": size and mtime unchanged
    for --stable-sec seconds. Protects against WRITE-in-progress for scp,
    rsync.tmp→mv, and similar patterns.
  - The Whisper model is lazy-loaded: brought to VRAM only when the queue has
    work, and evicted after --idle-unload-sec seconds of idleness. Between
    back-to-back files the model stays warm to avoid thrashing.
  - Initial scan at startup enqueues every media file without a matching
    raw.json, so the daemon also acts as a "catch-up" for anything dropped
    in while it was down.
  - Atomic writes: result goes into <stem>.tmp/raw.json, then
    <stem>.tmp → <stem> rename.
  - Graceful shutdown on SIGTERM/SIGINT: current file finishes, then exit.

Run inside the kurpatov-transcriber container (service in docker-compose):
  python -u /workspace/notebooks/03_watch_and_transcribe.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import json
import logging
import queue
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from faster_whisper import WhisperModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


log = logging.getLogger("watcher")


# ---------------------------------------------------------------------------
# Supported media file extensions.
#
# faster-whisper decodes via ffmpeg, so anything ffmpeg can read is fair
# game. We intentionally allow-list formats rather than rely on a single
# glob: a "sources" directory may also contain non-media artefacts
# (README files, transcripts, supporting PDFs) that must be ignored.
# ---------------------------------------------------------------------------

MEDIA_EXTENSIONS: frozenset[str] = frozenset({
    # Video
    ".mp4", ".mkv", ".webm", ".mov", ".m4v", ".avi",
    # Audio
    ".mp3", ".m4a", ".wav", ".ogg", ".flac", ".opus", ".aac",
})


def is_media(path: Path) -> bool:
    """True if the suffix is one we'll feed to Whisper."""
    return path.suffix.lower() in MEDIA_EXTENSIONS


# ---------------------------------------------------------------------------
# helpers (same semantics as 02_transcribe_incremental.py)
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


def out_dir_for(source: Path, out_root: Path, sources_root: Path) -> Path:
    """vault/raw/data/ mirrors the full sources/<...>/<name>.<ext>
    → <...>/<name>/raw.json.

    `out_root` is expected to be `/workspace/vault/raw/data/` (see --out
    default below); the `data/` segment is what separates transcript
    content from the repo's meta root in kurpatov-wiki-raw.
    """
    return out_root / source.relative_to(sources_root).with_suffix("")


def transcribe_one(
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
    log.info("[trans] %s (%.0fs audio)", source.name, duration)

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

    payload = {
        "info": {
            "language": info.language,
            "duration": info.duration,
            "language_probability": info.language_probability,
            "source_path": str(source),
            "model": model_name,
            "compute_type": compute,
            "beam_size": beam,
            "transcribed_at": utc_now_iso(),
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
            rel = path.relative_to(self.sources_root).with_suffix("")
        except ValueError:
            # path is outside sources_root — not our file
            return self.out_root / "__outside__" / "raw.json"
        return self.out_root / rel / "raw.json"

    def touch(self, path: Path) -> None:
        if not is_media(path):
            return
        if self._raw_json_for(path).exists():
            return
        try:
            st = path.stat()
        except FileNotFoundError:
            return
        if not st.st_size:
            # empty file — skip; ffmpeg won't like it
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
        log.info("[queue] + %s (qsize=%d)", path.name, self.queue.qsize())

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

            try:
                self._load_model()
                self.model_last_used = time.time()
                transcribe_one(
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
            except Exception:
                log.exception("[fail ] while processing %s", path)
            finally:
                with self._lock:
                    self._in_flight.discard(path)
                self.queue.task_done()

    # -- initial scan --

    def _initial_scan(self) -> None:
        all_media = sorted(
            p for p in self.sources_root.rglob("*")
            if p.is_file() and is_media(p)
        )
        pending = [
            p for p in all_media
            if not (out_dir_for(p, self.out_root, self.sources_root)
                    / "raw.json").exists()
        ]
        log.info(
            "[scan ] found=%d  done=%d  pending=%d",
            len(all_media), len(all_media) - len(pending), len(pending),
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
            "Root directory holding source media (video/audio). Watched "
            "recursively. Was historically named --videos; renamed when "
            "audio-only lectures and other source materials entered scope."
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
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    Daemon(args).run()


if __name__ == "__main__":
    main()
