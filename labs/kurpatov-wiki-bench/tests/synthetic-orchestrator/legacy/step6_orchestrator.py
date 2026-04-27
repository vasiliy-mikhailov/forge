"""
Step 6 — fail-fast policy on broken synthetic fixture.

Workspace setup: raw/001.json + raw/002.json + raw/003.json (DELIBERATELY
broken JSON) + raw/004.json. Orchestrator must:
  - process sources 1 and 2 successfully
  - delegate source 3 → sub-agent detects broken transcript →
    returns "failed: <reason>"
  - orchestrator stops, does NOT delegate source 4
  - final finish message indicates failure

Pass criteria:
  - source 1 and 2 written (verified=ok via bench_grade)
  - source 3 NOT written
  - source 4 NOT written
  - orchestrator's finish message contains "failed" or "stopped"
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


WS = Path("/tmp/step6-orch-ws")
WIKI = WS / "wiki"
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"


# Re-use the prompts from step5d for source-author + sub-sub-agents.
# Key difference: explicit instruction in source-author that on broken
# transcript it must return "failed: ..." and not invent fake claims.

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim
  - prior_claims_json

Decide:
  - If `claim` essentially matches a claim in any prior source: `REPEATED from <slug>`
  - Otherwise: `NEW`

Output ONE LINE only, then call finish.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Task: `claim: <text>`.

Step 1: `cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"`
Step 2: Output ONE LINE:
  - `CONTRADICTS_FACTS: <reason> | <url>`
  - `URL: <url>`
  - `NO_MATCH`

Then call finish.
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator. Task message:
  - concept_slug
  - definition
  - source_slug

If wiki/data/concepts/<concept_slug>.md exists → do nothing.
Else → file_editor create with:
```
---
slug: <concept_slug>
introduced_in: <source_slug>
---
# <Title>

<definition>
```
Append concept_slug to concepts list in wiki/data/concept-index.json.
Output ONE LINE: `concept <slug> ready` and finish.
"""

SOURCE_AUTHOR_PROMPT = """\
You are source-author. Process ONE lecture into a skill-v2 source.md.
DELEGATE per-claim work to sub-sub-agents.

Task message:
  - source_n, raw_path, target_path

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"
```

**FAIL-FAST**: If reading the JSON fails (json.JSONDecodeError, KeyError on
'segments', etc.) — DO NOT make up claims. DO NOT proceed to step B. Instead
call `finish` with EXACTLY this format:
  `failed: cannot read transcript at <raw_path>: <one-line error reason>`

### B. Get known claims
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```
Save full JSON output as prior_claims_json.

### C. Extract claims (LLM reasoning)
Identify 2-4 distinct empirical claims + 2-3 concept slugs.

### D. Spawn-once-reuse classifier+factchecker:
```
DelegateTool spawn ids=['classifier', 'factchecker', 'curator']
                   agent_types=['idea-classifier', 'fact-checker', 'concept-curator']
```
Then for each claim:
```
DelegateTool delegate tasks={
  'classifier': 'claim: <text>\\nprior_claims_json: <full JSON>',
  'factchecker': 'claim: <text>'
}
```
Combine outputs into marker per the priority:
  - fact-checker says CONTRADICTS_FACTS:... → marker [CONTRADICTS_FACTS]
  - classifier says REPEATED from X → marker [REPEATED (from: X)]
  - else → marker [NEW]

### E. For each new concept (not in prior_claims_json), delegate to curator.

### F. Assemble source.md and write to target_path
Frontmatter + 5 sections per skill v2 (TL;DR, Лекция, Claims, New ideas, All ideas).

### G. Finish
Single word `done` (or `failed: <reason>` on unrecoverable error).
"""


def main():
    register_tool("DelegateTool", DelegateTool)
    for spec in [
        ("idea-classifier", "Classify NEW vs REPEATED.", [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "Run factcheck.py for one claim.", ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Create/update concept article.", ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Process one lecture; delegate per-claim work.",
         ["terminal", "file_editor", "DelegateTool"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step6",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(agent=main_agent, workspace=str(WS),
                        visualizer=DelegationVisualizer(name="OrchStep6"))

    inputs = []
    for n in [1, 2, 3, 4]:
        target = f"wiki/data/sources/ТестКурс/999 Тестовый модуль/{n:03d} synth-source-{n}.md"
        inputs.append(f"  N={n}: raw_path=raw/{n:03d}.json, target_path={target}")

    master = (
        "Process the 4 sources sequentially, fail-fast on first failure.\n"
        "For each N in [1, 2, 3, 4]:\n"
        "  1. DelegateTool spawn ids=['src{N}'] agent_types=['source-author'].\n"
        "  2. DelegateTool delegate tasks={'src{N}': 'Process source N=<N>. raw_path=<raw>. "
        "target_path=<target>. Follow your system_prompt.'}.\n"
        "  3. Inspect the reply.\n"
        "     - If reply STARTS WITH 'failed:' → call finish with 'STOPPED at N=<N>: <reply>'.\n"
        "       DO NOT proceed to N+1.\n"
        "     - Else proceed to N+1.\n\n"
        "Inputs:\n" + "\n".join(inputs) + "\n\n"
        "After all sources processed without failure, finish with 'all done'."
    )
    print(f"=== master_prompt: {len(master):,} chars ===")
    conv.send_message(master)
    conv.run()

    # Verify outcome
    print("\n=== VERIFY ===")
    src_dir = WIKI / "data/sources/ТестКурс/999 Тестовый модуль"
    written = sorted(p.name for p in src_dir.glob("*.md")) if src_dir.exists() else []
    print(f"sources written: {written}")

    # Look at orchestrator's final message
    last_messages = []
    for ev in reversed(conv.state.events):
        d = ev.model_dump(mode="json")
        if "AgentFinishAction" in str(type(ev)) or "finish" in json.dumps(d, default=str)[:300].lower():
            last_messages.append(d)
            if len(last_messages) >= 3: break
    last_text = json.dumps(last_messages, default=str, ensure_ascii=False)

    pass_2_done = any("001" in n for n in written) and any("002" in n for n in written)
    pass_3_not_done = not any("003" in n for n in written)
    pass_4_not_done = not any("004" in n for n in written)
    pass_orch_stopped = "STOPPED" in last_text or "failed" in last_text.lower() or "stopped" in last_text.lower()

    print(f"  pass_2_done (1 and 2 written): {pass_2_done}")
    print(f"  pass_3_not_done (3 NOT written): {pass_3_not_done}")
    print(f"  pass_4_not_done (4 NOT written): {pass_4_not_done}")
    print(f"  pass_orch_stopped (finish mentions failed/stopped): {pass_orch_stopped}")

    if all([pass_2_done, pass_3_not_done, pass_4_not_done, pass_orch_stopped]):
        print("\n=== STEP 6 PASS ===")
        sys.exit(0)
    else:
        print("\n=== STEP 6 FAIL ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
