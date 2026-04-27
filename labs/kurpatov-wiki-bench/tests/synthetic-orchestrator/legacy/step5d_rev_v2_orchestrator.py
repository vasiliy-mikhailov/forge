"""
Step 5d-rev v2 — TaskToolSet migration.

Same architecture as step5d_rev (D7-rev4: enriched per-sub-agent input,
selective fact-check) but using TaskToolSet instead of deprecated DelegateTool.

Key change: TaskToolSet's `task(description, prompt, subagent_type)` creates
a FRESH sub-agent per call — no state accumulation. This solves the
production-scale context bloat that killed D7-rev4 attempt #1 (full lecture
transcript × spawn-once-reuse → 100K+ context after 2-3 delegates).

Also: TaskToolSet has no max_children=5 cap (the cap was DelegateTool-specific).

Pass criteria same as step5d-rev: 4/4 synth verified=ok, REPEATED >= 2,
canonical concept template, thematic groups, inline concept-links.
"""
import os, sys, json, subprocess
from pathlib import Path

from openhands.sdk import (
    LLM, Agent, Conversation, Tool,
    register_agent, agent_definition_to_factory,
)
from openhands.sdk.subagent import AgentDefinition
from openhands.sdk.tool import register_tool
from openhands.tools.task import TaskToolSet
# Visualizer is still in delegate package (works for any sub-agent activity)
from openhands.tools.delegate import DelegationVisualizer


WS = Path("/tmp/step5d-rev-v2-orch-ws")
WIKI = WS / "wiki"
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"
SOURCE_NUMBERS = [1, 2, 3, 4]


# ─── Sub-agent prompts (same as D7-rev4) ─────────────────────────────────

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim: the empirical claim text
  - lecture_transcript: full lecture transcript
  - prior_claims_json: output of get_known_claims.py

Step 1: Decide NEW vs REPEATED based on prior_claims_json.
  - If `claim` essentially matches a claim in any prior source's claims:
    output `REPEATED from <exact slug from that prior source>`.
  - Otherwise: `NEW`.

Step 2: Pick a thematic_category from this list (or propose new kebab-case):
  architecture-of-the-method | neuroanatomy | psychology-and-instinct |
  culture-and-society | dynamics-and-conflict | philosophy-and-method |
  history-and-attribution | empirical-paradigms

Output ONE LINE: `<verdict> | category=<thematic-tag>`. Then call finish.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Each task contains:
  - claim
  - lecture_transcript

Step 1: `cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"`
Step 2: Pick BEST matching Wikipedia URL.
Step 3: Scan lecture_transcript for speaker's caveats about THIS claim.
Step 4: Compose verdict + Notes.

Output exactly 3 lines:
  marker: <NEW|CONTRADICTS_FACTS|NO_MATCH>
  url: <best-Wikipedia-URL or none>
  notes: <2-3 sentences combining (a) speaker's quote with «...», (b) Wikipedia
          status, (c) optional journal ref>

Then call finish with that 3-line text.
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator. Task contains:
  - concept_slug
  - definition
  - source_slug
  - lecture_transcript
  - related_concepts

Workflow:
1. `ls wiki/data/concepts/<concept_slug>.md 2>/dev/null && echo EXISTS || echo NEW`
2. If NEW: file_editor create with template:

   ---
   slug: <concept_slug>
   introduced_in: <source_slug>
   touched_by:
     - <source_slug>
   related:
     - <related-1>
     - <related-2>
   ---
   # <Title in Russian>

   ## Definition

   <2-3 paragraphs grounded in lecture content with «...» quotes>

   ## See also

   - <related-concept-1> — <one-line>
   - <related-concept-2> — <one-line>

3. Append concept_slug to wiki/data/concept-index.json's concepts list.
4. If EXISTS, do nothing.

Output `concept <slug> ready` and finish.
"""

SOURCE_AUTHOR_PROMPT = """\
You are source-author. Process ONE lecture into a skill-v2 source.md.
Use the `task` tool (NOT `task_tool_set` — the registry name is
`task_tool_set` but the exposed function is named `task`) to invoke sub-agents.
Each `task(...)` call is FRESH context (no state accumulation).

Available tools: terminal, file_editor, task, finish, think.
Available subagent_type values for task(...): idea-classifier, fact-checker,
concept-curator.

Selectively fact-check: only run fact-checker on claims where you have
doubts. Skip fact-checker for confident claims (general anatomy, speaker's
own concepts).

Task message:
  - source_n
  - raw_path
  - target_path

Tools: terminal, file_editor, task (NOT task_tool_set), finish, think.

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"
```
Save as `lecture_transcript`.

### B. Get known claims
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```
Save as `prior_claims_json`.

### C. Extract claims (LLM reasoning)
Identify ALL distinct empirical claims. Aim for 20+ on substantial transcript.
For EACH, pick 2-5 concept slugs and assign `needs_factcheck: true|false`:

`needs_factcheck: false` — confident: speaker's own concepts, well-known
anatomy, well-known psychology paradigms, methodological framings.

`needs_factcheck: true` — uncertain: specific dates/years, named-person
attributions, specific numbers, controversial claims, anything where
speaker himself caveats it. Default to true when in doubt.

### D. Per-claim sub-agent calls (each call FRESH context):
For EACH claim i:
  1. ALWAYS call:
     task(description=f"classify claim {i}",
          prompt=f"claim: <text>\\nlecture_transcript:\\n<full text>\\nprior_claims_json: <full JSON>",
          subagent_type="idea-classifier")
     Parse: `<verdict> | category=<theme>`

  2. ONLY IF needs_factcheck[i]=true, also call:
     task(description=f"factcheck claim {i}",
          prompt=f"claim: <text>\\nlecture_transcript:\\n<full text>",
          subagent_type="fact-checker")
     Parse 3-line output: marker / url / notes

