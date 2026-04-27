#!/usr/bin/env python3
"""
get_known_claims.py — list every claim from existing source articles.

The agent must call this BEFORE classifying a new source's claims —
otherwise it cannot know:
  (a) which claims have already appeared in earlier sources (REPEATED), and
  (b) what slugs to put in `REPEATED (from: <slug>)` markers.

Output: JSON to stdout.
{
  "count_sources": <int>,
  "count_claims": <int>,
  "sources": [
    {
      "slug": "<full slug>",
      "path": "<path relative to wiki root>",
      "claims": [
        {"n": 1, "marker": "NEW", "text": "..."},
        {"n": 2, "marker": "CONTRADICTS_FACTS", "text": "..."}
      ]
    },
    ...
  ]
}

Run from /workspace/wiki (the wiki working tree). No args.
"""
import json
import re
import sys
from pathlib import Path

WIKI_ROOT = Path.cwd()
if not (WIKI_ROOT / "data" / "sources").exists():
    print(json.dumps({"error": f"data/sources not under {WIKI_ROOT}"}), file=sys.stderr)
    sys.exit(2)


def parse_frontmatter_slug(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fm = text[4:end]
    m = re.search(r"(?m)^slug:\s*(.+?)\s*$", fm)
    return m.group(1) if m else None


MARKER_RE = re.compile(
    r"`?(NEW|REPEATED|CONTRADICTS\s+EARLIER|CONTRADICTS\s+FACTS)`?|"
    r"\[(NEW|REPEATED|CONTRADICTS\s+EARLIER|CONTRADICTS\s+FACTS)\]",
    re.I,
)


def extract_claims(body):
    m = re.search(r"(?m)^## Claims[^\n]*\n(.*?)(?=\n## |\Z)", body, re.S)
    if not m:
        return []
    block = m.group(1)
    items = re.findall(
        r"(?m)^(\d+)\.\s+(.*?)(?=\n\d+\.\s|\n## |\Z)", block, re.S
    )
    out = []
    for num, raw in items:
        marker_match = MARKER_RE.search(raw)
        if marker_match:
            marker = (marker_match.group(1) or marker_match.group(2)).upper().replace(" ", "_")
        else:
            marker = "UNMARKED"
        # Strip leading marker token from text
        text = MARKER_RE.sub("", raw, count=1).strip(" `—–-:.\n")
        out.append({"n": int(num), "marker": marker, "text": text[:500]})
    return out


sources = []
for p in sorted((WIKI_ROOT / "data" / "sources").rglob("*.md")):
    if p.name.startswith("_"):
        continue
    body = p.read_text(encoding="utf-8")
    slug = parse_frontmatter_slug(body) or str(p.relative_to(WIKI_ROOT / "data" / "sources").with_suffix(""))
    claims = extract_claims(body)
    sources.append({
        "slug": slug,
        "path": str(p.relative_to(WIKI_ROOT)),
        "claims": claims,
    })

result = {
    "count_sources": len(sources),
    "count_claims": sum(len(s["claims"]) for s in sources),
    "sources": sources,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
