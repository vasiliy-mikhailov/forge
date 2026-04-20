"""
HTML → raw.json extractor for the Kurpatov-wiki ingest pipeline.

Scope:
    Some source materials arrive as getcourse.ru lesson-page HTML exports
    (the "print to HTML" archive the student can save from their course
    account). These pages carry the lecturer's prose alongside a lot of
    chrome: page scaffolding, an embedded video/audio player, student
    self-answers, comments. This module extracts ONLY the lecture prose
    and emits the same raw.json shape the whisper path produces, so the
    downstream wiki layer can treat both uniformly.

Output schema (shared with 02_ingest_incremental.py on the media path):

    info.language        — language tag (fixed "ru" for this course)
    info.source_path     — absolute path to the HTML file
    info.extractor       — "html"  (distinguishes from "whisper")
    info.title           — lesson title (<h2 class="lesson-title-value">)
    info.extracted_at    — ISO-8601 UTC
    info.paragraph_count — len(segments), convenience
    segments[].id        — 1-based
    segments[].text      — one paragraph of lecture prose (no start/end)

Forum content — student self-answers (.addfield.type-text under
.self-answers / .answer_wrapper), comments (.comments-tree), and the
embedded player itself — is explicitly dropped. Only .text-normal.f-text
blocks are harvested, because those are the lecturer-authored prose
blocks in the getcourse.ru page builder.

Run standalone for ad-hoc extraction:

    python _extract_html.py <path/to/lesson.html> [--out raw.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------

_WS_RE = re.compile(r"[ \u00a0\t]+")
_NL_RE = re.compile(r"\n{3,}")


def _normalize(text: str) -> str:
    """Collapse runs of whitespace, keep paragraph breaks."""
    text = text.replace("\u00a0", " ")
    text = _WS_RE.sub(" ", text)
    text = _NL_RE.sub("\n\n", text)
    return text.strip()


def _block_to_paragraphs(block) -> list[str]:
    """
    Split one .text-normal.f-text <div> into paragraph-sized strings.

    The getcourse.ru page builder tends to wrap each block in a single
    <p> that uses <br><br> for paragraph breaks, but sometimes it puts
    multiple <p> siblings at the top level. We handle both — split on
    <br><br>, then split on <p> boundaries, then strip residual tags
    via get_text.
    """
    # Insert paragraph separators at <br> boundaries so get_text preserves
    # them. Two consecutive <br>s become a paragraph boundary; single ones
    # become a soft newline inside a paragraph.
    for br in block.find_all("br"):
        br.replace_with("\n")

    chunks: list[str] = []
    # Prefer <p> children if present.
    paras = block.find_all("p", recursive=False)
    if paras:
        for p in paras:
            raw = p.get_text(separator="", strip=False)
            chunks.extend(piece for piece in re.split(r"\n\s*\n", raw))
    else:
        raw = block.get_text(separator="", strip=False)
        chunks.extend(piece for piece in re.split(r"\n\s*\n", raw))

    return [c for c in (_normalize(c) for c in chunks) if c]


def extract_paragraphs(html: str) -> tuple[str | None, list[str]]:
    """
    Parse an HTML document and return (title, paragraphs).

    Only <div class="text-normal f-text"> blocks are harvested. Any block
    that lives inside .self-answers, .answer_wrapper, .comments-tree, or
    any .comment is dropped (belt-and-braces — these classes shouldn't
    host .text-normal.f-text blocks, but we guard anyway so a future
    getcourse.ru template change can't leak student/comment text into
    the lecture output).
    """
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_el = soup.select_one("h2.lesson-title-value") \
        or soup.select_one(".lesson-title-value") \
        or soup.select_one("title")
    title = title_el.get_text(strip=True) if title_el else None

    # Drop everything forum-ish before we scan for prose blocks.
    for sel in (
        ".self-answers",
        ".answer_wrapper",
        ".comments-tree",
        ".comment-list",
        ".comment",
        ".b-like-and-subscribe-notifications",
        ".new-comment",
        ".gc-comment-form",
    ):
        for node in soup.select(sel):
            node.decompose()

    paragraphs: list[str] = []
    for block in soup.select("div.text-normal.f-text"):
        paragraphs.extend(_block_to_paragraphs(block))

    return title, paragraphs


# ---------------------------------------------------------------------------
# raw.json emitter
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_raw_payload(source: Path, language: str = "ru") -> dict[str, Any]:
    """Parse `source` and build the raw.json payload dict."""
    html = source.read_text(encoding="utf-8", errors="replace")
    title, paragraphs = extract_paragraphs(html)

    segments = [
        {"id": i, "text": text}
        for i, text in enumerate(paragraphs, 1)
    ]

    return {
        "info": {
            "language": language,
            "source_path": str(source),
            "extractor": "html",
            "title": title,
            "extracted_at": _utc_now_iso(),
            "paragraph_count": len(segments),
        },
        "segments": segments,
    }


# ---------------------------------------------------------------------------
# CLI (stand-alone use)
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", type=Path, help="HTML file to extract")
    ap.add_argument("--out", type=Path,
                    help="Where to write raw.json (default: stdout)")
    ap.add_argument("--language", default="ru")
    args = ap.parse_args()

    payload = build_raw_payload(args.source, language=args.language)
    text = json.dumps(payload, ensure_ascii=False, indent=2)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"[done ] {args.source.name} → {args.out} "
              f"({payload['info']['paragraph_count']} paragraphs, "
              f"title: {payload['info']['title']!r})")
    else:
        print(text)


if __name__ == "__main__":
    main()