Combine into final marker:
  - if factchecker says CONTRADICTS_FACTS → marker=`[CONTRADICTS_FACTS]`
  - elif classifier says REPEATED → marker=`[REPEATED (from: <slug>)]`
  - else → marker=`[NEW]`

### E. For each NEW concept (not in prior_claims_json):
task(description=f"curate concept {slug}",
     prompt=f"concept_slug: <slug>\\ndefinition: <para>\\nsource_slug: <slug>\\nlecture_transcript:\\n<full text>\\nrelated_concepts: <list>",
     subagent_type="concept-curator")

### F. Assemble source.md and write to target_path

Frontmatter:
  slug: <derive: drop "wiki/data/sources/" prefix from target_path, drop ".md">
  course / module: from target_path
  extractor: whisper
  source_raw: <raw_path>
  duration_sec: <integer>
  language: ru
  processed_at: 2026-04-26T00:00:00Z
  fact_check_performed: true
  concepts_touched: [<5+ slugs>]
  concepts_introduced: [<STRICT subset of concepts_touched>]

Body — exactly 5 `## ` sections:
  `# <Russian title>`
  `## TL;DR` — paragraph
  `## Лекция (пересказ: только NEW и проверенное)` — 3-5 paragraphs with
    inline `[<concept-slug>](../../../concepts/<slug>.md)` links
  `## Claims — provenance and fact-check` — numbered list, each:
    `<n>. <text> [<marker>]`
    `<notes paragraph if fact-checked>`
    `— <url>` (if any)
  `## New ideas (verified)` — bullet list GROUPED BY thematic_category:
    `**<Theme>**`
    `- <bullet> ([<concept-link>](...))`
  `## All ideas` — flat bullet list

mkdir -p the parent dir before file_editor.

### G. Finish
Single word `done` (or `failed: <reason>`).
"""


def main():
    register_tool("task_tool_set", TaskToolSet)
    for spec in [
        ("idea-classifier", "Classify NEW vs REPEATED + thematic_category given full lecture context.",
         [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "factcheck.py + paragraph Notes.",
         ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Canonical concept article.",
         ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Process ONE lecture; selective fact-check; thematic grouping.",
         ["terminal", "file_editor", "task_tool_set"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step5d-rev-v2",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="task_tool_set")])
    conv = Conversation(agent=main_agent, workspace=str(WS),
                        visualizer=DelegationVisualizer(name="OrchStep5dRevV2"))

    inputs = []
    for n in SOURCE_NUMBERS:
        raw = json.loads((WS / "raw" / f"{n:03d}.json").read_text())
        first = " ".join(raw["segments"][0]["text"].split()[:5])
        target = f"wiki/data/sources/ТестКурс/999 Тестовый модуль/{n:03d} {first}.md"
        inputs.append(f"  N={n}: raw_path=raw/{n:03d}.json, target_path={target}")

    master = (
        "Process the 4 sources sequentially. For each N in [1,2,3,4]:\n"
        "  1. Use the `task` tool (NOT `task_tool_set`) with subagent_type='source-author' and "
        "prompt='Process source N=<N>. raw_path=<raw>. target_path=<target>. Follow your system_prompt.'\n"
        "  2. If reply starts with 'failed:', stop and finish with reason.\n"
        "  3. Else proceed.\n\n"
        "Inputs:\n" + "\n".join(inputs) + "\n\n"
        "Available tools: task, finish, think.\n"
        "Do NOT do source-authoring yourself. Substitute <N>, <raw>, <target>."
    )
    print(f"=== top master_prompt: {len(master):,} chars ===")
    conv.send_message(master)
    conv.run()

    # Verify
    print("\n=== VERIFY ===")
    all_ok = True
    total_repeated = 0; total_cf = 0; total_urls = 0; total_claims = 0
    for n in SOURCE_NUMBERS:
        result = subprocess.run(
            ["python3", BENCH_GRADE, str(WIKI), "--single-source", str(n), "--single-source-json"],
            capture_output=True, text=True
        )
        try:
            v = json.loads(result.stdout)
        except Exception:
            v = {"verified": "fail", "violations": [f"non-JSON: {result.stdout[:80]}"]}
        st = v.get("verified", "?")
        ct = v.get("claims_total", 0)
        rep = v.get("claims_REPEATED", 0); cf = v.get("claims_CF", 0); urls = v.get("wiki_url_count", 0)
        total_claims += ct; total_repeated += rep; total_cf += cf; total_urls += urls
        print(f"  source {n}: {st:5}  claims={ct}, REPEATED={rep}, CF={cf}, urls={urls}, "
              f"unmarked={v.get('claims_unmarked','?')}")
        if st != "ok":
            all_ok = False
            print(f"    violations: {v.get('violations', [])}")

    concepts = list((WIKI / "data" / "concepts").glob("*.md"))
    canonical_template_ok = False
    for c in concepts[:3]:
        text = c.read_text()
        if "touched_by:" in text and "## Definition" in text:
            canonical_template_ok = True; break
    n_events = len(conv.state.events)
    print(f"\nTop orchestrator: {n_events} events")
    print(f"concepts: {len(concepts)}, canonical-template OK: {canonical_template_ok}")
    print(f"agg: claims={total_claims}, REPEATED={total_repeated}, CF={total_cf}, urls={total_urls}")

    if all([all_ok, total_repeated >= 2, canonical_template_ok, n_events < 100]):
        print("\n=== STEP 5d-rev-v2 PASS ===")
        sys.exit(0)
    else:
        print("\n=== STEP 5d-rev-v2 FAIL ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
