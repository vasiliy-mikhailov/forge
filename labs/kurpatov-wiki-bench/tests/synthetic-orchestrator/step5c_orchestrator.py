"""
Step 5c — 3-level orchestration on synth source 1.

Level 1: top orchestrator (this script's main_agent) — delegates to source-author.
Level 2: source-author — extracts claims, fans out to idea-classifier + fact-checker
         per claim, assembles source.md.
Level 3: idea-classifier (pure LLM) + fact-checker (terminal w/ factcheck.py).

Pass on synth source 1:
  - source 1 verified=ok
  - factcheck.py invocations visible in events
  - At least 1 Wikipedia URL inline in source.md
  - CONTRADICTS_FACTS marker on the 1950-Pareto error
  - Each level's context bounded (top orch < 100 events; source-author and
    sub-sub-agents have isolated state.events)
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


WS = Path("/tmp/step5c-orch-ws")
WIKI = WS / "wiki"
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"


# Level-3 sub-sub-agent prompts

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim: the empirical claim text
  - prior_claims_json: output of get_known_claims.py (may be `{"count_sources":0,"sources":[]}` if first source)

Decide:
  - If `claim` essentially matches a claim in any prior source's `claims` array
    (same factual proposition, possibly rephrased), output:
      `REPEATED from <exact slug from that prior source>`
  - Otherwise output: `NEW`

Output ONE LINE only, no surrounding prose, no quotes. Then call finish with that line.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Each task message contains:
  - claim: the empirical claim text

Step 1: Run via terminal:
  cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"

Step 2: Inspect the JSON output. The relevant fields per result are
  `title`, `description`, `url`. Pick the BEST matching Wikipedia URL.

Step 3: Decide:
  - If a result clearly matches the claim's topic AND the description
    contradicts a specific fact in the claim (date, year, name, attribution):
      output: `CONTRADICTS_FACTS: <one-line reason> | <url>`
  - Else if a result clearly matches the topic:
      output: `URL: <url>`
  - Else (factcheck returned empty even after fallback ladder, or no
    relevant match):
      output: `NO_MATCH`

Output ONE LINE only. Then call finish with that line.
"""


# Level-2 source-author prompt

SOURCE_AUTHOR_PROMPT = """\
You are source-author. You process ONE lecture into a skill-v2 source.md
file. You DELEGATE per-claim work to specialised sub-agents.

Your task message tells you:
  - source_n
  - raw_path (e.g. raw/001.json)
  - target_path (e.g. wiki/data/sources/.../001 ….md)

Tools available:
  - terminal (read transcripts, run get_known_claims.py)
  - file_editor (write target file)
  - DelegateTool (fan-out per claim to sub-sub-agents)

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"
```

### B. Get known claims from prior sources
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```
Save the full JSON output (`prior_claims_json`) — you will pass it to idea-classifier.

### C. Extract claims from your transcript (in your own LLM reasoning)
Identify 3–5 distinct empirical claims. For each, prepare a short claim string.

### D. Fan-out per claim — for EACH claim:
Use DelegateTool with command='spawn' to spawn TWO sub-agents per claim:
  ids=[f'class_{i}', f'fact_{i}']
  agent_types=['idea-classifier', 'fact-checker']

Then DelegateTool command='delegate' with both tasks at once (parallel):
  tasks={
    f'class_{i}': f"claim: <claim text>\\nprior_claims_json: <full JSON from step B>",
    f'fact_{i}':  f"claim: <claim text>"
  }

The delegation result will contain both sub-agents' one-line outputs.
Parse:
  - classifier output: `NEW` or `REPEATED from <slug>`
  - fact-checker output: `URL: <url>` or `CONTRADICTS_FACTS: <reason> | <url>` or `NO_MATCH`

Combine into the marker for this claim:
  - if fact-checker says `CONTRADICTS_FACTS:...`  → marker = `[CONTRADICTS_FACTS]`, url from fact-checker
  - elif classifier says `REPEATED from X`        → marker = `[REPEATED (from: X)]`, url if any
  - else                                          → marker = `[NEW]`, url if any

### E. Assemble source.md and write to target_path
Use file_editor. Required skill-v2 shape:

Frontmatter (YAML between --- fences, FIRST):
  slug: <derive from target_path: drop "wiki/" prefix, drop .md>
  course, module: from path components after wiki/data/sources/
  extractor: whisper
  source_raw: <raw_path>
  duration_sec: <integer>
  language: ru
  processed_at: 2026-04-26T00:00:00Z
  fact_check_performed: true
  concepts_touched: [<3+ kebab-case slugs>]
  concepts_introduced: [<2+ kebab-case slugs>]

Body (exactly five `## ` sections, in order):
  `# <Russian title>` (H1, NOT a section)
  `## TL;DR` — one paragraph
  `## Лекция (пересказ: только NEW и проверенное)` — 2-3 paragraphs
  `## Claims — provenance and fact-check` — numbered list, each claim:
      `<n>. <claim text> <marker> — <url-if-any>`
  `## New ideas (verified)` — bullet list
  `## All ideas` — bullet list

mkdir -p the parent dir before file_editor.

### F. Finish
Single word: `done` (or `failed: <one-line-reason>`).

Do NOT do classification or fact-checking yourself in your own reasoning.
Always delegate to idea-classifier + fact-checker.
"""


