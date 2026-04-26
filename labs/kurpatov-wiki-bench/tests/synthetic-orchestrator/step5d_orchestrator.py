"""
Step 5d — 3-level orchestration on 4 synth sources + concept-curator.

Per-claim fan-out: idea-classifier + fact-checker + concept-curator.
Sources processed sequentially: 1 → 2 → 3 → 4.

Pass:
  - 4/4 sources verified=ok
  - claims_REPEATED_sum >= 2 (cross-source detection)
  - claims_CF >= 1 (1950-Pareto error)
  - fact_check_citations_sum >= 6 (real Wikipedia URLs)
  - concepts_count >= 4 (concept-curator created files)
  - top orchestrator events bounded < 100
"""
import os, sys, json, subprocess
from pathlib import Path

from openhands.sdk import (
    LLM, Agent, Conversation, Tool,
    register_agent, agent_definition_to_factory,
)
from openhands.sdk.subagent import AgentDefinition
from openhands.sdk.tool import register_tool
from openhands.tools.delegate import DelegateTool, DelegationVisualizer


WS = Path("/tmp/step5d-orch-ws")
WIKI = WS / "wiki"
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"
SOURCE_NUMBERS = [1, 2, 3, 4]


# Level-3 sub-sub-agent prompts

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim
  - prior_claims_json (output of get_known_claims.py)

Decide:
  - If `claim` essentially matches a claim in any prior source's claims:
      `REPEATED from <exact slug from that prior source>`
  - Otherwise: `NEW`

Output ONE LINE only, then call finish with that line.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Task message: `claim: <text>`.

Step 1: `cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"`
Step 2: Pick the BEST matching Wikipedia URL.
Step 3: Output ONE LINE:
  - `CONTRADICTS_FACTS: <reason> | <url>`  (if Wikipedia contradicts a specific fact)
  - `URL: <url>`                            (if a clear topic match)
  - `NO_MATCH`                              (no relevant result)

Then call finish with that line.
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator. Task message contains:
  - concept_slug (kebab-case)
  - definition (one paragraph)
  - source_slug (the source that introduced this concept)

Workflow:
1. Check if `wiki/data/concepts/<concept_slug>.md` already exists via terminal:
     `ls wiki/data/concepts/<concept_slug>.md 2>/dev/null && echo EXISTS || echo NEW`
2. If NEW:
   a. Use file_editor to create wiki/data/concepts/<concept_slug>.md with this template:
       ```
       ---
       slug: <concept_slug>
       introduced_in: <source_slug>
       ---
       # <Title in Russian>

       <definition paragraph>
       ```
   b. Append the concept_slug to the `concepts` list in wiki/data/concept-index.json.
       (read JSON via terminal, mutate, write back)
3. If EXISTS, do nothing (idempotent).

Output ONE LINE: `concept <slug> ready` and call finish.
"""


# Level-2 source-author prompt

SOURCE_AUTHOR_PROMPT = """\
You are source-author. Process ONE lecture into a skill-v2 source.md.
DELEGATE per-claim work to sub-sub-agents. Do NOT classify, fact-check,
or curate concepts in your own reasoning — always delegate.

Task message:
  - source_n
  - raw_path
  - target_path

Tools: terminal, file_editor, DelegateTool.

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"
```

### B. Get known claims
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```
Save full JSON output as `prior_claims_json`.

### C. Extract claims (LLM reasoning, no tools)
Identify 2–4 distinct empirical claims. Also identify 2–3 concept slugs the
lecture introduces or references (kebab-case English).

### D. Spawn-once-reuse — ONE pair of sub-agents serves ALL claims.
Spawn ONCE at the beginning of step D:
  ids=['classifier', 'factchecker'], agent_types=['idea-classifier', 'fact-checker']
DelegateTool with command='spawn'.

Then for EACH claim (sequential):
  DelegateTool command='delegate' with tasks for the SAME two ids:
    {
      'classifier':  'claim: <claim text>\nprior_claims_json: <full JSON>',
      'factchecker': 'claim: <claim text>'
    }
  Both run in parallel; both return one-line outputs.

Parse outputs:
  - fact-checker → CONTRADICTS_FACTS:...  → marker=`[CONTRADICTS_FACTS]`, url
  - classifier → REPEATED from X           → marker=`[REPEATED (from: X)]`, url-if-any
  - else                                   → marker=`[NEW]`, url-if-any

### E. For each NEW concept introduced by this source (use concept-curator):
Spawn ONCE: ids=['curator'], agent_types=['concept-curator'].
Then for each new concept, DelegateTool delegate task to 'curator':
  'concept_slug: <slug>\ndefinition: <one paragraph>\nsource_slug: <derived from target_path>'

