#!/usr/bin/env python3
"""
synthetic-test assertions — H-Q2 (web search) + H-Q5 (prior-source read).

Args:
  argv[1]: run dir containing events.jsonl
  argv[2]: wiki dir (final state of /workspace/wiki after agent run)
  argv[3]: served model name (informational)

Exits 0 if all assertions pass, 1 otherwise.
"""
import json
import re
import sys
from pathlib import Path


GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def status(ok, label, detail=""):
    color = GREEN if ok else RED
    mark = "✓" if ok else "✗"
    print(f"  {color}{mark}{RESET} {label}")
    if detail:
        for line in detail.splitlines():
            print(f"      {line}")


def warn(label, detail=""):
    print(f"  {YELLOW}!{RESET} {label}")
    if detail:
        for line in detail.splitlines():
            print(f"      {line}")


def main():
    if len(sys.argv) < 3:
        print("usage: assert.py <run_dir> <wiki_dir> [served_name]", file=sys.stderr)
        sys.exit(2)

    run_dir = Path(sys.argv[1])
    wiki_dir = Path(sys.argv[2])
    served = sys.argv[3] if len(sys.argv) > 3 else "?"

    events_path = run_dir / "events.jsonl"
    events_text = events_path.read_text(encoding="utf-8") if events_path.exists() else ""

    print(f"\nmodel under test: {served}")
    print(f"events.jsonl   : {len(events_text)} bytes")
    print(f"wiki final     : {wiki_dir}")
    print()

    # ----------------------------------------------------------------
    # Tool inventory — what tools did the agent emit calls for?
    # ----------------------------------------------------------------
    print("--- tool inventory ---")
    tool_call_names = re.findall(r'"name":\s*"([^"]+)"', events_text)
    # filter to plausible tool-name set: only those that appear inside a tool_call block
    name_pattern = re.findall(r'"tool_call":\s*{[^}]*?"name":\s*"([^"]+)"', events_text, re.S)
    if not name_pattern:
        # fallback to any "name":"..." occurrence
        name_pattern = tool_call_names
    seen = sorted(set(name_pattern))
    print(f"  tool_call.name values seen: {seen if seen else '(none)'}")
    print()

    results = []

    # ----------------------------------------------------------------
    # A1 — H-Q2: agent attempted web fact-checking
    # ----------------------------------------------------------------
    web_tool_name = bool(re.search(
        r'"name":\s*"(?:web_search|browse|fetch|web_fetch|browser|tavily|serper|search)\b',
        events_text, re.I))
    # external curl/wget in terminal commands (not localhost / not inference / not GitHub auth)
    external_curl = bool(re.search(
        r'(?:curl|wget)[^"]*?https?://(?!localhost|127\.|inference\.|github\.com|api\.github)\S+',
        events_text, re.I))
    A1 = web_tool_name or external_curl
    detail = (f"web_tool_name={web_tool_name}, external_curl={external_curl}; "
              f"tools_seen={seen}")
    results.append(("A1 H-Q2: agent attempted web fact-checking", A1, detail))

    # ----------------------------------------------------------------
    # A2 — H-Q5: agent read source 001 article BEFORE creating source 002
    # ----------------------------------------------------------------
    # Find file_editor commands (view/cat) that reference 001 file path,
    # AND find the create of 002 file path. Compare positions.
    # We look at order in events.jsonl (timestamps would be more precise
    # but stream order is sufficient).
    pos_view_001 = None
    pos_create_002 = None

    # Look for file_editor.view of 001 article
    m_view_001 = re.search(
        r'"command":\s*"view"[^}]*?"path":\s*"[^"]*data/sources/[^"]*?001[^"]*"',
        events_text)
    if m_view_001:
        pos_view_001 = m_view_001.start()
    else:
        # Check for terminal cat of source 001 article (anywhere on path)
        m_cat = re.search(
            r'(?:cat|less|more|head|tail)\s+[^"]*data/sources/[^"]*?001[^"]*\.md',
            events_text)
        if m_cat:
            pos_view_001 = m_cat.start()

    # Look for file_editor.create of 002 article
    m_create_002 = re.search(
        r'"command":\s*"create"[^}]*?"path":\s*"[^"]*data/sources/[^"]*?002[^"]*\.md',
        events_text)
    if m_create_002:
        pos_create_002 = m_create_002.start()

    if pos_view_001 is None and pos_create_002 is None:
        A2 = False
        detail = "neither source 001 viewed nor source 002 created — agent didn't get that far"
    elif pos_view_001 is None and pos_create_002 is not None:
        A2 = False
        detail = f"source 002 was created (pos={pos_create_002}) without ever viewing source 001"
    elif pos_view_001 is not None and pos_create_002 is None:
        A2 = False
        detail = f"source 001 was viewed (pos={pos_view_001}) but source 002 was never created"
    else:
        A2 = pos_view_001 < pos_create_002
        detail = f"view_001@{pos_view_001} {'<' if A2 else '>='} create_002@{pos_create_002}"
    results.append(("A2 H-Q5: agent read source 001 BEFORE creating source 002", A2, detail))

    # ----------------------------------------------------------------
    # A3 — H-Q5: final source 002 article contains REPEATED marker
    # ----------------------------------------------------------------
    src_002_files = list((wiki_dir / "data" / "sources").rglob("*.md"))
    src_002 = next((p for p in src_002_files if "002" in p.name), None)

    if src_002 is None:
        A3 = False
        detail_a3 = f"source 002 article not found under {wiki_dir}/data/sources/"
    else:
        body = src_002.read_text(encoding="utf-8")
        # accept multiple marker formats
        A3 = bool(re.search(r"REPEATED", body))
        detail_a3 = (f"file: {src_002.relative_to(wiki_dir)}; "
                     f"size: {len(body)} bytes; "
                     f"REPEATED marker found: {A3}")
    results.append(("A3 H-Q5: source 002 marks at least one REPEATED claim", A3, detail_a3))

    # ----------------------------------------------------------------
    # A4 — H-Q2: source 001 contains URL citation in Claims
    # ----------------------------------------------------------------
    src_001 = next((p for p in src_002_files if "001" in p.name), None)
    if src_001 is None:
        A4 = False
        detail_a4 = "source 001 article not found"
    else:
        body = src_001.read_text(encoding="utf-8")
        # extract Claims section (## Claims to next ## or EOF)
        m = re.search(r"^## Claims[^\n]*\n(.*?)(?=\n## |\Z)", body, re.S | re.M)
        claims_block = m.group(1) if m else body
        urls = re.findall(r"https?://[^\s)\]\"]+", claims_block)
        A4 = len(urls) > 0
        detail_a4 = (f"file: {src_001.relative_to(wiki_dir)}; "
                     f"urls in Claims: {len(urls)}{'; first: ' + urls[0] if urls else ''}")
    results.append(("A4 H-Q2: source 001 has URL citation in Claims", A4, detail_a4))

    # ----------------------------------------------------------------
    # A5 — H-Q2: source 001 marks Pareto-1950 claim with CONTRADICTS_FACTS
    # ----------------------------------------------------------------
    if src_001 is None:
        A5 = False
        detail_a5 = "source 001 article not found"
    else:
        body = src_001.read_text(encoding="utf-8")
        # find any line/bullet containing both "1950" or "год" near "Парето"
        # AND the CONTRADICTS FACTS marker
        has_cf = bool(re.search(r"CONTRADICTS\s+FACTS", body, re.I))
        has_pareto_1950 = bool(re.search(r"Парето.{0,200}1950|1950.{0,200}Парето", body, re.S))
        A5 = has_cf and has_pareto_1950
        detail_a5 = (f"CONTRADICTS_FACTS marker present: {has_cf}; "
                     f"Pareto-1950 claim present: {has_pareto_1950}")
    results.append(("A5 H-Q2: source 001 catches Pareto-1950 fact error", A5, detail_a5))

    # ----------------------------------------------------------------
    # Print summary
    # ----------------------------------------------------------------
    print("--- assertions ---")
    for label, ok, detail in results:
        status(ok, label, detail)

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print()
    print(f"summary: {passed}/{total} pass")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
