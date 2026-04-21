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
import subprocess
import sys
import time
from pathlib import Path

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
    args = ap.parse_args()

    sources_root = Path(args.sources)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    def out_dir_for(src: Path) -> Path:
        return out_root / out_slug_for(src, sources_root)

    # ----- 1. Scan sources + pick the missing ones -----
    all_sources = sorted(p for p in sources_root.rglob("*")
                         if p.is_file() and extractor_for(p) is not None)
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

    # ----- 2. HTML first (cheap, no GPU needed) -----
    if pending_html:
        print(f"[html ] extracting {len(pending_html)} HTML page(s)")
        for idx, source in enumerate(pending_html, 1):
            stem = source.stem
            out_dir = out_dir_for(source)
            tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"
            out_dir.parent.mkdir(parents=True, exist_ok=True)
            clean_tmp_dir(tmp_dir)
            tmp_dir.mkdir(parents=True)

            payload = ingest_html(source, language=args.language)
            (tmp_dir / "raw.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_dir.rename(out_dir)
            print(f"[html ] [{idx}/{len(pending_html)}] {stem[:70]} — "
                  f"{payload['info']['paragraph_count']} paragraphs")

    # ----- 2b. PDF next (CPU-bound: text-layer fast; OCR slow-ish) -----
    if pending_pdf:
        print(f"[pdf  ] extracting {len(pending_pdf)} PDF file(s)")
        for idx, source in enumerate(pending_pdf, 1):
            stem = source.stem
            out_dir = out_dir_for(source)
            tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"
            out_dir.parent.mkdir(parents=True, exist_ok=True)
            clean_tmp_dir(tmp_dir)
            tmp_dir.mkdir(parents=True)

            payload = ingest_pdf(source, language=args.language)
            (tmp_dir / "raw.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp_dir.rename(out_dir)
            info = payload["info"]
            print(f"[pdf  ] [{idx}/{len(pending_pdf)}] {stem[:70]} — "
                  f"{info['paragraph_count']} paragraphs "
                  f"({info['page_count']} pages, "
                  f"source={info['pdf_text_source']})")

    if not pending_whisper:
        print(f"\n[done ] processed {len(pending)} sources -> {out_root}")
        return

    # ----- 3. Durations up front (accurate outer progress bar) -----
    print("[probe] measuring durations via ffprobe...")
    durations = {s: probe_duration(s) for s in pending_whisper}
    total_audio = sum(durations.values())
    print(f"[probe] queue: {len(pending_whisper)} files, "
          f"{total_audio/3600:.2f}h audio total "
          f"(≈{total_audio*0.05/60:.1f} min wall @ RTF 0.05)")

    # ----- 4. Load the model once for the whole batch -----
    print(f"[load ] {args.model} on cuda ({args.compute})")
    t0 = time.time()
    model = WhisperModel(
        args.model,
        device="cuda",
        compute_type=args.compute,
        download_root="/workspace/models",
    )
    print(f"[load ] done in {time.time() - t0:.1f}s")

    # ----- 5. Transcription with a double progress bar -----
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

    try:
        for idx, source in enumerate(pending_whisper, 1):
            audio_dur = durations[source]
            stem = source.stem
            out_dir = out_dir_for(source)
            tmp_dir = out_dir.parent / f"{out_dir.name}.tmp"
            out_dir.parent.mkdir(parents=True, exist_ok=True)
            clean_tmp_dir(tmp_dir)
            tmp_dir.mkdir(parents=True)

            label = stem if len(stem) <= 55 else stem[:52] + "..."
            label = f"[{idx}/{len(pending_whisper)}] {label}"

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
                _outer.update(step)

            t_file = time.time()
            payload = ingest_whisper(
                source, model,
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

            # atomic final rename
            tmp_dir.rename(out_dir)
            inner_bar.close()

            wall = time.time() - t_file
            rtf = wall / max(audio_dur, 1e-6)
            outer_bar.write(
                f"[done ] {stem[:70]} — {len(payload['segments'])} segs, "
                f"audio {audio_dur:.0f}s, wall {wall:.0f}s, RTF {rtf:.3f}"
            )

    finally:
        outer_bar.close()

    print(f"\n[done ] processed {len(pending)} sources -> {out_root}")


if __name__ == "__main__":
    main()
