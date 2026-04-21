"""
PDF → raw.json extractor for the Kurpatov-wiki ingest pipeline.

Scope:
    Lesson materials arrive as PDFs in two shapes:

      1. Image-only scans (macOS "Print to PDF" via Quartz PDFContext
         and similar workflows — each page is a single JPEG with no
         embedded text layer). These go through the VLM path below.
      2. Typeset exports with an embedded text layer (Word → "Export
         as PDF", LaTeX → pdflatex). These go through pypdf directly.

A detector picks the fast path when the PDF has enough extractable
text; otherwise we fall back to the VLM.

The VLM path uses **Qwen/Qwen2.5-VL-7B-Instruct** loaded via HuggingFace
`transformers` in bfloat16 on CUDA. See
[ADR 0009](../docs/adr/0009-pdf-extractor.md) 2026-04-21 revised
amendment for why we chose a vision-language model over
tesseract / PaddleOCR / Surya.

Output shape matches the other extractors' raw.json contract (ADR
0008). PDF-specific fields:

      * info.page_count            — number of pages
      * info.pdf_text_source       — "text_layer" | "qwen2.5-vl"
      * info.ocr_model             — HF model id (when vlm ran)
      * info.ocr_dpi               — rasterization DPI (when vlm ran)
      * segments[].page            — 1-based page number

Segmentation: one segment per paragraph (blank-line boundaries). Wrap
line-breaks inside a paragraph are collapsed to single spaces,
page-number-only paragraphs are dropped, and paragraphs shorter than
4 characters are dropped as noise.

Run standalone for ad-hoc extraction:

    python _extract_pdf.py <path/to/lesson.pdf> [--out raw.json] \\
                          [--dpi 200] [--force-vlm]
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
# tunables
# ---------------------------------------------------------------------------

# Minimum extractable character count across the document for us to
# trust the embedded text layer and skip the VLM.
_TEXT_LAYER_MIN_CHARS = 500

# 200 DPI is Qwen2.5-VL's sweet spot on A4: the vision encoder
# patchifies to ~28x28 pixel tiles, so more DPI burns VRAM + time
# with no visible quality gain. Lower than 150 starts losing thin
# Cyrillic diacritics on small print.
_DEFAULT_DPI = 200

# Default HF repo for the VLM path.
_DEFAULT_VLM_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"

# Instruction handed to the VLM for every page. Terse + explicit —
# Qwen2.5-VL is chat-tuned and will otherwise add "Here is the
# transcription:" style preamble.
_VLM_PROMPT = (
    "Transcribe all text from this page image in natural reading "
    "order. Preserve paragraph breaks exactly as they appear in the "
    "source. Do not add any commentary, captions, descriptions, or "
    "metadata — output only the text content that is visible on the "
    "page."
)

# Generous but finite; a dense A4 of Russian prose tokenizes to ~800
# tokens, so 4096 is ~5x headroom plus slack for lists/tables.
_VLM_MAX_NEW_TOKENS = 4096

_WS_RE = re.compile(r"\s+")
_PAGENUM_ONLY_RE = re.compile(r"^\s*\d{1,4}\s*$")


# ---------------------------------------------------------------------------
# text-layer detection + extraction
# ---------------------------------------------------------------------------

def _has_usable_text_layer(reader: PdfReader) -> bool:
    """Heuristic: does this PDF carry enough extractable text to skip the VLM?"""
    total = 0
    for page in reader.pages:
        try:
            total += len((page.extract_text() or "").strip())
        except Exception:
            continue
        if total >= _TEXT_LAYER_MIN_CHARS:
            return True
    return False


def _paragraphs_from_page_text(text: str) -> list[str]:
    """
    Split a single page's text into paragraphs.

    Splits on blank-line boundaries. Inside a paragraph, wrap line
    breaks are collapsed to single spaces. Page-number-only and
    ≤3-char noise paragraphs are dropped.
    """
    # Form-feed can appear between pages when we concatenate; strip.
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
            continue
        if len(joined) <= 3:
            continue
        paragraphs.append(joined)
    return paragraphs


def _extract_via_text_layer(reader: PdfReader) -> list[tuple[int, str]]:
    """(page_number, paragraph) tuples from the embedded text layer."""
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
# VLM path — Qwen2.5-VL-7B-Instruct via transformers
# ---------------------------------------------------------------------------

# Module-level cache: load the VLM once per process and reuse across
# files. The ingest daemon processes PDFs sequentially, so this amortises
# the ~10-30s weight-load cost across a batch.
_vlm_cache: dict[str, Any] = {}


def _load_vlm(model_id: str) -> tuple[Any, Any, Any]:
    """Lazy-load the VLM and its processor; cached at module scope."""
    import torch  # noqa: WPS433
    from transformers import (  # noqa: WPS433
        AutoProcessor,
        Qwen2_5_VLForConditionalGeneration,
    )

    if _vlm_cache.get("model_id") == model_id:
        return (
            _vlm_cache["model"],
            _vlm_cache["processor"],
            _vlm_cache["torch"],
        )

    processor = AutoProcessor.from_pretrained(model_id)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
        attn_implementation="sdpa",
    )
    model.eval()
    _vlm_cache.clear()
    _vlm_cache.update(
        model_id=model_id,
        model=model,
        processor=processor,
        torch=torch,
    )
    return model, processor, torch


def _vlm_page_text(model, processor, torch, img) -> str:
    """Run Qwen2.5-VL on a single PIL image and return the transcribed text."""
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": img},
            {"type": "text", "text": _VLM_PROMPT},
        ],
    }]
    chat = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
    )
    inputs = processor(
        text=[chat],
        images=[img],
        padding=True,
        return_tensors="pt",
    ).to("cuda")
    with torch.inference_mode():
        gen_ids = model.generate(
            **inputs,
            max_new_tokens=_VLM_MAX_NEW_TOKENS,
            do_sample=False,
        )
    # strip the prompt echo — every row of gen_ids starts with its
    # corresponding input row, then the new tokens.
    trimmed = [
        out[len(inp):]
        for inp, out in zip(inputs.input_ids, gen_ids)
    ]
    decoded = processor.batch_decode(
        trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    return decoded[0]


def _extract_via_vlm(
    source: Path,
    *,
    model_id: str = _DEFAULT_VLM_MODEL,
    dpi: int = _DEFAULT_DPI,
    page_count: int | None = None,
) -> list[tuple[int, str]]:
    """
    Rasterize each page and send it through the VLM, page-by-page.

    Rasterizing one page at a time keeps peak memory at one page's
    worth. The VLM itself is loaded once per process and cached at
    module scope via _load_vlm.
    """
    from pdf2image import convert_from_path  # noqa: WPS433

    if page_count is None:
        page_count = len(PdfReader(str(source)).pages)

    model, processor, torch = _load_vlm(model_id)

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
            text = _vlm_page_text(model, processor, torch, img)
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
    dpi: int = _DEFAULT_DPI,
    vlm_model: str = _DEFAULT_VLM_MODEL,
    force_vlm: bool = False,
) -> dict[str, Any]:
    """
    Parse ``source`` and build the raw.json payload dict.

    Tries the text-layer path first; falls back to the VLM. ``force_vlm``
    skips the text-layer detection (useful when the embedded text
    layer is known to be ligature noise).
    """
    reader = PdfReader(str(source))
    page_count = len(reader.pages)

    used = None  # "text_layer" | "qwen2.5-vl"
    pairs: list[tuple[int, str]] = []

    if not force_vlm and _has_usable_text_layer(reader):
        pairs = _extract_via_text_layer(reader)
        used = "text_layer"

    if not pairs:
        pairs = _extract_via_vlm(
            source, model_id=vlm_model, dpi=dpi, page_count=page_count,
        )
        used = "qwen2.5-vl"

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
    if used == "qwen2.5-vl":
        info["ocr_model"] = vlm_model
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
    ap.add_argument("--dpi", type=int, default=_DEFAULT_DPI,
                    help=f"Rasterization DPI for the VLM path "
                         f"(default: {_DEFAULT_DPI})")
    ap.add_argument("--vlm-model", default=_DEFAULT_VLM_MODEL,
                    help=f"HF repo id for the VLM "
                         f"(default: {_DEFAULT_VLM_MODEL})")
    ap.add_argument("--force-vlm", action="store_true",
                    help="Skip text-layer detection; always use the VLM.")
    args = ap.parse_args()

    payload = build_raw_payload(
        args.source,
        language=args.language,
        dpi=args.dpi,
        vlm_model=args.vlm_model,
        force_vlm=args.force_vlm,
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
