"""
Step 5b — orchestrator + REPEATED detection via get_known_claims.py.

Workspace layout (matches production):
  /tmp/step5b-orch-ws/
    raw/{001,002,003,004}.json
    wiki/
      data/sources/ТестКурс/999 Тестовый модуль/<NNN>....md   (sub-agents write here)
      data/concepts/, data/concept-index.json
      skills/benchmark/scripts/{get_known_claims.py, factcheck.py}

Sub-agent system_prompt now mandates calling get_known_claims.py BEFORE
classification. Sources processed sequentially: 001 → 002 → 003 → 004.
Synth fixtures 003 / 004 deliberately repeat claims from 001 / 002.

Pass criteria:
  - 4/4 sources verified=ok
  - claims_REPEATED_sum >= 2 in aggregate (003 marks Moore REPEATED;
    004 marks Everest REPEATED)
  - master_prompt < 1500 chars
  - orchestrator events count < 100
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


WS = Path("/tmp/step5b-orch-ws")
WIKI = WS / "wiki"
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"
SOURCE_NUMBERS = [1, 2, 3, 4]


SOURCE_AUTHOR_PROMPT = """\
You are source-author. Each task message tells you:
  - source_n (integer)
  - raw_path (relative path to raw transcript JSON, e.g. raw/001.json)
  - target_path (relative path to write the source article, e.g. wiki/data/sources/.../001 ....md)

12-step ritual scoped to ONE source. Do NOT iterate to other sources.

STEP 1 — Read the transcript.
  Use terminal:
    python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"

STEP 2 — Get inventory of known claims from prior sources.
  Use terminal (CRITICAL — MUST run from inside wiki dir):
    cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
  This returns JSON like:
    {"count_sources": N, "sources": [{"slug": "...", "claims": [{"n":1, "marker":"NEW", "text":"..."}, ...]}, ...]}
  Save the full JSON in your reasoning. You will need it for STEP 4.

STEP 3 — Extract claims from your transcript.
  Identify factual claims in the transcript. Aim for 3-5 claims per source.

STEP 4 — Classify each claim against prior known claims.
  For each new claim:
    - If the same claim text (or essentially the same factual proposition)
      appears in any prior source's claims (from STEP 2 output) → mark it
      `[REPEATED (from: <slug-of-that-prior-source>)]`. Use the EXACT slug
      string from get_known_claims.py output.
    - If the claim contradicts well-known facts → mark `[CONTRADICTS_FACTS]`.
    - Otherwise → `[NEW]`.

STEP 5 — Write target_path with skill-v2 shape.
  Required frontmatter (YAML between --- fences, FIRST):
    slug: <derive: dirs joined by /, file basename without .md, drop the leading "wiki/" if any>
    course, module: from target_path's path components after wiki/data/sources/
    extractor: whisper
    source_raw: <raw_path>
    duration_sec: <integer from STEP 1>
    language: ru
    processed_at: 2026-04-26T00:00:00Z
    fact_check_performed: true
    concepts_touched: [<3+ kebab-case slugs>]
    concepts_introduced: [<2+ kebab-case slugs>]

  Required body — exactly five `## ` sections in this order:
    `# <Russian title>` (H1, NOT a section)
    `## TL;DR` — one paragraph
    `## Лекция (пересказ: только NEW и проверенное)` — 2-3 paragraphs
    `## Claims — provenance and fact-check` — numbered list, each claim
      followed by its marker (`[NEW]` / `[REPEATED (from: <slug>)]` / `[CONTRADICTS_FACTS]`).
      Include at least 1 https://en.wikipedia.org/... URL inline.
    `## New ideas (verified)` — bullet list (-)
    `## All ideas` — bullet list (-)

STEP 6 — Use file_editor to create target_path. mkdir -p the parent first.

STEP 7 — Finish with the literal word: `done`
  (or `failed: <one-line-reason>` on unrecoverable error).

Do not add prose around the finish message. Do not add extra sections.
"""


def main():
    source_author = AgentDefinition(
        name="source-author",
        description="Writes one skill-v2 source.md given source_n + raw_path + target_path. Runs get_known_claims.py for REPEATED detection.",
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
        usage_id="step5b",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(
        agent=main_agent,
        workspace=str(WS),
        visualizer=DelegationVisualizer(name="OrchStep5b"),
    )

    inputs_lines = []
    for n in SOURCE_NUMBERS:
        raw = json.loads((WS / "raw" / f"{n:03d}.json").read_text())
        first_words = " ".join(raw["segments"][0]["text"].split()[:5])
        target = f"wiki/data/sources/ТестКурс/999 Тестовый модуль/{n:03d} {first_words}.md"
        inputs_lines.append(f"  N={n}: raw_path=raw/{n:03d}.json, target_path={target}")

    master_prompt = (
        "You are an orchestrator. Process the 4 sources below sequentially.\n"
        f"For each source N in {SOURCE_NUMBERS}:\n"
        "  1. Use DelegateTool spawn ids=['src{N}'] agent_types=['source-author'].\n"
        "  2. Use DelegateTool delegate tasks={'src{N}': 'Process source N=<N>. "
        "raw_path=<raw>. target_path=<target>. Follow your system_prompt.'}.\n"
        "  3. If sub-agent's reply starts with 'failed:', call finish with reason.\n"
        "  4. Otherwise proceed to N+1.\n"
        "\nPer-source inputs:\n" + "\n".join(inputs_lines) + "\n"
        "\nDo NOT do source-authoring yourself. Substitute <N>, <raw>, <target>.\n"
    )
    print(f"=== master_prompt size: {len(master_prompt):,} chars ===")

    conv.send_message(master_prompt)
    conv.run()

    # Verify each source via bench_grade --single-source-json (--repo points to wiki)
    print("\n" + "=" * 60)
    print("VERIFICATION PHASE")
    print("=" * 60)
    all_ok = True
    total_repeated = 0
    total_claims = 0
    for n in SOURCE_NUMBERS:
        result = subprocess.run(
            ["python3", BENCH_GRADE, str(WIKI), "--single-source", str(n), "--single-source-json"],
            capture_output=True, text=True
        )
        try:
            verify = json.loads(result.stdout)
        except Exception:
            verify = {"verified": "fail", "violations": [f"non-JSON: {result.stdout[:80]}"]}
        status = verify.get("verified", "?")
        rep = verify.get("claims_REPEATED", 0)
        ct = verify.get("claims_total", 0)
        total_repeated += rep
        total_claims += ct
        print(f"  source {n}: {status:5}  claims={ct}, REPEATED={rep}, "
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
    print(f"Aggregate: claims_total={total_claims}, claims_REPEATED_sum={total_repeated}")

    pass_master = len(master_prompt) < 1500
    pass_events = n_events < 100
    pass_repeated = total_repeated >= 2

    if all_ok and pass_master and pass_events and pass_repeated:
        print(f"\n=== STEP 5b PASS: 4/4 ok, REPEATED={total_repeated} >= 2 ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 5b FAIL: all_ok={all_ok}, master_ok={pass_master}, "
              f"events_ok={pass_events}, REPEATED_ok={pass_repeated} (got {total_repeated}, need >= 2) ===",
              file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
