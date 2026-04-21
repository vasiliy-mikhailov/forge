"""
PDF → raw.json extractor for the Kurpatov-wiki ingest pipeline.

Scope:
    Lesson materials sometimes arrive as PDF exports (typically macOS
    "Print to PDF" via Quartz PDFContext, or a similar workflow that
    stores each page as a single JPEG with no text layer). A minority
    of future PDFs may carry a text layer — typeset material exported
    from Word/LaTeX. This module handles both:

      1. If the file has a usable text layer (pypdf can pull > ~500
         characters across the document and page 1 is not blank),
         we read it directly — fast, lossless.
      2. Otherwise we rasterize each page with pdf2image and OCR it
         with tesseract (lang=rus+eng). CPU-only; runs on the ingest
         worker thread with no GPU contention.

The output shape matches the other extractors' raw.json contract
(see ADR 0008). Three additions specific to PDF:

      * info.page_count            — number of pages
      * info.pdf_text_source       — "text_layer" | "ocr" | "mixed"
      * info.ocr_lang              — tesseract -l string (when OCR ran)
      * segments[].page            — 1-based page number; lets the
                                     wiki-layer renderer anchor quotes
                                     to a specific page.

Segmentation mirrors the HTML extractor's "one segment per
structural unit" policy: within each page we split on blank-line
boundaries and emit one segment per paragraph. Wrap-induced soft
line breaks inside a paragraph are collapsed to single spaces.
Common OCR bullet glyphs (©, •, ●, ○, ◦) that show up at the start
of a paragraph are normalised to the "- " bullet prefix used by the
HTML extractor, so the downstream summarization prompt sees the
same list markers regardless of source.

Run standalone for ad-hoc extraction:

    python _extract_pdf.py <path/to/lesson.pdf> [--out raw.json] \
                          [--dpi 300] [--ocr-lang rus+eng]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


# ---------------------------------------------------------------------------
# text-layer detection
# ---------------------------------------------------------------------------

_TEXT_LAYER_MIN_CHARS = 500
_WS_RE = re.compile(r"\s+")
# Bullet glyphs tesseract frequently returns for round bullet markers.
_BULLET_RE = re.compile(r"^[©•●○◦▪▫·○◯]\s+")
# A page-number-only paragraph: just digits (maybe with noise like "OT" for "01").
_PAGENUM_ONLY_RE = re.compile(r"^\s*[OoО0-9]{1,4}\s*$")


def _has_usable_text_layer(reader: PdfReader) -> bool:
    """Heuristic: does this PDF carry enough extractable text to skip OCR?"""
    total = 0
    for page in reader.pages:
        try:
            total += len((page.extract_text() or "").strip())
        except Exception:
            continue
        if total >= _TEXT_LAYER_MIN_CHARS:
            return True
    return False


# ---------------------------------------------------------------------------
# paragraph splitting (shared by text-layer and OCR paths)
# ---------------------------------------------------------------------------

def _paragraphs_from_page_text(text: str) -> list[str]:
    """
    Split a single page's text into paragraphs.

    Splits on blank-line boundaries. Within a paragraph, wrap line
    breaks are collapsed to single spaces (a PDF page wraps a long
    sentence across visual lines; we don't want that wrap as a
    semantic boundary). Bullet glyphs at the start of a paragraph
    are normalised to ``- ``.
    """
    # form-feed can appear between pages when we concatenate; strip.
    text = text.replace("\x0c", "\n")
    paragraphs: list[str] = []
    for chunk in re.split(r"\n\s*\n+", text):
        lines = [ln.strip() for ln in chunk.split("\n") if ln.strip()]
        if not lines:
            continue
        joined = _WS_RE.sub(" ", " ".join(lines)).strip()
        if not joined:
            continue
        if _PAGENUM_ONLY_RE.match(joined):
            # likely a page marker (e.g. "01" mis-OCR'd as "OT"); drop.
            continue
        joined = _BULLET_RE.sub("- ", joined)
        # drop obvious OCR noise: isolated logos/glyphs or 2-3 character
        # fragments (page-numbers mis-OCR'd as "OT", "OS", "о3", etc.,
        # stray "@" from watermark logos). A legitimate paragraph — even
        # a short heading — has more content than this.
        if len(joined) <= 3:
            continue
        paragraphs.append(joined)
    return paragraphs


# ---------------------------------------------------------------------------
# text-layer path
# ---------------------------------------------------------------------------

def _extract_via_text_layer(reader: PdfReader) -> list[tuple[int, str]]:
    """
    Return a list of (page_number, paragraph) tuples from the embedded
    text layer. Paragraph order follows page order; within a page,
    order follows pypdf's natural extract_text() order.
    """
    out: list[tuple[int, str]] = []
    for page_idx, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        for para in _paragraphs_from_page_text(text):
            out.append((page_idx, para))
    return out


# ---------------------------------------------------------------------------
# OCR path
# ---------------------------------------------------------------------------

def _extract_via_ocr(
    source: Path,
    *,
    dpi: int = 300,
    lang: str = "rus+eng",
    page_count: int | None = None,
) -> list[tuple[int, str]]:
    """
    Rasterize each page to an image and OCR it.

    We rasterize one page at a time (via ``first_page``/``last_page``)
    rather than converting the whole PDF up front. A single 300 DPI
    A4 page is ~25 MB as an in-memory RGB bitmap; a 30-page deck
    converted all at once would swell to ~750 MB plus tesseract's
    working set, which can OOM on a modestly-provisioned ingest
    worker. Page-by-page keeps the peak at one page's worth.
    """
    # Imported lazily so callers that never take the OCR path (e.g. a
    # pytest unit test on a text-layer fixture) don't pay for the heavy
    # dependencies.
    from pdf2image import convert_from_path  # noqa: WPS433
    import pytesseract  # noqa: WPS433

    if page_count is None:
        page_count = len(PdfReader(str(source)).pages)

    out: list[tuple[int, str]] = []
    for page_idx in range(1, page_count + 1):
        images = convert_from_path(
            str(source), dpi=dpi,
            first_page=page_idx, last_page=page_idx,
        )
        if not images:
            continue
        img = images[0]
        try:
            text = pytesseract.image_to_string(img, lang=lang)
        finally:
            img.close()
        for para in _paragraphs_from_page_text(text):
            out.append((page_idx, para))
    return out


# ---------------------------------------------------------------------------
# metadata helpers
# ---------------------------------------------------------------------------

def _pdf_title(reader: PdfReader) -> str | None:
    meta = reader.metadata or {}
    title = meta.get("/Title")
    if title:
        title = str(title).strip()
    return title or None


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# raw.json emitter
# ---------------------------------------------------------------------------

def build_raw_payload(
    source: Path,
    *,
    language: str = "ru",
    dpi: int = 300,
    ocr_lang: str = "rus+eng",
    force_ocr: bool = False,
) -> dict[str, Any]:
    """
    Parse ``source`` and build the raw.json payload dict.

    Tries the text-layer path first; falls back to OCR. ``force_ocr``
    skips the text-layer detection (useful when the embedded text
    layer is known to be garbage — some scanners produce a text layer
    full of ligature noise).
    """
    reader = PdfReader(str(source))
    page_count = len(reader.pages)

    used = None  # "text_layer" | "ocr"
    pairs: list[tuple[int, str]] = []

    if not force_ocr and _has_usable_text_layer(reader):
        pairs = _extract_via_text_layer(reader)
        used = "text_layer"

    if not pairs:
        pairs = _extract_via_ocr(
            source, dpi=dpi, lang=ocr_lang, page_count=page_count,
        )
        used = "ocr"

    title = _pdf_title(reader)

    segments = [
        {"id": i, "text": text, "page": page}
        for i, (page, text) in enumerate(pairs, 1)
    ]

    info: dict[str, Any] = {
        "language": language,
        "source_path": str(source),
        "extractor": "pdf",
        "title": title,
        "extracted_at": _utc_now_iso(),
        "page_count": page_count,
        "paragraph_count": len(segments),
        "pdf_text_source": used,
    }
    if used == "ocr":
        info["ocr_lang"] = ocr_lang
        info["ocr_dpi"] = dpi

    return {"info": info, "segments": segments}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", type=Path, help="PDF file to extract")
    ap.add_argument("--out", type=Path,
                    help="Where to write raw.json (default: stdout)")
    ap.add_argument("--language", default="ru")
    ap.add_argument("--dpi", type=int, default=300,
                    help="Rasterization DPI for OCR path (default: 300)")
    ap.add_argument("--ocr-lang", default="rus+eng",
                    help="tesseract -l string (default: rus+eng)")
    ap.add_argument("--force-ocr", action="store_true",
                    help="Skip text-layer detection; always OCR.")
    args = ap.parse_args()

    payload = build_raw_payload(
        args.source,
        language=args.language,
        dpi=args.dpi,
        ocr_lang=args.ocr_lang,
        force_ocr=args.force_ocr,
    )

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        info = payload["info"]
        print(
            f"[done ] {args.source.name} → {args.out} "
            f"({info['paragraph_count']} paragraphs, "
            f"{info['page_count']} pages, "
            f"source={info['pdf_text_source']}, "
            f"title={info['title']!r})"
        )
    else:
        print(text)


if __name__ == "__main__":
    main()