def main():
    register_tool("DelegateTool", DelegateTool)

    # Register the three custom agents
    classifier = AgentDefinition(
        name="idea-classifier",
        description="Pure-LLM. Decides NEW vs REPEATED for one claim given prior_claims_json.",
        tools=[],
        system_prompt=IDEA_CLASSIFIER_PROMPT,
    )
    register_agent(classifier.name, agent_definition_to_factory(classifier), classifier)

    factchecker = AgentDefinition(
        name="fact-checker",
        description="Calls factcheck.py for one claim, returns best Wikipedia URL or CONTRADICTS_FACTS verdict.",
        tools=["terminal"],
        system_prompt=FACT_CHECKER_PROMPT,
    )
    register_agent(factchecker.name, agent_definition_to_factory(factchecker), factchecker)

    source_author = AgentDefinition(
        name="source-author",
        description="Processes ONE lecture into skill-v2 source.md. Delegates per-claim work.",
        tools=["terminal", "file_editor", "DelegateTool"],
        system_prompt=SOURCE_AUTHOR_PROMPT,
    )
    register_agent(source_author.name, agent_definition_to_factory(source_author), source_author)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step5c",
    )

    # Top orchestrator — only DelegateTool
    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(
        agent=main_agent,
        workspace=str(WS),
        visualizer=DelegationVisualizer(name="OrchStep5c"),
    )

    target = "wiki/data/sources/ТестКурс/999 Тестовый модуль/001 Сегодня поговорим о двух эмпирических.md"
    master = (
        "Use DelegateTool spawn ids=['src1'] agent_types=['source-author'].\n"
        f"Then delegate task to src1: 'Process source N=1. raw_path=raw/001.json. "
        f"target_path={target}. Follow your system_prompt.'\n"
        "After src1 returns, finish with the reply verbatim.\n"
    )
    print(f"=== top master_prompt: {len(master):,} chars ===")
    conv.send_message(master)
    conv.run()

    # Verify
    print("\n=== VERIFY ===")
    result = subprocess.run(
        ["python3", BENCH_GRADE, str(WIKI), "--single-source", "1", "--single-source-json"],
        capture_output=True, text=True
    )
    try:
        verify = json.loads(result.stdout)
    except Exception:
        verify = {"verified": "fail", "violations": [f"non-JSON: {result.stdout[:80]}"]}
    print(json.dumps(verify, ensure_ascii=False, indent=2))

    # Extra checks: factcheck.py was actually invoked
    events_text = json.dumps([ev.model_dump(mode="json") for ev in conv.state.events],
                              default=str, ensure_ascii=False)
    factcheck_in_events = "factcheck.py" in events_text
    n_events_top = len(conv.state.events)
    bytes_top = len(events_text)
    print(f"\nTop orchestrator: {n_events_top} events, {bytes_top:,} bytes")
    print(f"factcheck.py in events: {factcheck_in_events}")

    pass_verified = verify.get("verified") == "ok"
    pass_factcheck = factcheck_in_events
    pass_url = verify.get("wiki_url_count", 0) >= 1
    pass_top_bounded = n_events_top < 100

    if pass_verified and pass_factcheck and pass_url and pass_top_bounded:
        print(f"\n=== STEP 5c PASS ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 5c FAIL: verified={pass_verified}, factcheck={pass_factcheck}, "
              f"url={pass_url}, top_bounded={pass_top_bounded} ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
