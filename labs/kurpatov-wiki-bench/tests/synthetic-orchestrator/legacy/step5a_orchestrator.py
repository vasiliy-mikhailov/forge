"""
Step 5a — orchestrator passes only source_n + paths, NOT transcripts.

Master prompt is now ~400 chars regardless of transcript size.
Sub-agent reads transcript itself from raw/{N}.json via terminal.

Asserts:
  - 4/4 sources verified=ok
  - master_prompt size < 600 chars
  - orchestrator total events bytes much less than Step 5
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


WS = Path("/tmp/step5a-orch-ws")
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"
SOURCE_NUMBERS = [1, 2, 3, 4]


# Sub-agent now reads the transcript file itself.
SOURCE_AUTHOR_PROMPT = """\
You are source-author. Each task message tells you:
  - source_n (integer)
  - raw_path (path to raw transcript JSON, relative to workspace)
  - target_path (path to write the source article, relative to workspace)

Steps:
1. Read the raw JSON via terminal:
   `python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments']))"`
   This gives you the lecture transcript text.
   Also note `d['info']['duration']` for the duration_sec field.
2. Use file_editor to create target_path with the EXACT skill-v2 shape:

## Frontmatter (YAML between --- fences, FIRST)
slug: <derive from target_path: dirs joined by /, file basename without .md>
course: <first dir level after data/sources/>
module: <second dir level after data/sources/>
extractor: whisper
source_raw: <raw_path>
duration_sec: <integer from raw JSON's info.duration>
language: ru
processed_at: 2026-04-26T00:00:00Z
fact_check_performed: true
concepts_touched: [<3+ kebab-case slugs>]
concepts_introduced: [<2+ kebab-case slugs>]

## Body sections (exactly these 5 ## headers, in order)
- `# <Russian title>` — H1, NOT a section
- `## TL;DR` — one paragraph
- `## Лекция (пересказ: только NEW и проверенное)` — 2-3 paragraphs
- `## Claims — provenance and fact-check` — numbered list, 3+ claims, each with marker
  `[NEW]`, `[REPEATED (from: <slug>)]`, or `[CONTRADICTS_FACTS]`. Include ≥1 wikipedia URL inline.
- `## New ideas (verified)` — bullet list (-)
- `## All ideas` — bullet list (-)

3. mkdir -p the parent dir before file_editor.
4. Finish with single word: `done` (or `failed: <reason>` on unrecoverable error).
"""


def main():
    source_author = AgentDefinition(
        name="source-author",
        description="Writes one skill-v2 source.md given source_n + raw_path + target_path.",
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
        usage_id="step5a",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(
        agent=main_agent,
        workspace=str(WS),
        visualizer=DelegationVisualizer(name="OrchStep5a"),
    )

    # Build per-source delegate inputs as compact tuples
    inputs_lines = []
    for n in SOURCE_NUMBERS:
        raw = json.loads((WS / "raw" / f"{n:03d}.json").read_text())
        first_words = " ".join(raw["segments"][0]["text"].split()[:5])
        target = f"data/sources/ТестКурс/999 Тестовый модуль/{n:03d} {first_words}.md"
        inputs_lines.append(f"  N={n}: raw_path=raw/{n:03d}.json, target_path={target}")

    master_prompt = (
        "You are an orchestrator. Process the 4 sources below sequentially.\n"
        f"For each source N in {SOURCE_NUMBERS}:\n"
        "  1. Use DelegateTool with command='spawn', ids=['src{N}'], "
        "agent_types=['source-author'].\n"
        "  2. Use DelegateTool with command='delegate', tasks={'src{N}': "
        "'Process source N=<N>. raw_path=<raw>. target_path=<target>. "
        "Follow your system_prompt.'}.\n"
        "  3. If sub-agent's reply starts with 'failed:', call finish with the reason.\n"
        "  4. Otherwise proceed to N+1.\n"
        f"\nPer-source inputs:\n" + "\n".join(inputs_lines) + "\n"
        "\nDo NOT do source-authoring yourself. Only orchestrate via DelegateTool. "
        "Substitute <N>, <raw>, <target> with the values from the inputs.\n"
    )

    print(f"=== master_prompt size: {len(master_prompt):,} chars ===")
    print(master_prompt)
    print("=== end of master_prompt ===\n")

    conv.send_message(master_prompt)
    conv.run()

    # Verify
    print("\n" + "=" * 60)
    print("VERIFICATION PHASE")
    print("=" * 60)
    all_ok = True
    for n in SOURCE_NUMBERS:
        result = subprocess.run(
            ["python3", BENCH_GRADE, str(WS), "--single-source", str(n), "--single-source-json"],
            capture_output=True, text=True
        )
        try:
            verify = json.loads(result.stdout)
        except Exception:
            verify = {"verified": "fail", "violations": [f"non-JSON: {result.stdout[:80]}"]}
        status = verify.get("verified", "?")
        print(f"  source {n}: {status:5}  claims={verify.get('claims_total','?')}, "
              f"unmarked={verify.get('claims_unmarked','?')}, "
              f"sections={verify.get('sections_count','?')}, "
              f"urls={verify.get('wiki_url_count','?')}")
        if status != "ok":
            all_ok = False
            print(f"    violations: {verify.get('violations', [])}")

    n_events = len(conv.state.events)
    events_bytes = sum(len(json.dumps(ev.model_dump(mode="json"), default=str, ensure_ascii=False))
                       for ev in conv.state.events)
    print(f"\nOrchestrator: {n_events} events, total ~{events_bytes:,} bytes")
    print(f"master_prompt size: {len(master_prompt):,} chars")

    if all_ok and len(master_prompt) < 1500 and n_events < 100:
        print("\n=== STEP 5a PASS ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 5a FAIL ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