DO NOT spawn multiple classifier/factchecker/curator instances. Always reuse
the three you spawned at the start. The DelegateTool spawn cap is 5 — stay
under it.

### F. Assemble source.md and write to target_path
Frontmatter (YAML between --- fences):
  slug: <derive: drop wiki/ prefix from target_path, drop .md>
  course, module: from path
  extractor: whisper
  source_raw: <raw_path>
  duration_sec: <integer>
  language: ru
  processed_at: 2026-04-26T00:00:00Z
  fact_check_performed: true
  concepts_touched: [<list>]
  concepts_introduced: [<list>]

Body — exactly five `## ` sections in order:
  `# <Russian title>` (H1, NOT a section)
  `## TL;DR`
  `## Лекция (пересказ: только NEW и проверенное)`
  `## Claims — provenance and fact-check` (numbered list, marker per claim, URL inline)
  `## New ideas (verified)` (bullet list)
  `## All ideas` (bullet list)

mkdir -p the parent first.

### G. Finish
Single word: `done` (or `failed: <reason>`).
"""


def main():
    register_tool("DelegateTool", DelegateTool)

    for spec in [
        ("idea-classifier", "Pure-LLM classifier for one claim.", [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "Calls factcheck.py for one claim.", ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Creates/updates concept article + index entry.", ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Processes ONE lecture; delegates per-claim work.",
         ["terminal", "file_editor", "DelegateTool"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step5d",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(agent=main_agent, workspace=str(WS),
                        visualizer=DelegationVisualizer(name="OrchStep5d"))

    inputs = []
    for n in SOURCE_NUMBERS:
        raw = json.loads((WS / "raw" / f"{n:03d}.json").read_text())
        first = " ".join(raw["segments"][0]["text"].split()[:5])
        target = f"wiki/data/sources/ТестКурс/999 Тестовый модуль/{n:03d} {first}.md"
        inputs.append(f"  N={n}: raw_path=raw/{n:03d}.json, target_path={target}")

    master = (
        "Process the 4 sources sequentially. For each N in [1,2,3,4]:\n"
        "  1. DelegateTool spawn ids=['src{N}'] agent_types=['source-author'].\n"
        "  2. DelegateTool delegate tasks={'src{N}': 'Process source N=<N>. raw_path=<raw>. "
        "target_path=<target>. Follow your system_prompt.'}.\n"
        "  3. If reply starts with 'failed:', stop and finish with reason.\n"
        "  4. Else proceed.\n\n"
        "Inputs:\n" + "\n".join(inputs) + "\n\n"
        "Do NOT do source-authoring yourself. Substitute <N>, <raw>, <target>."
    )
    print(f"=== top master_prompt: {len(master):,} chars ===")
    conv.send_message(master)
    conv.run()

    # Verify
    print("\n=== VERIFY ===")
    all_ok = True
    total_repeated = 0
    total_cf = 0
    total_urls = 0
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
        rep = v.get("claims_REPEATED", 0); cf = v.get("claims_CF", 0); urls = v.get("wiki_url_count", 0)
        total_repeated += rep; total_cf += cf; total_urls += urls
        print(f"  source {n}: {st:5}  claims={v.get('claims_total','?')}, "
              f"REPEATED={rep}, CF={cf}, urls={urls}, "
              f"unmarked={v.get('claims_unmarked','?')}")
        if st != "ok": all_ok = False; print(f"    violations: {v.get('violations', [])}")

    concepts = list((WIKI / "data" / "concepts").glob("*.md"))
    n_events = len(conv.state.events)
    bytes_top = sum(len(json.dumps(ev.model_dump(mode="json"), default=str, ensure_ascii=False))
                     for ev in conv.state.events)
    print(f"\nTop orchestrator: {n_events} events, {bytes_top:,} bytes")
    print(f"concepts created: {len(concepts)}")
    print(f"agg: REPEATED={total_repeated}, CF={total_cf}, urls={total_urls}")

    pass_all_ok = all_ok
    pass_rep = total_repeated >= 2
    pass_cf = total_cf >= 1
    pass_urls = total_urls >= 6
    pass_concepts = len(concepts) >= 4
    pass_bounded = n_events < 100

    if all([pass_all_ok, pass_rep, pass_cf, pass_urls, pass_concepts, pass_bounded]):
        print(f"\n=== STEP 5d PASS ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 5d FAIL: ok={pass_all_ok}, rep={pass_rep}({total_repeated}), "
              f"cf={pass_cf}({total_cf}), urls={pass_urls}({total_urls}), "
              f"concepts={pass_concepts}({len(concepts)}), bounded={pass_bounded}({n_events}) ===",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
