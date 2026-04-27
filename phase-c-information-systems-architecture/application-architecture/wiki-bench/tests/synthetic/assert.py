#!/usr/bin/env python3
"""
synthetic-test assertions — H-Q2 / H-Q5 / H-Q-plan.

Args:
  argv[1]: run dir containing events.jsonl
  argv[2]: wiki dir (final state of /workspace/wiki after agent run)
  argv[3]: served model name (informational)
  argv[4]: skill version (v1|v2) — affects which assertions are mandatory
  argv[5]: sources count (2|4) — number of expected source files

Exits 0 if all (mandatory) assertions pass, 1 otherwise.
"""
import json
import re
import sys
from pathlib import Path


GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREY = "\033[90m"
RESET = "\033[0m"


def status(ok, label, detail="", optional=False):
    if ok:
        mark = f"{GREEN}✓{RESET}"
    elif optional:
        mark = f"{YELLOW}-{RESET}"
    else:
        mark = f"{RED}✗{RESET}"
    print(f"  {mark} {label}")
    if detail:
        for line in detail.splitlines():
            print(f"      {line}")


def main():
    if len(sys.argv) < 4:
        print("usage: assert.py <run_dir> <wiki_dir> <served> [skill_v] [sources_n]", file=sys.stderr)
        sys.exit(2)

    run_dir = Path(sys.argv[1])
    wiki_dir = Path(sys.argv[2])
    served = sys.argv[3]
    skill_v = sys.argv[4] if len(sys.argv) > 4 else "v1"
    sources_n = int(sys.argv[5]) if len(sys.argv) > 5 else 2

    events_path = run_dir / "events.jsonl"
    events_text = events_path.read_text(encoding="utf-8") if events_path.exists() else ""

    print(f"\nmodel under test : {served}")
    print(f"skill version    : {skill_v}")
    print(f"sources expected : {sources_n}")
    print(f"events.jsonl     : {len(events_text)} bytes")
    print(f"wiki final       : {wiki_dir}")
    print()

    # ----------------------------------------------------------------
    # Tool inventory
    # ----------------------------------------------------------------
    print("--- tool inventory ---")
    name_pattern = re.findall(r'"tool_call":\s*{[^}]*?"name":\s*"([^"]+)"', events_text, re.S)
    if not name_pattern:
        name_pattern = re.findall(r'"name":\s*"([^"]+)"', events_text)
    seen = sorted(set(name_pattern))
    print(f"  tool_call.name values seen: {seen if seen else '(none)'}")
    print()

    # ----------------------------------------------------------------
    # Timeline — files / scripts the agent touched, in order
    # ----------------------------------------------------------------
    print("--- file/script access timeline ---")
    timeline = []

    # file_editor view & create on data/sources or scripts paths
    for m in re.finditer(
        r'"command":\s*"(view|create|str_replace)"[^}]*?"path":\s*"([^"]+)"',
        events_text):
        cmd, path = m.group(1), m.group(2)
        if "data/sources" in path or "scripts/" in path or "raw.json" in path or "SKILL.md" in path:
            timeline.append((m.start(), f"file_editor.{cmd}  {path}"))

    # terminal commands matching get_known_claims.py / factcheck.py / cat <source>
    for m in re.finditer(
        r'"command":\s*"((?:[^"\\]|\\.)*)"',  # arguments string
        events_text):
        cmd = m.group(1).replace('\\"', '"').replace("\\\\", "\\")
        if "get_known_claims.py" in cmd:
            timeline.append((m.start(), f"terminal: get_known_claims.py"))
        elif "factcheck.py" in cmd:
            arg = re.search(r'factcheck\.py\s+["\']?([^"\'|;&\\]{0,80})', cmd)
            timeline.append((m.start(), f"terminal: factcheck.py {arg.group(1).strip() if arg else ''}"))
        elif re.search(r"\b(?:cat|head|tail|less|more)\s+[^\\&|]*data/sources/", cmd):
            arg = re.search(r"data/sources/[^\s\"';|]+", cmd)
            timeline.append((m.start(), f"terminal: cat  {arg.group(0) if arg else '?'}"))

    timeline.sort(key=lambda t: t[0])
    if timeline:
        for _, line in timeline[:60]:
            print(f"  {GREY}•{RESET} {line[:140]}")
        if len(timeline) > 60:
            print(f"  ... +{len(timeline)-60} more")
    else:
        print(f"  {GREY}(no relevant file/script accesses){RESET}")
    print()

    results = []

    # ----------------------------------------------------------------
    # Discover final source files
    # ----------------------------------------------------------------
    src_files = sorted(
        [p for p in (wiki_dir / "data" / "sources").rglob("*.md") if not p.name.startswith("_")]
    )
    src_by_n = {}
    for p in src_files:
        m = re.match(r"(\d+)", p.name)
        if m:
            src_by_n[int(m.group(1))] = p

    # ----------------------------------------------------------------
    # A1 — H-Q2: agent attempted web fact-checking
    # ----------------------------------------------------------------
    web_tool_name = bool(re.search(
        r'"name":\s*"(?:web_search|browse|fetch|web_fetch|browser|tavily|serper|search)\b',
        events_text, re.I))
    factcheck_calls = len(re.findall(r'factcheck\.py', events_text))
    external_curl = bool(re.search(
        r'(?:curl|wget|urllib|http\.client)[^"]*?(?:wikipedia|britannica|wikidata|en\.|ru\.)',
        events_text, re.I))
    A1 = web_tool_name or external_curl or factcheck_calls > 0
    detail = (f"web_tool_name={web_tool_name}, factcheck.py_calls={factcheck_calls}, "
              f"external_http={external_curl}; tools={seen}")
    results.append(("A1 H-Q2: agent attempted web fact-checking", A1, detail, False))

    # ----------------------------------------------------------------
    # A2 — H-Q5: agent read prior source 001 BEFORE creating source 002
    # (only meaningful for sources_n >= 2)
    # ----------------------------------------------------------------
    pos_view_001 = None
    pos_create_002 = None

    m_view_001 = re.search(
        r'"command":\s*"view"[^}]*?"path":\s*"[^"]*data/sources/[^"]*?\b001\b',
        events_text)
    if m_view_001:
        pos_view_001 = m_view_001.start()
    if pos_view_001 is None:
        m_cat = re.search(
            r'(?:cat|head|tail|less|more)\s+[^"]*data/sources/[^"]*?\b001\b[^"]*\.md',
            events_text)
        if m_cat:
            pos_view_001 = m_cat.start()
    if pos_view_001 is None:
        # also count get_known_claims.py call as "reads prior 001 indirectly"
        m_gkc = re.search(r'get_known_claims\.py', events_text)
        if m_gkc:
            pos_view_001 = m_gkc.start()

    m_create_002 = re.search(
        r'"command":\s*"create"[^}]*?"path":\s*"[^"]*data/sources/[^"]*?\b002\b[^"]*\.md',
        events_text)
    if m_create_002:
        pos_create_002 = m_create_002.start()

    if pos_view_001 is None and pos_create_002 is None:
        A2 = False
        detail = "neither prior-source read nor source 002 create observed"
    elif pos_view_001 is None:
        A2 = False
        detail = f"source 002 created without any prior-source/inventory read"
    elif pos_create_002 is None:
        A2 = False
        detail = f"prior-source/inventory read happened but source 002 never created"
    else:
        A2 = pos_view_001 < pos_create_002
        detail = f"prior-read@{pos_view_001} {'<' if A2 else '>='} create_002@{pos_create_002}"
    results.append(("A2 H-Q5: agent read prior sources BEFORE creating source 002", A2, detail, False))

    # ----------------------------------------------------------------
    # A3 — H-Q5: source 002 has at least one REPEATED marker
    # ----------------------------------------------------------------
    src_002 = src_by_n.get(2)
    if src_002 is None:
        A3, detail = False, "source 002 article not produced"
    else:
        body = src_002.read_text(encoding="utf-8")
        A3 = bool(re.search(r"REPEATED", body))
        detail = f"file: {src_002.relative_to(wiki_dir)}; size: {len(body)}; REPEATED found: {A3}"
    results.append(("A3 H-Q5: source 002 marks ≥1 REPEATED claim", A3, detail, False))

    # ----------------------------------------------------------------
    # A4 — H-Q2: source 001 has URL citation
    # ----------------------------------------------------------------
    src_001 = src_by_n.get(1)
    if src_001 is None:
        A4, detail = False, "source 001 article not produced"
    else:
        body = src_001.read_text(encoding="utf-8")
        m = re.search(r"^## Claims[^\n]*\n(.*?)(?=\n## |\Z)", body, re.S | re.M)
        block = m.group(1) if m else body
        urls = re.findall(r"https?://[^\s)\]\"]+", block)
        A4 = len(urls) > 0
        detail = f"urls in Claims: {len(urls)}{'; first: ' + urls[0] if urls else ''}"
    results.append(("A4 H-Q2: source 001 has URL citation", A4, detail, False))

    # ----------------------------------------------------------------
    # A5 — H-Q2: source 001 catches Pareto-1950 fact error
    # ----------------------------------------------------------------
    if src_001 is None:
        A5, detail = False, "source 001 not produced"
    else:
        body = src_001.read_text(encoding="utf-8")
        has_cf = bool(re.search(r"CONTRADICTS\s+FACTS", body, re.I))
        has_pareto_1950 = bool(re.search(r"Парето.{0,200}1950|1950.{0,200}Парето", body, re.S))
        A5 = has_cf and has_pareto_1950
        detail = f"CONTRADICTS_FACTS marker: {has_cf}; Pareto-1950 claim present: {has_pareto_1950}"
    results.append(("A5 H-Q2: source 001 catches Pareto-1950 fact error", A5, detail, False))

    # ----------------------------------------------------------------
    # A6 — H-Q-plan / H-Q5: get_known_claims.py called ≥(N-1) times
    # (mandatory only if skill v2)
    # ----------------------------------------------------------------
    gkc_calls = len(re.findall(r'get_known_claims\.py', events_text))
    expected = max(0, sources_n - 1)
    A6 = gkc_calls >= expected
    detail = f"get_known_claims.py invocations: {gkc_calls} (expected ≥{expected} for {sources_n} sources)"
    optional6 = (skill_v == "v1")
    results.append(("A6 H-Q-plan: get_known_claims.py called per-source", A6, detail, optional6))

    # ----------------------------------------------------------------
    # A7 — H-Q-plan / H-Q2: factcheck.py called ≥4 times across run
    # (mandatory only if skill v2)
    # ----------------------------------------------------------------
    fc_calls = len(re.findall(r'factcheck\.py', events_text))
    A7 = fc_calls >= max(4, sources_n)  # rough: at least 1 empirical claim per source
    detail = f"factcheck.py invocations: {fc_calls}"
    optional7 = (skill_v == "v1")
    results.append(("A7 H-Q-plan: factcheck.py called for empirical claims", A7, detail, optional7))

    # ----------------------------------------------------------------
    # A8 — H-Q5: REPEATED markers reference real prior-source slugs
    # ----------------------------------------------------------------
    bad_slugs = []
    seen_slugs = set()
    # Collect all real source-article slugs (from frontmatter or filename)
    for p in src_files:
        body = p.read_text(encoding="utf-8")
        m = re.search(r"(?m)^slug:\s*(.+?)\s*$", body)
        if m:
            seen_slugs.add(m.group(1).strip())
        seen_slugs.add(p.stem)  # also accept stem
    # Find REPEATED (from: <slug>) markers and check
    for p in src_files:
        body = p.read_text(encoding="utf-8")
        for m in re.finditer(r"REPEATED\s*\(from:\s*([^)]+)\)", body):
            ref = m.group(1).strip()
            # Allow match against full slug OR ends-with stem
            ok = any(ref == s or s.endswith(ref) or ref.endswith(s) for s in seen_slugs)
            if not ok:
                bad_slugs.append((p.name, ref))
    A8 = len(bad_slugs) == 0
    detail = (f"REPEATED-slug references all valid: {A8}"
              + (f"; invalid: {bad_slugs[:3]}" if bad_slugs else ""))
    results.append(("A8 H-Q5: REPEATED markers reference real prior slugs", A8, detail, False))

    # ----------------------------------------------------------------
    # A9 — H-Q2: URLs are from Wikipedia
    # ----------------------------------------------------------------
    all_urls = []
    for p in src_files:
        body = p.read_text(encoding="utf-8")
        all_urls.extend(re.findall(r"https?://[^\s)\]\"]+", body))
    wiki_urls = [u for u in all_urls if "wikipedia.org" in u]
    A9 = len(all_urls) > 0 and (len(wiki_urls) / len(all_urls) > 0.5)
    detail = f"total urls: {len(all_urls)}; wikipedia urls: {len(wiki_urls)}"
    results.append(("A9 H-Q2: URL citations are Wikipedia-sourced", A9, detail, False))

    # ----------------------------------------------------------------
    # A10 — H-Q-plan: every source has all the required articles
    # ----------------------------------------------------------------
    expected_files = set(range(1, sources_n + 1))
    found_files = set(src_by_n.keys())
    missing = expected_files - found_files
    A10 = len(missing) == 0
    detail = f"expected sources: {sorted(expected_files)}; missing: {sorted(missing) if missing else '(none)'}"
    results.append(("A10 H-Q-plan: all expected source articles produced", A10, detail, False))

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print("--- assertions ---")
    for label, ok, detail, optional in results:
        status(ok, label, detail, optional=optional)

    mandatory = [r for r in results if not r[3]]
    passed = sum(1 for _, ok, _, _ in mandatory if ok)
    total = len(mandatory)
    print()
    print(f"summary: {passed}/{total} mandatory pass (skill={skill_v}, sources={sources_n})")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
