#!/usr/bin/env python3
"""
bench-grade.py — Layer 0/1/2 quality metrics for kurpatov-wiki bench output.

Parses a clone of `kurpatov-wiki-wiki` on a bench branch (or main =
Opus baseline) and emits per-source / per-concept structural metrics
plus aggregate counts. No LLM needed.

Usage:
  python3 bench_grade.py <wiki_repo_path>
  python3 bench_grade.py <candidate_path> --compare-with <gold_path>

Exit code: 0 always (it's a measurement, not a gate).
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

import yaml


# The lecture section was renamed (2026-04-29) from
#   "## Лекция (пересказ: только NEW и проверенное)"
# to
#   "## Лекция сжато (только новое и проверенное)"
# Accept either spelling so old bench results stay graded. The new spelling
# also reframes the section as first-person condensed lecture, not retelling.
LECTURE_SECTION_HEADERS = [
    "## Лекция сжато (только новое и проверенное)",
    "## Лекция (пересказ: только NEW и проверенное)",
]
REQUIRED_SOURCE_SECTIONS = [
    "## TL;DR",
    LECTURE_SECTION_HEADERS,  # any-of
    "## Claims — provenance and fact-check",
    "## New ideas (verified)",
    "## All ideas",
]
REQUIRED_FRONTMATTER_FIELDS = [
    "slug", "course", "module", "extractor", "source_raw",
    "processed_at", "fact_check_performed",
    "concepts_touched", "concepts_introduced",
]
REQUIRED_CONCEPT_SECTIONS = ["## Definition"]


def parse_frontmatter(text: str):
    """Return (frontmatter_dict_or_None, body_str). Permissive."""
    if not text.startswith("---\n"):
        return None, text
    try:
        end = text.index("\n---\n", 4)
    except ValueError:
        return None, text
    fm_block = text[4:end]
    body = text[end + 5:]
    try:
        fm = yaml.safe_load(fm_block) or {}
    except yaml.YAMLError:
        return None, body
    return fm, body


# Marker classification for a single claim line.
# We tolerate two formats observed in the wild:
#   Opus:   "1. `NEW` — text"
#   Qwen:   "1. text [NEW] — explanation"
# So we look for the marker token anywhere in the line.
MARKER_PATTERNS = {
    # Accept both "CONTRADICTS FACTS" (space) and "CONTRADICTS_FACTS" (underscore)
    # as separators — skill v2 spec uses underscore but earlier prose used space.
    "CONTRADICTS_FACTS":   re.compile(r"`?CONTRADICTS[\s_]+FACTS`?|\[CONTRADICTS[\s_]+FACTS\]", re.I),
    "CONTRADICTS_EARLIER": re.compile(r"`?CONTRADICTS[\s_]+EARLIER\s*\([^)]*\)?`?|\[CONTRADICTS[\s_]+EARLIER", re.I),
    "REPEATED":            re.compile(r"`?REPEATED\s*\([^)]*\)?`?|\[REPEATED", re.I),
    "NEW":                 re.compile(r"`NEW`|\[NEW\]", re.I),
}
NOTES_FLAG = re.compile(r"⚠|\*?Notes\.?\*?", re.I)
URL_RE = re.compile(r"https?://[^\s)\]\"]+")


def classify_claim(line: str):
    """Return (marker, has_notes, num_urls). marker = first match priority order."""
    for marker in ("CONTRADICTS_FACTS", "CONTRADICTS_EARLIER", "REPEATED", "NEW"):
        if MARKER_PATTERNS[marker].search(line):
            return marker, bool(NOTES_FLAG.search(line)), len(URL_RE.findall(line))
    return None, bool(NOTES_FLAG.search(line)), len(URL_RE.findall(line))


def extract_section(body: str, header: str):
    """Return body of a section between `header` and the next `## ` header."""
    pat = re.compile(r"(?m)^" + re.escape(header) + r"\b.*$")
    m = pat.search(body)
    if not m:
        return None
    start = m.end()
    nxt = re.search(r"(?m)^## ", body[start:])
    end = start + nxt.start() if nxt else len(body)
    return body[start:end]


def parse_claims_section(text: str):
    """Yield (claim_num, body_line) for each numbered claim in the section."""
    if text is None:
        return
    for m in re.finditer(r"(?m)^(\d+)\.\s+(.*?)(?=\n\d+\.\s|\n## |\Z)", text, re.S):
        yield int(m.group(1)), m.group(2).strip()


def count_bullets(text: str):
    if text is None:
        return 0
    return len(re.findall(r"(?m)^\s*[-*]\s+", text))


def grade_source(path: Path):
    """Grade one source.md. Returns dict with metrics + violations."""
    raw = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    violations = []
    if fm is None:
        violations.append("frontmatter missing or unparseable")
        fm = {}

    for f in REQUIRED_FRONTMATTER_FIELDS:
        if f not in fm:
            violations.append(f"frontmatter missing field: {f}")

    for sec in REQUIRED_SOURCE_SECTIONS:
        if isinstance(sec, list):
            # any-of: pass if at least one alternative header is present
            if not any(re.search(r"(?m)^" + re.escape(alt), body) for alt in sec):
                violations.append(f"missing section: any of {sec}")
        else:
            if not re.search(r"(?m)^" + re.escape(sec), body):
                violations.append(f"missing section: {sec}")

    claims_block = extract_section(body, "## Claims — provenance and fact-check")
    new_ideas_block = extract_section(body, "## New ideas (verified)")
    all_ideas_block = extract_section(body, "## All ideas")
    # Try new header first, fall back to old.
    lecture_block = None
    for h in LECTURE_SECTION_HEADERS:
        lecture_block = extract_section(body, h)
        if lecture_block:
            break

    marker_counts = Counter()
    notes_count = 0
    citation_count = 0
    unmarked_claims = 0
    claim_idx = 0

    for num, claim_text in parse_claims_section(claims_block or ""):
        claim_idx += 1
        marker, has_notes, urls = classify_claim(claim_text)
        if marker is None:
            unmarked_claims += 1
        else:
            marker_counts[marker] += 1
        if has_notes:
            notes_count += 1
        citation_count += urls

    return {
        "path": str(path),
        "stem": path.stem,
        "frontmatter": {
            "slug": fm.get("slug"),
            "fact_check_performed": fm.get("fact_check_performed"),
            "concepts_touched_count": len(fm.get("concepts_touched") or []),
            "concepts_introduced_count": len(fm.get("concepts_introduced") or []),
        },
        "concepts_touched": list(fm.get("concepts_touched") or []),
        "concepts_introduced": list(fm.get("concepts_introduced") or []),
        "metrics": {
            "claims_total": claim_idx,
            "claims_unmarked": unmarked_claims,
            "claims_NEW": marker_counts["NEW"],
            "claims_REPEATED": marker_counts["REPEATED"],
            "claims_CONTRADICTS_EARLIER": marker_counts["CONTRADICTS_EARLIER"],
            "claims_CONTRADICTS_FACTS": marker_counts["CONTRADICTS_FACTS"],
            "notes_flagged": notes_count,
            "fact_check_citations": citation_count,
            "new_ideas_bullets": count_bullets(new_ideas_block),
            "all_ideas_bullets": count_bullets(all_ideas_block),
            "lecture_words": len((lecture_block or "").split()),
        },
        "violations": violations,
    }


def grade_concept(path: Path):
    raw = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)
    violations = []
    if fm is None:
        violations.append("frontmatter missing or unparseable")
        fm = {}
    if "slug" not in fm:
        violations.append("frontmatter missing field: slug")
    if "touched_by" not in fm:
        violations.append("frontmatter missing field: touched_by")
    for sec in REQUIRED_CONCEPT_SECTIONS:
        if not re.search(r"(?m)^" + re.escape(sec), body):
            violations.append(f"missing section: {sec}")
    contributions_block = extract_section(body, "## Contributions by source")
    contrib_subs = re.findall(r"(?m)^### ", contributions_block or "") if contributions_block else []

    # L1.5: canonical skill v2 concept shape (per wiki:prompts/concept-article.md).
    # Soft layer — surface violations, do not change pass/fail.
    touched_by = list(fm.get("touched_by") or [])
    v15_violations = []
    if touched_by:
        if "## Contributions by source" not in body:
            v15_violations.append("L1.5: ## Contributions by source missing")
        else:
            sub_pat = re.compile(
                r"(?ms)^### (\S.*?)\n(.*?)(?=\n### |\n## |\Z)"
            )
            subs = sub_pat.findall(contributions_block or "")
            if len(subs) < len(touched_by):
                v15_violations.append(
                    f"L1.5: {len(subs)} ### sub-sections vs {len(touched_by)} touched_by entries"
                )
            for slug_line, sub_body in subs:
                if len(sub_body.strip()) < 30:
                    v15_violations.append(
                        f"L1.5: ### sub-section for {slug_line[:40]} too short"
                    )
        if "first_introduced_in" not in fm:
            v15_violations.append("L1.5: frontmatter missing first_introduced_in")
    violations.extend(v15_violations)

    return {
        "path": str(path),
        "slug": path.stem,
        "frontmatter": {
            "slug": fm.get("slug"),
            "first_introduced_in": fm.get("first_introduced_in"),
            "touched_by_count": len(fm.get("touched_by") or []),
        },
        "touched_by": list(fm.get("touched_by") or []),
        "metrics": {
            "definition_present": "## Definition" in body,
            "contributions_count": len(contrib_subs),
            "body_lines": len(body.splitlines()),
        },
        "violations": violations,
    }


def grade_repo(repo: Path):
    """Grade one bench-branch checkout: data/sources/* + data/concepts/* + concept-index.json."""
    sources_root = repo / "data" / "sources"
    concepts_root = repo / "data" / "concepts"
    index_path = repo / "data" / "concept-index.json"

    sources = []
    if sources_root.exists():
        for src in sorted(sources_root.rglob("*.md")):
            if src.stem.startswith("_"):
                continue
            sources.append(grade_source(src))

    concepts = []
    if concepts_root.exists():
        for c in sorted(concepts_root.glob("*.md")):
            if c.name.startswith("_"):
                continue
            concepts.append(grade_concept(c))

    index = None
    index_violations = []
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            index_violations.append(f"concept-index.json parse error: {e}")

    # Cross-references
    concept_files = {c["slug"] for c in concepts}
    cross_violations = []

    for src in sources:
        for slug in src["concepts_touched"]:
            if slug not in concept_files:
                cross_violations.append(f"{src['stem']}: concepts_touched references missing concept '{slug}'")
        intr = set(src["concepts_introduced"])
        touched = set(src["concepts_touched"])
        if not intr.issubset(touched):
            extra = intr - touched
            cross_violations.append(f"{src['stem']}: concepts_introduced not subset of concepts_touched (extras: {sorted(extra)})")

    if index is not None:
        idx_processed = {p["slug"] if isinstance(p, dict) else p for p in index.get("processed_sources", [])}
        idx_concepts = set((index.get("concepts") or {}).keys())
        for src in sources:
            if src["frontmatter"]["slug"] not in idx_processed:
                cross_violations.append(f"{src['stem']}: source slug not in concept-index.processed_sources")
        for slug in concept_files - idx_concepts:
            cross_violations.append(f"concept '{slug}' present as file but missing from concept-index.concepts")
        for slug in idx_concepts - concept_files:
            cross_violations.append(f"concept '{slug}' in index but no data/concepts/<slug>.md file")

    aggregate = {
        "sources_count": len(sources),
        "concepts_count": len(concepts),
        "claims_total_sum": sum(s["metrics"]["claims_total"] for s in sources),
        "claims_NEW_sum": sum(s["metrics"]["claims_NEW"] for s in sources),
        "claims_REPEATED_sum": sum(s["metrics"]["claims_REPEATED"] for s in sources),
        "claims_CONTRADICTS_EARLIER_sum": sum(s["metrics"]["claims_CONTRADICTS_EARLIER"] for s in sources),
        "claims_CONTRADICTS_FACTS_sum": sum(s["metrics"]["claims_CONTRADICTS_FACTS"] for s in sources),
        "claims_unmarked_sum": sum(s["metrics"]["claims_unmarked"] for s in sources),
        "notes_flagged_sum": sum(s["metrics"]["notes_flagged"] for s in sources),
        "fact_check_citations_sum": sum(s["metrics"]["fact_check_citations"] for s in sources),
        "fact_check_performed_count": sum(1 for s in sources if s["frontmatter"]["fact_check_performed"]),
        "lecture_words_sum": sum(s["metrics"]["lecture_words"] for s in sources),
        "all_violations_count": (
            sum(len(s["violations"]) for s in sources) +
            sum(len(c["violations"]) for c in concepts) +
            len(index_violations) + len(cross_violations)
        ),
    }

    return {
        "repo": str(repo),
        "aggregate": aggregate,
        "sources": sources,
        "concepts_count_by_definition_present": sum(1 for c in concepts if c["metrics"]["definition_present"]),
        "concept_violations": [c for c in concepts if c["violations"]],
        "index_violations": index_violations,
        "cross_violations": cross_violations,
    }


def fmt_per_source(grade, label):
    print(f"\n=== {label}: per-source ===")
    print(f"{'src':<8} {'tcl':>5} {'NEW':>4} {'REP':>4} {'CE':>3} {'CF':>3} {'unm':>4} "
          f"{'⚠':>3} {'cit':>4} {'ct':>3} {'ci':>3} {'lec.w':>6} {'viols':>6}")
    for s in grade["sources"]:
        m = s["metrics"]
        f = s["frontmatter"]
        stem = s["stem"][:8]
        print(f"{stem:<8} {m['claims_total']:>5} {m['claims_NEW']:>4} "
              f"{m['claims_REPEATED']:>4} {m['claims_CONTRADICTS_EARLIER']:>3} "
              f"{m['claims_CONTRADICTS_FACTS']:>3} {m['claims_unmarked']:>4} "
              f"{m['notes_flagged']:>3} {m['fact_check_citations']:>4} "
              f"{f['concepts_touched_count']:>3} {f['concepts_introduced_count']:>3} "
              f"{m['lecture_words']:>6} {len(s['violations']):>6}")


def fmt_aggregate(grade, label):
    a = grade["aggregate"]
    print(f"\n=== {label}: aggregate ===")
    for k, v in a.items():
        print(f"  {k:<35} {v}")


def fmt_violations(grade, label):
    print(f"\n=== {label}: violations ===")
    n = 0
    for s in grade["sources"]:
        for v in s["violations"]:
            print(f"  source[{s['stem'][:30]}]: {v}")
            n += 1
    for c in grade["concept_violations"]:
        for v in c["violations"]:
            print(f"  concept[{c['slug']}]: {v}")
            n += 1
    for v in grade["index_violations"]:
        print(f"  index: {v}")
        n += 1
    for v in grade["cross_violations"]:
        print(f"  cross-ref: {v}")
        n += 1
    if n == 0:
        print("  (none)")


def fmt_compare(cand, gold):
    a, b = cand["aggregate"], gold["aggregate"]
    print("\n=== compare candidate vs gold (Δ = cand − gold) ===")
    rows = [
        ("sources_count", a["sources_count"], b["sources_count"]),
        ("concepts_count", a["concepts_count"], b["concepts_count"]),
        ("claims_total_sum", a["claims_total_sum"], b["claims_total_sum"]),
        ("claims_NEW_sum", a["claims_NEW_sum"], b["claims_NEW_sum"]),
        ("claims_REPEATED_sum", a["claims_REPEATED_sum"], b["claims_REPEATED_sum"]),
        ("claims_CONTRADICTS_EARLIER_sum", a["claims_CONTRADICTS_EARLIER_sum"], b["claims_CONTRADICTS_EARLIER_sum"]),
        ("claims_CONTRADICTS_FACTS_sum", a["claims_CONTRADICTS_FACTS_sum"], b["claims_CONTRADICTS_FACTS_sum"]),
        ("claims_unmarked_sum", a["claims_unmarked_sum"], b["claims_unmarked_sum"]),
        ("notes_flagged_sum", a["notes_flagged_sum"], b["notes_flagged_sum"]),
        ("fact_check_citations_sum", a["fact_check_citations_sum"], b["fact_check_citations_sum"]),
        ("fact_check_performed_count", a["fact_check_performed_count"], b["fact_check_performed_count"]),
        ("lecture_words_sum", a["lecture_words_sum"], b["lecture_words_sum"]),
        ("violations", a["all_violations_count"], b["all_violations_count"]),
    ]
    print(f"  {'metric':<35} {'cand':>8} {'gold':>8} {'Δ':>8} {'%':>8}")
    for name, x, y in rows:
        delta = x - y
        pct = (x / y * 100) if y else float("inf") if x else 0.0
        print(f"  {name:<35} {x:>8} {y:>8} {delta:>+8} {pct:>7.0f}%")

    # Concept slug coverage: which Opus concepts are missing from candidate?
    cand_slugs = {c["slug"] for c in cand_concepts}
    gold_slugs = {c["slug"] for c in gold_concepts}
    missing_in_cand = sorted(gold_slugs - cand_slugs)
    extra_in_cand = sorted(cand_slugs - gold_slugs)
    print(f"\n  concepts in gold not in candidate ({len(missing_in_cand)}):")
    for s in missing_in_cand[:50]:
        print(f"    - {s}")
    if len(missing_in_cand) > 50:
        print(f"    ... +{len(missing_in_cand) - 50} more")
    if extra_in_cand:
        print(f"  concepts in candidate not in gold ({len(extra_in_cand)}):")
        for s in extra_in_cand[:20]:
            print(f"    + {s}")



def grade_single_source_stem_json(repo: Path, stem: str, module_subdir: str = ""):
    """Grade a single source identified by its directory stem (e.g.
    `000 № 1. Вводная лекция о дисциплине`). Preferred entry point
    for multi-module pilots — no numeric-prefix coupling.
    """
    sources_root = repo / "data" / "sources"
    if module_subdir:
        sources_root = sources_root / module_subdir
    if not sources_root.exists():
        out = {"verified": "fail", "violations": [f"no sources root at {sources_root}"]}
        print(json.dumps(out, ensure_ascii=False))
        return
    target = f"{stem}.md"
    matches = [m for m in sources_root.rglob(target) if m.name == target]
    matches = [m for m in matches if not m.name.startswith("_template")]
    if not matches:
        out = {"verified": "fail", "violations": [f"no source file matching stem {stem!r}"]}
        print(json.dumps(out, ensure_ascii=False))
        return
    if len(matches) > 1:
        out = {"verified": "fail", "violations": [f"multiple source files matching stem {stem!r}: {[str(m) for m in matches]}"]}
        print(json.dumps(out, ensure_ascii=False))
        return
    src_path = matches[0]
    g = grade_source(src_path)
    commit_sha = None
    try:
        import subprocess
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            commit_sha = r.stdout.strip()
    except Exception:
        pass
    g["commit_sha"] = commit_sha
    g["source_file"] = str(src_path.relative_to(repo))
    if "violations" in g and g["violations"]:
        g["verified"] = "fail"
    else:
        g["verified"] = "ok"
    print(json.dumps(g, ensure_ascii=False))


def grade_single_source_json(repo: Path, source_n: int, module_subdir: str = ""):
    """
    Find the source-N file in the repo (matches files starting with `<NNN> `
    under data/sources/<module-subdir>/), grade it, and emit the D7-rev3
    verify-script contract JSON to stdout.

    module_subdir scopes the rglob to a single module path so that
    multi-module pilots don't match same-numbered files across modules.
    """
    sources_root = repo / "data" / "sources"
    if module_subdir:
        sources_root = sources_root / module_subdir
    if not sources_root.exists():
        out = {"verified": "fail", "violations": [f"no sources root at {sources_root}"]}
        print(json.dumps(out, ensure_ascii=False))
        return

    prefix = f"{source_n:03d} "
    matches = [m for m in sources_root.rglob(f"{prefix}*.md") if m.stem.startswith(prefix)]
    # Filter out _template
    matches = [m for m in matches if not m.name.startswith("_template")]
    if not matches:
        out = {"verified": "fail", "violations": [f"no source file matching '{prefix}*.md'"]}
        print(json.dumps(out, ensure_ascii=False))
        return
    if len(matches) > 1:
        out = {"verified": "fail", "violations": [f"multiple source files matching '{prefix}*.md': {[str(m) for m in matches]}"]}
        print(json.dumps(out, ensure_ascii=False))
        return

    src_path = matches[0]
    g = grade_source(src_path)

    # Try to get current commit_sha of the repo HEAD
    commit_sha = None
    try:
        import subprocess
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            commit_sha = r.stdout.strip()
    except Exception:
        pass

    metrics = g["metrics"]
    violations = list(g["violations"])

    sections_count = 0
    body_text = src_path.read_text(encoding="utf-8")
    for sec in REQUIRED_SOURCE_SECTIONS:
        if re.search(r"(?m)^" + re.escape(sec), body_text):
            sections_count += 1

    has_claims_section = "## Claims" in body_text
    frontmatter_ok = (g["frontmatter"]["slug"] is not None and
                      g["frontmatter"]["fact_check_performed"] is not None)

    # Decision rule
    verified = "ok" if (
        frontmatter_ok
        and sections_count >= 5
        and has_claims_section
        and metrics["claims_total"] > 0
        and metrics["claims_unmarked"] == 0
    ) else "fail"

    out = {
        "verified": verified,
        "commit_sha": commit_sha,
        "source_file": str(src_path.relative_to(repo)),
        "frontmatter_ok": frontmatter_ok,
        "sections_count": sections_count,
        "has_claims_section": has_claims_section,
        "claims_total": metrics["claims_total"],
        "claims_NEW": metrics["claims_NEW"],
        "claims_REPEATED": metrics["claims_REPEATED"],
        "claims_CF": metrics["claims_CONTRADICTS_FACTS"],
        "claims_unmarked": metrics["claims_unmarked"],
        "wiki_url_count": metrics["fact_check_citations"],
        "concepts_introduced_count": g["frontmatter"]["concepts_introduced_count"],
        "violations": violations,
    }
    print(json.dumps(out, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("repo", help="path to a kurpatov-wiki-wiki checkout (bench branch)")
    p.add_argument("--compare-with", help="path to gold checkout (e.g. opus baseline)")
    p.add_argument("--json", help="write per-source/aggregate JSON to this path")
    p.add_argument("--single-source", type=int, metavar="N", help="grade a single source by index (e.g. 5 for `005 ...`)")
    p.add_argument("--module-subdir", type=str, default="", help="scope --single-source search to data/sources/<module-subdir>/ (Course/Module path), to disambiguate same-index sources across modules")
    p.add_argument("--single-source-stem", type=str, default="", metavar="STEM", help="grade a single source by its directory stem (e.g. `000 № 1. Вводная лекция о дисциплине`). Preferred over --single-source for multi-module pilots; identifies the source unambiguously without relying on numeric-prefix conventions.")
    p.add_argument("--single-source-json", action="store_true", help="emit D7-rev3 verify-script contract JSON to stdout for the --single-source target")
    args = p.parse_args()

    if args.single_source_stem and args.single_source_json:
        grade_single_source_stem_json(Path(args.repo), args.single_source_stem, args.module_subdir)
        return
    if args.single_source is not None and args.single_source_json:
        grade_single_source_json(Path(args.repo), args.single_source, args.module_subdir)
        return

    cand = grade_repo(Path(args.repo))
    fmt_aggregate(cand, "candidate")
    fmt_per_source(cand, "candidate")
    fmt_violations(cand, "candidate")

    if args.json:
        Path(args.json).write_text(json.dumps(cand, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")

    if args.compare_with:
        global cand_concepts, gold_concepts  # for fmt_compare
        gold = grade_repo(Path(args.compare_with))
        fmt_aggregate(gold, "gold")
        fmt_per_source(gold, "gold")
        # build concept lists for slug coverage
        cand_concepts = [{"slug": Path(p).stem} for p in
                         sorted((Path(args.repo) / "data" / "concepts").glob("*.md"))]
        gold_concepts = [{"slug": Path(p).stem} for p in
                         sorted((Path(args.compare_with) / "data" / "concepts").glob("*.md"))]
        fmt_compare(cand, gold)


if __name__ == "__main__":
    main()
