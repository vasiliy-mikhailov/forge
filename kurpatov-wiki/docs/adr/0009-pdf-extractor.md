# 0009 — PDF extractor: OCR-first, text-layer fallthrough

Status: Accepted (2026-04-21)

## Context

[ADR 0008](0008-ingest-dispatch.md) left room for the ingest daemon
to grow beyond audio/video + HTML:

> Future extractors (PDF exports, .docx, .srt re-ingest, …) each get
> their own extension allow-list and their own `_extract_<kind>.py`.

PDFs turn up in the course material in two shapes:

1. **macOS "Print to PDF" scans.** A lesson whose original source was
   a slide deck, a Word document, or a photograph of handwritten
   notes, run through the macOS print pipeline. The output is a PDF
   whose every page is a single JPEG — no embedded text layer, no
   `/Font` dictionary, no character information at all. `pypdf` on
   such a file returns the empty string.
2. **Typeset exports with a text layer.** Word → "Export as PDF",
   LaTeX → `pdflatex`, or equivalents. Here `pypdf` can pull the
   text directly — fast, lossless, and safe against OCR substitution
   errors.

We want one extractor that handles both without surprising the
ingest operator. The first source we care about in practice is of
type (1) — image-only scans of Russian text — so OCR must work well
out of the box; (2) should still get the fast path when it's
available.

Questions:

* **Which OCR engine?** Tesseract, EasyOCR, and PaddleOCR all have
  working Russian models. Tesseract ships a native Ubuntu apt
  package with a stable Russian traineddata (`tesseract-ocr-rus`),
  runs CPU-only, and has negligible cold-start. EasyOCR and
  PaddleOCR each want a PyTorch/Paddle stack and some GPU VRAM to
  be useful; on our ingest worker that VRAM is already claimed by
  faster-whisper and we don't want to fight over it.
* **Detection vs. always-OCR?** Running OCR unconditionally on a
  native-text PDF wastes seconds per page and introduces substitution
  noise. Trusting `pypdf` unconditionally returns empty segments on
  scans. We want a detector.
* **Segmentation.** The other extractors emit one segment per
  natural unit (whisper — one sentence-ish chunk; html — one
  paragraph). PDFs need something similar. Page anchoring matters
  too — the wiki-layer renderer should be able to say "see source,
  p. 7" when summarizing.
* **Memory.** At 300 DPI a single A4 page rasterizes to a ~25 MB RGB
  bitmap. A 30-page deck converted all at once balloons to ~750 MB
  plus tesseract's working set, which OOMs modest workers.

## Decision

1. **Tesseract is the OCR engine** (lang `rus+eng`, 300 DPI). apt
   packages (`tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng`)
   plus `poppler-utils` for `pdftoppm`, plus `pypdf + pdf2image +
   pytesseract + Pillow` on the Python side. CPU-only. No GPU
   contention with whisper, no extra weights to download at build
   time.
2. **Text-layer first, OCR fallback.** The extractor calls
   `pypdf.PdfReader.extract_text()` on every page; if the total is
   ≥ 500 characters it keeps that output and skips OCR entirely.
   Otherwise it rasterizes and OCRs. A `--force-ocr` flag overrides
   the detector for cases where the embedded text layer is known to
   be ligature noise.
3. **Segmentation mirrors `_extract_html.py`.** One segment per
   paragraph (blank-line boundaries), wrap line-breaks inside a
   paragraph collapsed to single spaces, bullet glyphs normalised
   to `- `, page-number-only and ≤3-char OCR noise paragraphs
   dropped. Segments carry a 1-based `page` field so quotes can be
   cited.
4. **Page-by-page rasterization.** `pdf2image.convert_from_path` is
   called with `first_page=n`, `last_page=n`, processing one page
   at a time and closing each image before moving on. Peak memory
   stays at one page's worth regardless of deck length.
5. **raw.json contract additions** (on top of the ADR 0008 schema):

        info.extractor        = "pdf"
        info.page_count       = int
        info.paragraph_count  = int   (len(segments))
        info.pdf_text_source  = "text_layer" | "ocr"
        info.ocr_lang         = "rus+eng"   (when ocr ran)
        info.ocr_dpi          = 300         (when ocr ran)
        segments[].page       = 1-based page number

6. **Dispatch.** `02_ingest_incremental.py` and
   `03_watch_and_ingest.py` both grow a `PDF_EXTENSIONS = {".pdf"}`
   allow-list, an `ingest_pdf` branch in `extractor_for()`, and a
   PDF processing slot that runs alongside HTML (cheap, before the
   whisper batch). The daemon never loads the whisper model for a
   PDF.
7. **No confidence score in MVP.** Tesseract exposes a per-word
   confidence, but we don't surface it. If mis-OCR turns out to
   corrupt summaries we'll revisit — for now `pdf_text_source =
   "ocr"` is a coarse signal the summarizer prompt can lean on.

## Consequences

* Image-only Russian PDFs (the expected majority) ingest end-to-end
  with no user intervention beyond dropping the file under
  `sources/<mirror>/`.
* Typeset PDFs, when they appear, skip OCR and finish in seconds.
* Container image grows by ~140 MB (tesseract binaries + Russian
  traineddata + poppler + Pillow). No GPU memory impact.
* The `segments[].page` anchor gives the wiki-layer renderer a
  lighter-weight citation than whisper's `start`/`end` — one number,
  unambiguous.
* OCR substitution errors will leak into summaries on difficult
  scans (cursive, rotated pages). Acceptable for now; a manual
  override lives on the Mac side (edit `raw.json` in place; the
  pusher treats it as just another file).

## Alternatives considered

* **EasyOCR** — larger model download, competes with whisper for VRAM,
  worse Cyrillic punctuation handling on scanned A4 in our spot
  check.
* **PaddleOCR** — similar VRAM issue; the Paddle toolchain is
  heavier to keep in a CUDA image we already use primarily for
  PyTorch.
* **Always OCR.** Would waste seconds per page on typeset PDFs and
  introduce substitution noise where none exists. Detector is cheap.
* **Per-page JSON instead of per-paragraph segments.** Rejected — it
  would diverge from the schema the HTML and whisper extractors
  already share, and forces the summarizer to redo paragraph
  detection. `segments[].page` gives us the page anchor without a
  schema split.
