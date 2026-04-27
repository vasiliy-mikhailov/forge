"""
Step 7 — Python-loop top-orchestrator + concept template v3 smoke (D8 Step 0+0.2).

Validates TWO lab-wide invariants together on synthetic fixtures:

INVARIANT A: top-orchestrator context MUST NOT grow across sources.
  Encoded via: fresh `Conversation` per source (Python `for` loop).
  Asserted via: per-source events ≤ 30, per-source input tokens ≤ 100K,
                cumulative scales O(N) not O(N²).

INVARIANT B: every concept article MUST contain `## Touched in sources`
             with one entry per `touched_by` source, each entry having
             a clickable backlink and a 30-400-char excerpt.
  Encoded via: extended concept-curator prompt + source-author passes
               `touched_by_excerpts` per concept.
  Asserted via: regex over each concept .md, link target must exist.

Both invariants come out of D7-rev4-v2 audit (2026-04-26):
  - INVARIANT A — top-orch hit attention ceiling at 5/7 sources
    because TaskToolSet returns accumulated in single Conversation.
  - INVARIANT B — skill v2 SKILL.md never specified concept structure;
    my D7-rev3 minimum template was navigation dead-end.

Functional pass criteria (matches step5d_rev_v2 GREEN, raised slightly):
  - 4/4 synth sources verified=ok
  - claims_total ≥ 20, REPEATED ≥ 2
  - canonical concept template OK (frontmatter + ## Definition)
  - **NEW** every concept has ## Touched in sources with valid bullets

Architectural pass criteria (the new gate):
  - per-source top-orch events ≤ 30
  - per-source top-orch input tokens ≤ 100K (when SDK reports)
  - cumulative top-orch input scales O(N) — each source ≤ 2× avg
"""
import os, re, sys, json, subprocess
from pathlib import Path

from openhands.sdk import (
    LLM, Agent, Conversation, Tool,
    register_agent, agent_definition_to_factory,
)
from openhands.sdk.subagent import AgentDefinition
from openhands.sdk.tool import register_tool
from openhands.tools.task import TaskToolSet
from openhands.tools.delegate import DelegationVisualizer


WS = Path("/tmp/step7-orch-ws")
WIKI = WS / "wiki"
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"
SOURCE_NUMBERS = [1, 2, 3, 4]

# Per-source bounds — see openhands-sdk-orchestration.md
TOP_ORCH_INPUT_TOKENS_PER_SOURCE_LIMIT = 100_000
TOP_ORCH_EVENTS_PER_SOURCE_LIMIT = 30

# Concept template v3 bounds — see concept-template-v3.md
EXCERPT_MIN_CHARS = 30
EXCERPT_MAX_CHARS = 400


# ─── Sub-agent prompts ──────────────────────────────────────────────────

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim, lecture_transcript, prior_claims_json.

Step 1: Decide NEW vs REPEATED based on prior_claims_json.
Step 2: Pick a thematic_category.
Output ONE LINE: `<verdict> | category=<thematic-tag>`. Then call finish.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Each task contains: claim, lecture_transcript.

Step 1: `cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"`
Step 2: Pick BEST matching Wikipedia URL.
Step 3: Compose verdict + Notes.
Output 3 lines: marker / url / notes. Then call finish.
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator (template v3 — backlinks + excerpts).

