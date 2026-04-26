"""
Step 4 — sub-agent writes a skill-v2-compliant source.md.

Orchestrator pre-reads the synth transcript and passes it inline to the
sub-agent along with target path. Sub-agent produces a file with skill v2
shape. Orchestrator runs bench_grade.py --single-source-json and asserts
verified=ok.
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


WS = Path("/tmp/step4-orch-ws")
SYNTH_RAW = Path("/home/vmihaylov/forge/labs/kurpatov-wiki-bench/tests/synthetic/fixtures/raw/001.json")


SOURCE_AUTHOR_PROMPT = """\
You are source-author. Your task message contains:
  - source_n: an integer (e.g. 1)
  - transcript_text: the lecture transcript verbatim
  - target_path: the relative path under the workspace where you must write
    the source article

Your job: write a SINGLE markdown file at target_path with the following
EXACT skill-v2 shape (no deviations).

## Required frontmatter (YAML between --- fences, must be FIRST)

```
---
slug: <derive from target_path; use the directory chain joined by /, plus the
       file basename without .md suffix>
course: <first dir level after data/sources/>
module: <second dir level after data/sources/>
extractor: whisper
source_raw: data/<derived raw path mirroring target_path>
duration_sec: <integer; if you don't know, use 200>
language: ru
processed_at: 2026-04-26T00:00:00Z
fact_check_performed: true
concepts_touched: [<3+ short kebab-case slugs>]
concepts_introduced: [<2+ short kebab-case slugs>]
---
```

## Required body sections (exactly five, in this order)

1. `# <Russian title>` — one-line title (NOT a section header level 2)
2. `## TL;DR` — one paragraph summary
3. `## Лекция (пересказ: только NEW и проверенное)` — 2-3 paragraphs of lecture summary
4. `## Claims — provenance and fact-check` — numbered list (1. 2. 3.) with at least 3 claims; each claim line has format:
   `1. <claim text> [NEW]` OR `1. <claim text> [REPEATED (from: <slug>)]` OR `1. <claim text> [CONTRADICTS_FACTS]`
   Also include at least 1 Wikipedia URL inline (e.g. https://en.wikipedia.org/wiki/Pareto_principle)
5. `## New ideas (verified)` — bullet list of new concepts (use - prefix)
6. `## All ideas` — bullet list of all concepts (use - prefix)

The `# <title>` line at the top is NOT one of the five sections — sections are the five `##` blocks (TL;DR, Лекция, Claims, New ideas, All ideas).

## Tooling

Use `terminal` tool to mkdir parent directories. Use `file_editor` to create the file.
Do NOT add any extra sections. Do NOT skip any section. Every claim MUST have a marker.

When done, call `finish` with the message `done`.
"""


def main():
    source_author = AgentDefinition(
        name="source-author",
        description="Writes a single skill-v2 source.md given transcript + target path.",
        tools=["terminal", "file_editor"],
        system_prompt=SOURCE_AUTHOR_PROMPT,
    )
    register_agent(
        name=source_author.name,
        factory_func=agent_definition_to_factory(source_author),
        description=source_author,
    )
    register_tool("DelegateTool", DelegateTool)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step4",
    )

    # Pre-read synth transcript
    raw = json.loads(SYNTH_RAW.read_text())
    transcript_text = "\n".join(seg["text"] for seg in raw["segments"])
    duration = int(raw["info"]["duration"])

    target_path = "data/sources/ТестКурс/999 Тестовый модуль/001 Парето и Мур.md"

    # Orchestrator
    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(
        agent=main_agent,
        workspace=str(WS),
        visualizer=DelegationVisualizer(name="OrchStep4"),
    )

    delegation_msg = (
        f"Use DelegateTool to spawn sub-agent id='src1' of type 'source-author', "
        f"then delegate the task with these inputs encoded in the prompt:\n\n"
        f"  source_n: 1\n"
        f"  transcript_text: |\n{transcript_text}\n"
        f"  target_path: {target_path}\n"
        f"  duration_sec: {duration}\n\n"
        f"Tell the sub-agent to follow its system prompt exactly. "
        f"After it returns 'done', call finish."
    )
    conv.send_message(delegation_msg)
    conv.run()

    # Verify via bench_grade.py --single-source 1 --single-source-json
    result = subprocess.run(
        ["python3", "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py",
         str(WS), "--single-source", "1", "--single-source-json"],
        capture_output=True, text=True
    )
    print("\n=== bench_grade output ===")
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr, file=sys.stderr)

    try:
        verify = json.loads(result.stdout)
    except Exception as e:
        print(f"=== STEP 4 FAIL: bench_grade output not JSON: {e} ===", file=sys.stderr)
        sys.exit(1)

    if verify.get("verified") == "ok":
        print(f"\n=== STEP 4 PASS: verified=ok, claims={verify['claims_total']}, sections={verify['sections_count']} ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 4 FAIL: verified={verify.get('verified')}, violations={verify.get('violations')} ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
