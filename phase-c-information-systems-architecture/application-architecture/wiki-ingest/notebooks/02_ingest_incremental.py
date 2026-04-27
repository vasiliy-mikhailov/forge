"""
Incremental ingest for the Kurpatov-wiki vault.

Recursively scans /workspace/sources/, compares against the list of
existing raw.json files under /workspace/vault/raw/data/<mirror>/<slug>/
raw.json, and processes only the missing ones.

Three extractors live behind a shared scheduler:

  * WHISPER_EXTENSIONS — audio / video the faster-whisper model can
    decode via ffmpeg. Produces segments[] with word-level timestamps.

  * HTML_EXTENSIONS — getcourse.ru-style lesson-page exports. The
    extractor lives in `_extract_html.py`; it harvests only the lecturer
    prose (`<div class="text-normal f-text">` blocks) and emits the
    same segments[] shape with no timing fields.

  * PDF_EXTENSIONS — PDF exports of lesson materials. The extractor
    lives in `_extract_pdf.py`. Tries the embedded text layer first
    (via pypdf); for image-only PDFs (e.g. macOS "Print to PDF" scans)
    falls back to tesseract OCR (lang=rus+eng, 300 DPI, page-by-page
    rasterization). Emits the same segments[] shape; each segment
    carries a .page anchor.

All extractors emit the same raw.json schema so downstream (the
kurpatov-wiki-raw pusher and the Mac-side wiki-renderer) doesn't need
to care which extractor ran:

  info.language               — "ru" (or whisper-detected)
  info.source_path            — absolute path to the source file
  info.extractor              — "whisper" | "html" | "pdf"
  info.extracted_at           — ISO-8601 UTC
  info.title                  — lesson title (html/pdf only; absent on whisper)
  info.transcribed_at         — alias of extracted_at (whisper only;
                                kept for backward compat with older tools
                                that predate the rename)
  info.duration / .language_probability / .model / .compute_type /
  info.beam_size / .diarized  — whisper only
  info.page_count / .paragraph_count  — pdf only
  info.pdf_text_source        — pdf only: "text_layer" | "qwen2.5-vl"
  info.ocr_model / .ocr_dpi   — pdf only, present when pdf_text_source != text_layer
  segments[].id               — sequential, 1-based
  segments[].text             — recognized / extracted text
  segments[].start / .end     — seconds (whisper only)
  segments[].speaker          — null placeholder (whisper only)
  segments[].words[]          — word-level timestamps (whisper only)
  segments[].page             — 1-based page number (pdf only)

Output layout — per-source directory under `vault/raw/data/`:

  sources/<mirror>/<stem>.mp4   → vault/raw/data/<mirror>/<stem>/raw.json
  sources/<mirror>/<stem>.html  → vault/raw/data/<mirror>/<stem>/raw.json
  sources/<mirror>/<stem>.pdf   → vault/raw/data/<mirror>/<stem>/raw.json

All extractors drop the extension and use the bare stem — the
zero-padded ``NNN`` prefix every source carries already guarantees
uniqueness within a module (ADR 0004, amended by ADR 0008).

Atomicity: the result is first written to <slug>.tmp/raw.json, then
<slug>.tmp → <slug> via rename. An interrupted run leaves no corrupt
artifacts; the next pass will regenerate them.

Run inside the jupyter-kurpatov-wiki container:
  docker exec -t jupyter-kurpatov-wiki python -u /workspace/notebooks/02_ingest_incremental.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel
from tqdm import tqdm

# local helpers — non-media extractors
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _extract_html  # noqa: E402
import _extract_pdf   # noqa: E402


# ---------------------------------------------------------------------------
# ingest dispatch — kept in sync with 03_watch_and_ingest.py
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


def out_slug_for(source: Path, sources_root: Path) -> Path:
    """
    Directory name (relative to --out) for a given source.

    Always strip the extension. Uniqueness of stems within a module is
    a data-model invariant enforced by the zero-padded ``NNN`` prefix
    every source carries; two sources with the same stem but different
    extensions in the same directory would be a data-entry bug.

    Examples:
        sources/a/000 foo.mp4  → a/000 foo
        sources/a/001 bar.html → a/001 bar
        sources/a/002 baz.pdf  → a/002 baz
    """
    rel = source.relative_to(sources_root)
    return rel.with_suffix("")


def reclaim_orphan_outputs(
    sources_root: Path,
    out_root: Path,
    dry_run: bool = False,
) -> int:
    """
    Delete <out_root>/<mirror>/<slug>/ directories whose matching source
    file no longer exists under <sources_root>/<mirror>/<slug>.<ext>.

    Mirror operation to the forward scan (sources without raw.json →
    extract). Together they keep the raw tree in sync with sources;
    the rename case works automatically.

    Top-level files under out_root (CLAUDE.md, README.md) are ignored
    because we only look at directories containing a ``raw.json``.

    Second pass: stale ``*.tmp`` staging dirs from the atomic-write
    pattern (``<slug>.tmp/raw.json`` → ``<slug>/``). At startup no
    extraction is mid-flight, so any surviving ``*.tmp`` dir is
    garbage — unless the source itself legitimately has ``.tmp`` in
    its basename, in which case we keep it.

    Returns the number of paths reclaimed (orphan raws + stale .tmp
    dirs), or would-be reclaimed when dry_run=True.
    """
    if not out_root.exists():
        return 0

    orphans: list[Path] = []
    for raw in out_root.rglob("raw.json"):
        slug_dir = raw.parent
        slug_rel = slug_dir.relative_to(out_root)
        has_source = any(
            (sources_root / (str(slug_rel) + ext)).exists()
            for ext in INGEST_EXTENSIONS
        )
        if not has_source:
            orphans.append(slug_dir)

    for slug_dir in orphans:
        slug_rel = slug_dir.relative_to(out_root)
        verb = "would remove" if dry_run else "removing"
        print(f"[reclaim] {verb} orphan {slug_rel}")
        if dry_run:
            continue
        shutil.rmtree(slug_dir)
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
        print(f"[reclaim] {verb} stale .tmp {slug_rel}")
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
# helpers
# ---------------------------------------------------------------------------

def probe_duration(path: Path) -> float:
    """Duration via ffprobe — no decoding."""
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
    """Wipe a half-written tmp directory left over from an interrupted run."""
    if not tmp_dir.exists():
        return
    for p in tmp_dir.rglob("*"):
        if p.is_file():
            p.unlink()
    for p in sorted(tmp_dir.rglob("*"), reverse=True):
        if p.is_dir():
            p.rmdir()
    tmp_dir.rmdir()


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# html extractor (non-gpu, cheap)
# ---------------------------------------------------------------------------

def ingest_html(source: Path, language: str) -> dict:
    """
    Run the HTML extractor and return the raw.json payload.

    Delegates to _extract_html.build_raw_payload so the ad-hoc CLI and
    the pipeline share one code path.
    """
    return _extract_html.build_raw_payload(source, language=language)


# ---------------------------------------------------------------------------
# pdf extractor (non-gpu, OCR-bound on image-only PDFs)
# ---------------------------------------------------------------------------

def ingest_pdf(source: Path, language: str) -> dict:
    """
    Run the PDF extractor and return the raw.json payload.

    Text-layer first (fast, via pypdf); OCR fallback on image-only
    PDFs (tesseract rus+eng at 300 DPI). CPU-only — runs on the
    ingest worker thread with no GPU contention.
    """
    return _extract_pdf.build_raw_payload(source, language=language)


# ---------------------------------------------------------------------------
# whisper path — GPU transcription of media files
# ---------------------------------------------------------------------------

def ingest_whisper(
    source: Path,
    model: WhisperModel,
    *,
    model_name: str,
    compute: str,
    beam: int,
    language: str,
    audio_dur: float,
    progress_cb,
) -> dict:
    """
    Transcribe `source` with whisper and return the raw.json payload.

    `progress_cb(step_seconds)` is called after each segment so the caller
    can advance both the inner and outer tqdm bars uniformly.
    """
    segments_iter, info = model.transcribe(
        str(source),
        language=language,
        beam_size=beam,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        word_timestamps=True,
    )

    raw_segments = []
    processed = 0.0
    for i, seg in enumerate(segments_iter, 1):
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
        step = max(seg.end - processed, 0.0)
        if step > 0:
            progress_cb(step)
            processed = seg.end

    # VAD may have trimmed trailing silence — top up to nominal length.
    tail = max(audio_dur - processed, 0.0)
    if tail > 0:
        progress_cb(tail)

    now = utc_now_iso()
    return {
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


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="/workspace/sources",
                    help="Root with source files (recursive scan). "
                         "Any suffix in INGEST_EXTENSIONS is picked up.")
    ap.add_argument("--out", default="/workspace/vault/raw/data",
                    help="Where to place extracts (default: vault/raw/data)")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--compute", default="float16",
                    choices=["float16", "bfloat16", "int8_float16"])
    ap.add_argument("--beam", type=int, default=5)
    ap.add_argument("--language", default="ru")
    ap.add_argument("--reclaim-dry-run", action="store_true",
                    help="Log orphan raw dirs but do not delete them.")
    args = ap.parse_args()

    sources_root = Path(args.sources)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    def out_dir_for(src: Path) -> Path:
        return out_root / out_slug_for(src, sources_root)

    # ----- 0. Reconcile: drop orphan raw dirs whose source was removed -----
    n_reclaimed = reclaim_orphan_outputs(
        sources_root, out_root, dry_run=args.reclaim_dry_run,
    )
    # Always emit the heartbeat (even for 0 items) so the smoke test
    # can assert the reclaim code path ran. See tests/smoke.md §8.
    print(f"[reclaim] startup pass complete — {n_reclaimed} item(s) "
          f"{'would be reclaimed (dry-run)' if args.reclaim_dry_run else 'reclaimed'}")

    # ----- 1. Scan sources + pick the missing ones -----
    # Sort by slug (stem-only, ext stripped) rather than full path so
    # the processing order matches the daemon's priority-queue order
    # (ADR 0008) — lexicographic slug order is the NNN-prefix order
    # from ADR 0004 (000/000, 000/001, 001/000, ...). We do NOT group
    # by extractor type — later sources may cite earlier ones across
    # formats (e.g. a whisper transcript of a lecture citing a PDF).
    all_sources = sorted(
        (p for p in sources_root.rglob("*")
         if p.is_file() and extractor_for(p) is not None),
        key=lambda p: str(out_slug_for(p, sources_root)),
    )
    pending = [s for s in all_sources
               if not (out_dir_for(s) / "raw.json").exists()]

    pending_whisper = [s for s in pending if extractor_for(s) == "whisper"]
    pending_html = [s for s in pending if extractor_for(s) == "html"]
    pending_pdf = [s for s in pending if extractor_for(s) == "pdf"]

    done_count = len(all_sources) - len(pending)
    print(f"[scan ] sources found: {len(all_sources)}  "
          f"done: {done_count}  pending: {len(pending)} "
          f"(whisper: {len(pending_whisper)}, html: {len(pending_html)}, "
          f"pdf: {len(pending_pdf)})")

    if not pending:
        print("[done ] nothing to do — vault/raw/data is up to date")
        return

    # ----- 2. Probe whisper durations up front (for the outer bar) -----
    durations: dict[Path, float] = {}
    total_audio = 0.0
    if pending_whisper:
        print("[probe] measuring whisper-input durations via ffprobe...")
        durations = {s: probe_duration(s) for s in pending_whisper}
        total_audio = sum(durations.values())
        print(f"[probe] whisper queue: {len(pending_whisper)} files, "
              f"{total_audio/3600:.2f}h audio total "
              f"(≈{total_audio*0.05/60:.1f} min wall @ RTF 0.05)")

    # ----- 3. Whisper model, lazily loaded on first whisper item -----
    model: Optional[WhisperModel] = None

    def _ensure_model() -> WhisperModel:
        nonlocal model
        if model is None:
            print(f"[load ] {args.model} on cuda ({args.compute})")
            t0 = time.time()
            model = WhisperModel(
                args.model,
                device="cuda",
                compute_type=args.compute,
                download_root="/workspace/models",
            )
            print(f"[load ] done in {time.time() - t0:.1f}s")
        return model

    # ----- 4. Outer audio-seconds bar (only meaningful with whisper) -----
    outer_bar = None
    if pending_whisper:
        outer_bar = tqdm(
            total=total_audio,
            desc="TOTAL",
            position=0,
            unit="s",
            dynamic_ncols=True,
            bar_format=(
                "{l_bar}{bar}| {n:.0f}/{total:.0f}s "
                "[{elapsed}<{remaining}]"
            ),
        )

    # ----- 5. Single unified loop — STRICT slug order -----
    # Processing 000/000 → 000/001 → 001/000 → ... matters because
    # later sources may cite earlier ones (e.g. "part 2" references
    # "part 1"). Do NOT re-group by extractor type. See
    # docs/adr/0008 amendments.
    def _say(msg: str) -> None:
        # Write through the bar when active so tqdm redraws cleanly.
        if outer_bar is not None:
            outer_bar.write(msg)
        else:
            print(msg)

    try:
        whisper_seen = 0
        for idx, source in enumerate(pending, 1):
            kind = extractor_for(source)
            stem = source.stem
            out_dir = out_dir_for(source)
            tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"
            out_dir.parent.mkdir(parents=True, exist_ok=True)
            clean_tmp_dir(tmp_dir)
            tmp_dir.mkdir(parents=True)

            if kind == "html":
                payload = ingest_html(source, language=args.language)
                (tmp_dir / "raw.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                tmp_dir.rename(out_dir)
                _say(f"[html ] [{idx}/{len(pending)}] {stem[:70]} — "
                     f"{payload['info']['paragraph_count']} paragraphs")

            elif kind == "pdf":
                payload = ingest_pdf(source, language=args.language)
                (tmp_dir / "raw.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                tmp_dir.rename(out_dir)
                info = payload["info"]
                _say(f"[pdf  ] [{idx}/{len(pending)}] {stem[:70]} — "
                     f"{info['paragraph_count']} paragraphs "
                     f"({info['page_count']} pages, "
                     f"source={info['pdf_text_source']})")

            elif kind == "whisper":
                _model = _ensure_model()
                audio_dur = durations[source]
                whisper_seen += 1
                label = stem if len(stem) <= 55 else stem[:52] + "..."
                label = f"[{whisper_seen}/{len(pending_whisper)}] {label}"

                inner_bar = tqdm(
                    total=audio_dur,
                    desc=label,
                    position=1,
                    leave=False,
                    unit="s",
                    dynamic_ncols=True,
                    bar_format="{l_bar}{bar}| {n:.0f}/{total:.0f}s",
                )

                def _tick(step: float, _inner=inner_bar, _outer=outer_bar):
                    _inner.update(step)
                    if _outer is not None:
                        _outer.update(step)

                t_file = time.time()
                payload = ingest_whisper(
                    source, _model,
                    model_name=args.model,
                    compute=args.compute,
                    beam=args.beam,
                    language=args.language,
                    audio_dur=audio_dur,
                    progress_cb=_tick,
                )

                (tmp_dir / "raw.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                tmp_dir.rename(out_dir)
                inner_bar.close()

                wall = time.time() - t_file
                rtf = wall / max(audio_dur, 1e-6)
                _say(f"[done ] {stem[:70]} — {len(payload['segments'])} segs, "
                     f"audio {audio_dur:.0f}s, wall {wall:.0f}s, "
                     f"RTF {rtf:.3f}")

    finally:
        if outer_bar is not None:
            outer_bar.close()

    print(f"\n[done ] processed {len(pending)} sources -> {out_root}")


if __name__ == "__main__":
    main()