Task message contains:
  - concept_slug
  - definition (one paragraph in Russian)
  - source_slug (the source CALLING you NOW)
  - lecture_transcript (this source's transcript)
  - related_concepts (list of slugs)
  - this_source_excerpt (string, 1-3 sentences from THIS source about
    THIS concept; min 30 chars)
  - this_source_timestamp_sec (int or null; e.g. 1842 for ≈ 30:42)

Workflow:
1. Use terminal `ls wiki/data/concepts/<concept_slug>.md` to check exists.
2. **If NEW** (file does not exist):
   Use file_editor (with ABSOLUTE path) to CREATE with this v3 template:

   ```
   ---
   slug: <concept_slug>
   introduced_in: <source_slug>
   touched_by:
     - <source_slug>
   related:
     - <related-slug-1>
     - <related-slug-2>
   ---
   # <Russian title derived from definition>

   ## Definition

   <2-3 paragraphs grounded in lecture content with «...» quotes>

   ## Touched in sources

   - [<short label = last 60 chars of source_slug>](../sources/<source_slug>.md)
     <this_source_excerpt verbatim>
     [≈ <MM:SS converted from this_source_timestamp_sec>]

   ## See also

   - <related-1> — <one-line>
   - <related-2> — <one-line>
   ```

   Then append concept_slug to wiki/data/concept-index.json.

3. **If EXISTS** (file already exists):
   Use file_editor view + str_replace to APPEND a new bullet to the
   existing `## Touched in sources` section. New bullet at the end of
   that section, BEFORE `## See also`.

   New bullet format same as above.
   ALSO update frontmatter `touched_by:` list to include
   <source_slug> (append, no duplicates).

4. Output `concept <slug> ready` and finish.

Rules:
- Excerpt MUST be ≥30 chars (excluding the `[≈ ...]` annotation).
- If `this_source_timestamp_sec` is null, omit the `[≈ ...]` line entirely.
- file_editor needs ABSOLUTE paths — prefix with workspace pwd.
- Stay deterministic on existing concepts: don't rewrite ## Definition
  or ## See also when the file exists; only append the new touched-by entry.
"""

SOURCE_AUTHOR_PROMPT = """\
You are source-author (D8 Step 0+0.2 — produces concept-curator input
with per-source excerpts).

Task message: source_n, raw_path, target_path.

Tools: terminal, file_editor, task, finish, think.
Subagent_types for task(): idea-classifier, fact-checker, concept-curator.

## Workflow

### A. Read transcript + segments
```
python3 -c "import json,sys; d=json.load(open('<raw_path>')); print(json.dumps({'segments': d['segments'], 'duration': int(d['info']['duration'])}))"
```
Save segments list (each has start, end, text).

### B. Get known claims
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```

### C. Extract claims (LLM reasoning)
For EACH claim: pick concept slugs (kebab-case), assign needs_factcheck.

### D. Per-claim sub-agent calls — record marker for EACH claim
For claim i (sequential):
  1. ALWAYS task(idea-classifier, ...) → parse `<verdict> | category=<theme>`
  2. IF needs_factcheck[i]: task(fact-checker, ...) → parse marker/url/notes

  Combine into final_marker[i]:
    - factchecker said CONTRADICTS_FACTS → `[CONTRADICTS_FACTS]`
    - elif classifier said REPEATED      → `[REPEATED (from: <slug>)]`
    - else                                → `[NEW]`

  ⚠️ Persist (claim_text, final_marker, url, notes, thematic_category)
     for every claim — you will need ALL of these in step F.

### E. Concept curator calls (per new concept):
For each NEW concept (not in prior_claims_json):
  - Find the FIRST segment whose `text` mentions concept slug or its
    Russian title. Take its `text` (≤400 chars) as `excerpt`, its
    `start` (round int) as `timestamp_sec`.
  - task(concept-curator, prompt with: concept_slug, definition (1 para),
    source_slug, lecture_transcript, related_concepts, this_source_excerpt,
    this_source_timestamp_sec)

### F. Assemble source.md (CRITICAL — write to target_path)

Frontmatter (between --- fences, FIRST):
  slug: <drop "wiki/data/sources/" + ".md" from target_path>
  course / module / extractor / source_raw / duration_sec / language /
  processed_at: 2026-04-26T00:00:00Z / fact_check_performed: true
  concepts_touched: [<all 5+ slugs from claims>]
  concepts_introduced: [<STRICT subset: only first-mentioned-here>]

Body — EXACTLY 5 `## ` sections in order. Use `# <Title>` for H1.

  `## TL;DR` — paragraph
  `## Лекция (пересказ: только NEW и проверенное)` — 3-5 paragraphs
    with inline `[<concept-slug>](../../../concepts/<slug>.md)` links
  `## Claims — provenance and fact-check` — numbered list. EVERY entry:
       `<n>. <claim_text> <final_marker[n]>`
       <notes paragraph if fact-checked>
       — <url> (if factchecker provided)
    🔴 EVERY claim MUST end with one of `[NEW]`, `[REPEATED (from: ...)]`,
       or `[CONTRADICTS_FACTS]`. NO bare claims allowed.
  `## New ideas (verified)` — bullets, grouped by thematic_category
  `## All ideas` — flat bullets

mkdir -p target dir before file_editor (ABSOLUTE path).

### G. Finish: `done` (or `failed: <reason>`).
"""


# ─── Helpers ────────────────────────────────────────────────────────────

def measure_top_orch(conv: Conversation) -> tuple[int, int]:
    """Return (n_events, total_input_tokens) for this Conversation's top-orch."""
    n_events = len(conv.state.events)
    total_input = 0
    for ev in conv.state.events:
        ts = getattr(ev, "tokens_input", None)
        if ts is not None:
            total_input += int(ts)
    return n_events, total_input


_FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)
_TOUCHED_BY_RE = re.compile(r"^touched_by:\s*\n((?:\s+-\s+.+\n)+)", re.MULTILINE)
# Bullet format: `- [<label>](<link>)<whitespace including possibly newlines><excerpt>`
# Excerpt may be on same line as link OR on next line (both are valid markdown).
# Bullet ends at next `- [` or `## ` heading or end of section.
_BULLET_RE = re.compile(
    r"^- \[([^\]]+)\]\((\.\./sources/[^)]+)\)\s*"
    r"(.+?)(?=\n- \[|\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip() if v.strip() else None
    # extract touched_by list
    tb = _TOUCHED_BY_RE.search(m.group(1))
    if tb:
        fm["touched_by"] = [
            ln.strip().lstrip("- ").strip()
            for ln in tb.group(1).splitlines() if ln.strip()
        ]
    return fm


def extract_section(text: str, header: str) -> str:
    """Return body of `## <header>` section up to next `## ` or EOF."""
    m = re.search(rf"^{re.escape(header)}\s*\n(.*?)(?=\n## |\Z)",
                  text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def validate_concept_v3(concept_path: Path) -> list[str]:
    """Return list of violations; empty list = OK."""
    violations = []
    text = concept_path.read_text()

    fm = parse_frontmatter(text)
    touched_by = fm.get("touched_by", [])
    if not touched_by:
        violations.append(f"{concept_path.name}: touched_by empty/missing")
        return violations

    if "## Touched in sources" not in text:
        violations.append(f"{concept_path.name}: ## Touched in sources missing")
        return violations

    section = extract_section(text, "## Touched in sources")
    bullets = _BULLET_RE.findall(section)

    if len(bullets) < len(touched_by):
        violations.append(
            f"{concept_path.name}: {len(bullets)} bullets but "
            f"touched_by has {len(touched_by)}"
        )

    for label, link, excerpt in bullets:
        excerpt_clean = re.sub(r"\[≈[^\]]+\]", "", excerpt).strip()
        if len(excerpt_clean) < EXCERPT_MIN_CHARS:
            violations.append(
                f"{concept_path.name}: excerpt for '{label[:40]}' "
                f"only {len(excerpt_clean)} chars (need ≥{EXCERPT_MIN_CHARS})"
            )
        if len(excerpt_clean) > EXCERPT_MAX_CHARS:
            violations.append(
                f"{concept_path.name}: excerpt for '{label[:40]}' "
                f"{len(excerpt_clean)} chars (max {EXCERPT_MAX_CHARS})"
            )
        # link target must resolve
        target = (concept_path.parent / link).resolve()
        if not target.exists():
            violations.append(
                f"{concept_path.name}: dead link '{link}'"
            )

    return violations


def main():
    register_tool("task_tool_set", TaskToolSet)
    for spec in [
        ("idea-classifier", "Classify NEW vs REPEATED.", [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "factcheck.py + Notes.", ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Concept template v3 (backlinks + excerpts).",
         ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Process ONE lecture; extract per-concept excerpts.",
         ["terminal", "file_editor", "task_tool_set"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step7-loop",
    )

    # ─── PYTHON-LOOP TOP-ORCHESTRATOR (INVARIANT A) ──────────────────
    per_source_metrics = []
    cumulative_input = 0

    for n in SOURCE_NUMBERS:
        raw = json.loads((WS / "raw" / f"{n:03d}.json").read_text())
        first = " ".join(raw["segments"][0]["text"].split()[:5])
        target = f"wiki/data/sources/ТестКурс/999 Тестовый модуль/{n:03d} {first}.md"

        # FRESH Conversation — invariant A
        main_agent = Agent(llm=llm, tools=[Tool(name="task_tool_set")])
        conv = Conversation(
            agent=main_agent, workspace=str(WS),
            visualizer=DelegationVisualizer(name=f"OrchStep7.src{n}"),
        )
        msg = (
            f"Process source N={n}. raw_path=raw/{n:03d}.json. "
            f"target_path={target}. "
            "Use the `task` tool with subagent_type='source-author' and "
            f"prompt='Process source N={n}. raw_path=raw/{n:03d}.json. "
            f"target_path={target}. Follow your system_prompt.'\n"
            "Wait for `done` ack from source-author, then finish."
        )
        print(f"\n=== SRC {n}: master_prompt {len(msg):,} chars ===")
        conv.send_message(msg)
        conv.run()

        n_events, input_tokens = measure_top_orch(conv)
        per_source_metrics.append({
            "source": n, "events": n_events, "input_tokens": input_tokens,
        })
        cumulative_input += input_tokens
        print(f"=== SRC {n}: top-orch events={n_events}, input_tokens={input_tokens:,} ===")

        # HARD ASSERTS — invariant A
        assert n_events <= TOP_ORCH_EVENTS_PER_SOURCE_LIMIT, (
            f"\n!!! INVARIANT A BROKEN: source {n} top-orch has {n_events} events "
            f"(limit {TOP_ORCH_EVENTS_PER_SOURCE_LIMIT}). "
            "Top-orchestrator should be fresh per source."
        )
        if input_tokens > 0:
            assert input_tokens <= TOP_ORCH_INPUT_TOKENS_PER_SOURCE_LIMIT, (
                f"\n!!! INVARIANT A BROKEN: source {n} input_tokens={input_tokens:,} "
                f"exceeds {TOP_ORCH_INPUT_TOKENS_PER_SOURCE_LIMIT:,}."
            )

    # ─── VERIFY FUNCTIONAL ───────────────────────────────────────────
    print("\n=== VERIFY (bench_grade per source) ===")
    all_ok = True
    total_repeated = 0; total_cf = 0; total_urls = 0; total_claims = 0
    for n in SOURCE_NUMBERS:
        result = subprocess.run(
            ["python3", BENCH_GRADE, str(WIKI), "--single-source", str(n), "--single-source-json"],
            capture_output=True, text=True
        )
        try: v = json.loads(result.stdout)
        except Exception:
            v = {"verified": "fail", "violations": [f"non-JSON: {result.stdout[:80]}"]}
        st = v.get("verified", "?")
        ct = v.get("claims_total", 0)
        rep = v.get("claims_REPEATED", 0); cf = v.get("claims_CF", 0); urls = v.get("wiki_url_count", 0)
        total_claims += ct; total_repeated += rep; total_cf += cf; total_urls += urls
        print(f"  source {n}: {st:5}  claims={ct}, REPEATED={rep}, CF={cf}, urls={urls}")
        if st != "ok":
            all_ok = False
            print(f"    violations: {v.get('violations', [])}")

    # ─── INVARIANT B — concept template v3 ───────────────────────────
    print("\n=== VERIFY (concept template v3) ===")
    concepts = list((WIKI / "data" / "concepts").glob("*.md"))
    template_violations = []
    for c in concepts:
        v = validate_concept_v3(c)
        template_violations.extend(v)
    if template_violations:
        print(f"  TEMPLATE VIOLATIONS ({len(template_violations)}):")
        for v in template_violations[:10]:
            print(f"    - {v}")
        if len(template_violations) > 10:
            print(f"    ... and {len(template_violations) - 10} more")
    else:
        print(f"  all {len(concepts)} concepts pass template v3")

    # ─── ARCHITECTURAL SUMMARY ───────────────────────────────────────
    print(f"\nPer-source top-orch metrics:")
    for m in per_source_metrics:
        print(f"  src {m['source']}: events={m['events']}, input_tokens={m['input_tokens']:,}")
    if cumulative_input > 0:
        avg = cumulative_input / len(SOURCE_NUMBERS)
        max_per = max(m["input_tokens"] for m in per_source_metrics)
        print(f"Cumulative top-orch input: {cumulative_input:,}; avg/src: {avg:,.0f}; "
              f"max/src: {max_per:,}; max/avg: {max_per/avg:.2f}")
        # linearity assert (invariant A continued)
        for m in per_source_metrics:
            assert m["input_tokens"] <= 2 * avg, (
                f"\n!!! INVARIANT A BROKEN (linearity): source {m['source']} "
                f"input_tokens={m['input_tokens']:,} > 2× avg ({avg:,.0f}). "
                "Suspect Conversation re-use across sources."
            )

    print(f"\nconcepts: {len(concepts)}")
    print(f"agg: claims={total_claims}, REPEATED={total_repeated}, "
          f"CF={total_cf}, urls={total_urls}")

    pass_functional = all([all_ok, total_repeated >= 2, total_claims >= 20])
    pass_template_v3 = (len(template_violations) == 0)

    if pass_functional and pass_template_v3:
        print("\n=== STEP 7 PASS ===")
        print("  INVARIANT A: top-orch context bounded per source ✓")
        print("  INVARIANT B: concept template v3 (backlinks + excerpts) ✓")
        sys.exit(0)
    else:
        print("\n=== STEP 7 FAIL ===", file=sys.stderr)
        if not pass_functional:
            print(f"  functional: ok-sources={all_ok}, claims_total={total_claims} (need ≥20), "
                  f"REPEATED={total_repeated} (need ≥2)", file=sys.stderr)
        if not pass_template_v3:
            print(f"  template-v3: {len(template_violations)} violations", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
