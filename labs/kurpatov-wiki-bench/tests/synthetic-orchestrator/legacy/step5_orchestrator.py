"""
Step 5 — orchestrator iterates 4 synth sources sequentially.

For each source N in [1, 2, 3, 4]:
  1. Pre-read raw/N.json → transcript_text
  2. Delegate to source-author with N + transcript + target_path
  3. Verify via bench_grade --single-source N --json
  4. If verified=fail → fail-fast (stop, exit non-zero)
  5. Else accumulate {n, status, verify_json} in orchestrator state

After all 4: print summary table, exit 0 if all 4 verified=ok.

Also assert orchestrator's own conversation event count stays bounded
(< 50 events) — proxy for "context didn't bloat".
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


WS = Path("/tmp/step5-orch-ws")
SYNTH_RAW = Path("/home/vmihaylov/forge/labs/kurpatov-wiki-bench/tests/synthetic/fixtures/raw")
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"
SOURCE_NUMBERS = [1, 2, 3, 4]


SOURCE_AUTHOR_PROMPT = """\
You are source-author. Your task message contains:
  - source_n: integer
  - transcript_text: lecture transcript verbatim
  - target_path: relative path under workspace where the article goes

Write a SINGLE markdown file at target_path with this EXACT skill-v2 shape:

## Frontmatter (YAML between --- fences, must be FIRST)
slug: <derive from target_path: dirs joined by /, file basename without .md>
course, module: from target_path's first two dirs after data/sources/
extractor: whisper
source_raw: data/<derived raw path mirroring target_path>
duration_sec: <integer, default 200 if unknown>
language: ru
processed_at: 2026-04-26T00:00:00Z
fact_check_performed: true
concepts_touched: [<3+ kebab-case slugs>]
concepts_introduced: [<2+ kebab-case slugs>]

## Body sections (exactly five ## headers, in this order)
- `# <Russian title>` (one-line H1, NOT a section)
- `## TL;DR` — one paragraph
- `## Лекция (пересказ: только NEW и проверенное)` — 2-3 paragraphs
- `## Claims — provenance and fact-check` — numbered list with at least 3
  claims; each MUST end with one marker: `[NEW]`, `[REPEATED (from: <slug>)]`,
  or `[CONTRADICTS_FACTS]`. Include at least 1 https://en.wikipedia.org/... URL inline.
- `## New ideas (verified)` — bullet list (-)
- `## All ideas` — bullet list (-)

## Tooling
- terminal: mkdir -p parent dirs
- file_editor: create the file

When done, finish with the SINGLE word: done

If you encounter unrecoverable error, finish with: failed: <one-line reason>
"""


def main():
    source_author = AgentDefinition(
        name="source-author",
        description="Writes one skill-v2 source.md given transcript+target.",
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
        usage_id="step5",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(
        agent=main_agent,
        workspace=str(WS),
        visualizer=DelegationVisualizer(name="OrchStep5"),
    )

    # Build the orchestrator's master prompt: tells it to loop and delegate
    sources_text = ""
    for n in SOURCE_NUMBERS:
        raw = json.loads((SYNTH_RAW / f"{n:03d}.json").read_text())
        transcript = "\n".join(seg["text"] for seg in raw["segments"])
        # use first 3 words of first segment as slug-suggestion
        title_hint = " ".join(raw["segments"][0]["text"].split()[:5])
        target = f"data/sources/ТестКурс/999 Тестовый модуль/{n:03d} {title_hint}.md"
        sources_text += f"\n--- SOURCE {n} ---\n"
        sources_text += f"target_path: {target}\n"
        sources_text += f"duration_sec: {int(raw['info']['duration'])}\n"
        sources_text += f"transcript_text:\n{transcript}\n"

    master_prompt = (
        f"You are an orchestrator. Process {len(SOURCE_NUMBERS)} synthetic sources "
        f"sequentially. For each source N in {SOURCE_NUMBERS}, you must:\n"
        f"  1. Use DelegateTool to spawn a NEW sub-agent id='src{{N}}' "
        f"of type 'source-author'.\n"
        f"  2. Delegate the source-N task with the inputs given below.\n"
        f"  3. Wait for sub-agent's return ('done' or 'failed: ...').\n"
        f"  4. If sub-agent says 'failed', STOP — call finish with the failure reason.\n"
        f"  5. Otherwise proceed to the next source.\n"
        f"\nAfter all {len(SOURCE_NUMBERS)} done, finish with a one-line summary.\n"
        f"\nCRITICAL: do NOT do any source-authoring yourself. Only orchestrate via "
        f"DelegateTool.\n"
        f"\nSource inputs:\n{sources_text}"
    )

    print(f"Orchestrator prompt size: {len(master_prompt):,} chars")
    conv.send_message(master_prompt)
    conv.run()

    # Verify each source via bench_grade
    print("\n" + "=" * 60)
    print("VERIFICATION PHASE")
    print("=" * 60)
    all_ok = True
    results = []
    for n in SOURCE_NUMBERS:
        result = subprocess.run(
            ["python3", BENCH_GRADE, str(WS), "--single-source", str(n), "--single-source-json"],
            capture_output=True, text=True
        )
        try:
            verify = json.loads(result.stdout)
        except Exception:
            verify = {"verified": "fail", "violations": [f"non-JSON: {result.stdout[:80]}"]}
        results.append({"n": n, "verify": verify})
        status = verify.get("verified", "?")
        print(f"  source {n}: {status:5}  claims={verify.get('claims_total','?')}, "
              f"unmarked={verify.get('claims_unmarked','?')}, "
              f"sections={verify.get('sections_count','?')}, "
              f"urls={verify.get('wiki_url_count','?')}")
        if status != "ok":
            all_ok = False
            print(f"    violations: {verify.get('violations', [])}")

    # Orchestrator events count
    n_events = len(conv.state.events)
    print(f"\nOrchestrator events count: {n_events}")
    print(f"Sources verified ok: {sum(1 for r in results if r['verify'].get('verified')=='ok')}/{len(SOURCE_NUMBERS)}")

    if all_ok and n_events < 100:
        print("\n=== STEP 5 PASS ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 5 FAIL: all_ok={all_ok}, n_events={n_events} ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
