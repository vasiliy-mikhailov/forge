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
    segments[].text      — one structural unit of lecture prose
                           (one paragraph, one <li>, or one heading).
                           List items are prefixed with "- " (ul)
                           or "1. " (ol). Headings are prefixed with
                           "## ".  No start/end timestamps.

Forum content — student self-answers (.addfield.type-text under
.self-answers / .answer_wrapper), comments (.comments-tree), and the
embedded player itself — is explicitly dropped. Only .text-normal.f-text
blocks are harvested, because those are the lecturer-authored prose
blocks in the getcourse.ru page builder.

Why segment-per-structural-unit:
    getcourse.ru lessons regularly interleave prose <p> with <ul> lists
    that carry curriculum bullets ("Вы научитесь: …"). An earlier
    naive flattener that walked only <p> children silently dropped the
    <ul> siblings. Walking in document order and emitting one segment
    per <p> / <li> / <hN> keeps structure faithful and lets the
    downstream summarization prompt see which lines are list items.

Run standalone for ad-hoc extraction:

    python _extract_html.py <path/to/lesson.html> [--out raw.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Iterator

from bs4 import BeautifulSoup, NavigableString, Tag


# ---------------------------------------------------------------------------
# parsing
# ---------------------------------------------------------------------------

_WS_RE = re.compile(r"[ \u00a0\t\r\n]+")

_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_LIST_TAGS = {"ul", "ol"}
_PARA_TAGS = {"p"}
_BLOCKQUOTE_TAGS = {"blockquote"}
# Container tags whose children we recurse into rather than emitting as
# a single unit. Everything else top-level we treat as a paragraph-ish
# fallback.
_CONTAINER_TAGS = {"div", "section", "article"}


def _inline_text(node: Tag | NavigableString) -> str:
    """Flatten a node to a single-line, whitespace-normalised string."""
    if isinstance(node, NavigableString):
        return _WS_RE.sub(" ", str(node)).strip()
    # Convert <br> to soft space before flattening (they're used inside
    # <li> for soft line wraps; we don't want to split a single bullet).
    for br in node.find_all("br"):
        br.replace_with(" ")
    text = node.get_text(separator=" ", strip=False)
    return _WS_RE.sub(" ", text).strip()




def _iter_text_with_br(node):
    """Yield strings for text nodes, and None as a marker for each <br>.

    Non-destructive: does not mutate the DOM (unlike replace_with, which
    would leak across sibling traversals inside _emit_list/etc.).
    """
    if isinstance(node, NavigableString):
        yield str(node)
        return
    if not isinstance(node, Tag):
        return
    if node.name == "br":
        yield None
        return
    for child in node.children:
        yield from _iter_text_with_br(child)


def _split_p_by_br_runs(p_tag: Tag) -> list[str]:
    """Split a <p>'s content on <br><br> (or longer <br> runs).

    Single <br>s become a soft space inside the same paragraph
    (getcourse.ru often uses a single <br> for a line wrap). Two or
    more in a row are treated as a paragraph boundary — some lesson
    pages ship a single giant <p> with all content separated only by
    <br><br>.
    """
    pieces: list[str] = []
    buf: list[str] = []
    br_run = 0
    for tok in _iter_text_with_br(p_tag):
        if tok is None:
            br_run += 1
            if br_run >= 2:
                text = _WS_RE.sub(" ", "".join(buf)).strip()
                if text:
                    pieces.append(text)
                buf = []
                br_run = 0
            else:
                buf.append(" ")
        else:
            br_run = 0
            buf.append(tok)
    text = _WS_RE.sub(" ", "".join(buf)).strip()
    if text:
        pieces.append(text)
    return pieces

def _emit_list(list_tag: Tag, ordered: bool, depth: int = 0) -> Iterator[str]:
    """
    Emit one segment per <li>. Nested lists are emitted as their own
    segments with an indent-aware prefix.
    """
    counter = 0
    for li in list_tag.find_all("li", recursive=False):
        counter += 1
        # Split the li into: its own text, and any nested lists.
        # We emit the li's own text first (with a bullet or number
        # prefix), then recurse into nested lists so they keep their
        # position in the output stream.
        nested_lists = []
        for child in list_tag.find_all(True):
            pass  # no-op; we iterate the specific li below
        # Clone-free approach: temporarily detach nested lists from li
        # while we extract the li's own text, then emit each nested
        # list as its own recursive batch.
        nested = [c for c in li.find_all(["ul", "ol"], recursive=False)]
        for n in nested:
            n.extract()
        own_text = _inline_text(li)
        bullet = f"{counter}. " if ordered else "- "
        indent = "  " * depth
        if own_text:
            yield f"{indent}{bullet}{own_text}"
        for n in nested:
            yield from _emit_list(n, ordered=(n.name == "ol"), depth=depth + 1)


def _emit_block(block: Tag) -> Iterator[str]:
    """
    Walk a .text-normal.f-text block in document order and yield one
    segment per structural unit: <p>, <hN>, each <li>, <blockquote>.
    <br> inside a <p> becomes a soft space; <br><br> becomes a
    paragraph boundary (splits into two <p>-equivalent segments).
    Nested container <div>/<section> are recursed into.
    """
    # (getcourse.ru lessons express paragraph breaks as sibling <p>s,
    #  not as <br><br> inside a single <p>, so we don't split <br><br>
    #  here. _inline_text() will collapse any embedded <br> to a soft
    #  space.)

    # Walk top-level children, dispatching by tag.
    for child in block.children:
        if isinstance(child, NavigableString):
            txt = _WS_RE.sub(" ", str(child)).strip()
            if txt:
                yield txt
            continue
        if not isinstance(child, Tag):
            continue
        name = child.name.lower()
        if name in _HEADING_TAGS:
            txt = _inline_text(child)
            if txt:
                yield f"## {txt}"
        elif name in _PARA_TAGS:
            for piece in _split_p_by_br_runs(child):
                yield piece
        elif name in _LIST_TAGS:
            yield from _emit_list(child, ordered=(name == "ol"))
        elif name in _BLOCKQUOTE_TAGS:
            txt = _inline_text(child)
            if txt:
                yield f"> {txt}"
        elif name in _CONTAINER_TAGS:
            # Recurse into containers (getcourse.ru nests text inside
            # <div>s occasionally).
            yield from _emit_block(child)
        elif name == "br":
            continue  # already handled inside <p>; stray top-level <br>s are skip
        else:
            # Unknown top-level tag — treat as a paragraph if it has text.
            txt = _inline_text(child)
            if txt:
                yield txt


def extract_paragraphs(html: str) -> tuple[str | None, list[str]]:
    """
    Parse an HTML document and return (title, segments).

    Only <div class="text-normal f-text"> blocks are harvested. Any block
    that lives inside .self-answers, .answer_wrapper, .comments-tree, or
    any .comment is dropped (belt-and-braces — these classes shouldn't
    host .text-normal.f-text blocks, but we guard anyway so a future
    getcourse.ru template change can't leak student/comment text into
    the lecture output).

    Segments are emitted one-per-structural-unit: each <p>, <li>,
    <hN>, <blockquote> becomes its own entry. See module docstring
    for rationale and prefix conventions.
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

    segments: list[str] = []
    for block in soup.select("div.text-normal.f-text"):
        for seg in _emit_block(block):
            seg = seg.strip()
            if seg:
                segments.append(seg)
    return title, segments


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
