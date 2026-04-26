"""
Step 5d-rev (D7-rev4 TDD on synth) — enriched per-sub-agent input + selective fact-check.

Differences from step5d_orchestrator.py:
  1. source-author passes FULL TRANSCRIPT into each delegate task body
     (not just claim text). Sub-agents see the lecture in their context.
  2. source-author also assigns `needs_factcheck: true|false` per claim;
     only true claims trigger fact-checker delegation. False claims still
     get classifier (for thematic_category + REPEATED).
  3. classifier returns `verdict | category=<thematic-tag>` (was just verdict).
  4. fact-checker returns structured `marker / url / notes` (was URL only),
     where notes is 2-3 sentences combining speaker caveats, Wikipedia
     status, optional journal ref.
  5. concept-curator writes canonical template with `touched_by` field +
     `## Definition` section (was minimal frontmatter).
  6. source-author at assembly groups `## New ideas` by thematic_category,
     adds Notes under each fact-checked claim, embeds inline concept-links
     in body bullets.

Pass on synth (4 sources):
  - 4/4 sources verified=ok
  - claims_REPEATED_sum >= 2 (cross-source carries over)
  - notes_flagged_sum >= 2 (fact-checker Notes parseable)
  - concept files have `touched_by` field + `## Definition` section
  - source.md has thematic groups in `## New ideas`
  - top orchestrator events bounded
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


WS = Path("/tmp/step5d-rev-orch-ws")
WIKI = WS / "wiki"
BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"
SOURCE_NUMBERS = [1, 2, 3, 4]


# ─── Level-3 sub-agent prompts (D7-rev4) ─────────────────────────────────

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim: the empirical claim text
  - lecture_transcript: full lecture transcript (read-only context)
  - prior_claims_json: output of get_known_claims.py (may be empty for first source)

Step 1: Decide NEW vs REPEATED based on prior_claims_json.
  - If `claim` essentially matches a claim in any prior source's claims:
    output `REPEATED from <exact slug from that prior source>`.
  - Otherwise: `NEW`.

Step 2: Look at where this claim sits in the lecture's narrative flow.
  Pick a thematic_category from this list (or propose a new kebab-case
  category if none fits):
    - architecture-of-the-method
    - neuroanatomy
    - psychology-and-instinct
    - culture-and-society
    - dynamics-and-conflict
    - philosophy-and-method
    - history-and-attribution
    - empirical-paradigms

Output ONE LINE: `<verdict> | category=<thematic-tag>`
Examples:
  NEW | category=neuroanatomy
  REPEATED from .../001 Парето | category=empirical-paradigms

Then call finish with that line.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Each task message contains:
  - claim: the empirical claim text
  - lecture_transcript: full lecture transcript (read-only context)

Step 1: Run via terminal:
  cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"

Step 2: Pick the BEST matching Wikipedia URL from results. Read the
  description field for context.

Step 3: Scan `lecture_transcript` for any caveats the speaker makes ABOUT
  THIS SPECIFIC CLAIM. Quote the speaker's own qualifications verbatim
  using «...» where available.

Step 4: Compose verdict + Notes:
  - If a result clearly matches the topic AND the description contradicts
    a specific fact in the claim (date, year, attribution, number):
        marker = CONTRADICTS_FACTS
  - Else if a result clearly matches the topic:
        marker = NEW (URL backs the claim, no contradiction found)
  - Else (factcheck returned empty or no relevant match):
        marker = NO_MATCH

Output structured text — exactly 3 lines:
  marker: <NEW|CONTRADICTS_FACTS|NO_MATCH>
  url: <best-Wikipedia-URL or none>
  notes: <2-3 sentences combining (a) speaker's own qualifications quoted
          from transcript using «...», (b) Wikipedia/scientific status,
          (c) optional journal reference if Wikipedia article body cites
          one>

Then call finish with that 3-line text verbatim (no extra prose around).
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator. Task message contains:
  - concept_slug (kebab-case)
  - definition (one paragraph in Russian, derived from lecture)
  - source_slug (the source that introduced this concept)
  - lecture_transcript (read-only — for grounding)
  - related_concepts (list of slugs of other concepts in the same source)

Workflow:
1. Check if `wiki/data/concepts/<concept_slug>.md` exists:
     `ls wiki/data/concepts/<concept_slug>.md 2>/dev/null && echo EXISTS || echo NEW`
2. If NEW:
   a. Use file_editor to create `wiki/data/concepts/<concept_slug>.md` with
      this CANONICAL template:

       ---
       slug: <concept_slug>
       introduced_in: <source_slug>
       touched_by:
         - <source_slug>
       related:
         - <related-slug-1>
         - <related-slug-2>
       ---
       # <Title in Russian>

       ## Definition

       <2-3 paragraph definition grounded in lecture content; quote the
       speaker's own framing with «...» where relevant>

       ## See also

       - <related-concept-1> — <one line of why related>
       - <related-concept-2> — <one line of why related>

   b. Read `wiki/data/concept-index.json`, append concept_slug to its
      `concepts` list, write back.
3. If EXISTS, do nothing (idempotent).

Output ONE LINE: `concept <slug> ready` and finish.
"""

SOURCE_AUTHOR_PROMPT = """\
You are source-author. You process ONE lecture into a skill-v2 source.md
file. You DELEGATE per-claim work to sub-sub-agents — but only run
fact-checker on claims where you have doubts (specific dates, attributions,
numbers, controversial assertions). For confident claims (general anatomy,
speaker's own concept definitions, well-known psychology paradigms), skip
fact-checker entirely and mark `[NEW]` without a URL.

Your task message tells you:
  - source_n (integer)
  - raw_path (relative path, e.g. raw/001.json)
  - target_path (relative path, e.g. wiki/data/sources/.../001 ....md)

Tools: terminal, file_editor, DelegateTool.

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"
```
Save the transcript text as `lecture_transcript` — you will pass it INTO
each delegate call below.

### B. Get known claims from prior sources
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```
Save full JSON output as `prior_claims_json`.

### C. Extract claims (LLM reasoning, no tools)
Identify ALL distinct empirical claims you can find. Aim for 20+ on a
substantial transcript; do NOT under-extract. For each claim, also pick
2-5 concept slugs (kebab-case English) that this claim references.

For EACH claim, also assign confidence:

`needs_factcheck: false` — confident, no fact-check needed:
  - Speaker's own conceptual definitions
  - Well-known general anatomy / neuroanatomy
  - Well-known psychology paradigms
  - Methodological framings of the speaker
  - Claims about the speaker's own synthesis

`needs_factcheck: true` — uncertain, requires verification:
  - Specific dates / years
  - Specific attributions to named people
  - Specific numbers / statistics / percentages
  - Names of laws / theories tied to person
  - Claims that cross into other disciplines (history, biology, economics)
  - Any claim where the speaker himself caveats it

When in doubt, default to `needs_factcheck: true`. Over-checking is fine,
under-checking risks fake URLs.

### D. Spawn-once-reuse — ONE pair of sub-agents serves ALL claims:
```
DelegateTool spawn ids=['classifier', 'factchecker', 'curator']
                   agent_types=['idea-classifier', 'fact-checker', 'concept-curator']
```

For EACH claim i:
  - ALWAYS delegate to classifier (need thematic_category and REPEATED detection)
  - ONLY IF needs_factcheck[i]=true → delegate to factchecker
  - Pass `lecture_transcript` (the full text from Step A) into both delegate calls

If needs_factcheck=true:
```
DelegateTool delegate tasks={
  'classifier':  'claim: <claim>\\nlecture_transcript:\\n<full text>\\nprior_claims_json: <full JSON>',
  'factchecker': 'claim: <claim>\\nlecture_transcript:\\n<full text>'
}
```

If needs_factcheck=false:
```
DelegateTool delegate tasks={
  'classifier': 'claim: <claim>\\nlecture_transcript:\\n<full text>\\nprior_claims_json: <full JSON>'
}
```

Parse classifier output: `<verdict> | category=<theme>` →
  - if verdict starts with "REPEATED" → marker = `[REPEATED (from: <slug>)]`
  - else → marker = `[NEW]`
  - thematic_category = parsed from `category=...`

If factchecker invoked, parse 3-line output:
  marker: <CONTRADICTS_FACTS|NEW|NO_MATCH>
  url: <url>
  notes: <text>
  - If factchecker said `CONTRADICTS_FACTS`, OVERRIDE classifier's marker → `[CONTRADICTS_FACTS]`
  - URL goes inline in `## Claims` after the marker
  - notes goes as paragraph under the claim line

### E. For EACH new concept introduced (NOT in prior_claims_json):
DelegateTool delegate task to 'curator':
  `concept_slug: <slug>\\ndefinition: <one paragraph>\\nsource_slug: <derived from target_path>\\nlecture_transcript:\\n<full text>\\nrelated_concepts: <list>`

### F. Assemble source.md and write to target_path

Frontmatter (YAML between --- fences, FIRST):
  slug: <derive: drop "wiki/data/sources/" prefix from target_path, drop ".md">
  course: <first dir level after wiki/data/sources/>
  module: <second dir level after wiki/data/sources/>
  extractor: whisper
  source_raw: <raw_path>
  duration_sec: <integer from STEP A>
  language: ru
  processed_at: 2026-04-26T00:00:00Z
  fact_check_performed: true
  concepts_touched: [<all referenced concepts, 5+ slugs>]
  concepts_introduced: [<STRICT subset of concepts_touched: only first-mentioned-in-this-source>]

CRITICAL: slug must NOT include "data/sources/" or "wiki/" prefix.
CRITICAL: concepts_introduced ⊂ concepts_touched (subset, not equal).

Body — exactly five `## ` sections in order:
  `# <Russian title>` (H1, NOT a section)

  `## TL;DR` — one paragraph

  `## Лекция (пересказ: только NEW и проверенное)` — 3-5 paragraphs.
    Embed inline concept-links: `[<concept-slug>](../../../concepts/<concept-slug>.md)`
    where each concept is first mentioned in the prose.

  `## Claims — provenance and fact-check` — numbered list. For each claim:
    `<n>. <claim text> [<marker>]`
    `<notes paragraph if fact-checked, otherwise omit>`
    `— <url>` (only if fact-checker provided one)

  `## New ideas (verified)` — bullet list, GROUPED BY thematic_category:
    `**<Theme 1 name>**`
    `- <bullet describing claim 1> ([<concept-link>](...))`
    `- <bullet describing claim 2> ([<concept-link>](...))`
    ``
    `**<Theme 2 name>**`
    `- ...`

  `## All ideas` — flat bullet list of all extracted concepts/claims.

mkdir -p the parent dir before file_editor.

### G. Finish
Single word `done` (or `failed: <one-line-reason>` on unrecoverable error).
"""


def main():
    register_tool("DelegateTool", DelegateTool)
    for spec in [
        ("idea-classifier", "Classify NEW vs REPEATED + thematic_category given full lecture context.",
         [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "Run factcheck.py + write paragraph Notes; only invoked on doubtful claims.",
         ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Create canonical concept article with touched_by + ## Definition.",
         ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Process ONE lecture; selective fact-check + thematic grouping at assembly.",
         ["terminal", "file_editor", "DelegateTool"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step5d-rev",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(agent=main_agent, workspace=str(WS),
                        visualizer=DelegationVisualizer(name="OrchStep5dRev"))

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
    total_repeated = 0; total_cf = 0; total_urls = 0; total_claims = 0; total_notes = 0
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
        # Notes: count "Notes" / "*Notes*" / "⚠" markers in actual file
        # bench_grade --single-source doesn't surface notes_flagged in JSON for single source — re-read file
        src_file = WIKI / v.get("source_file", "") if v.get("source_file") else None
        notes_count = 0
        if src_file and src_file.exists():
            text = src_file.read_text()
            # Crude: count "Notes" occurrences in Claims block
            import re
            cb = re.search(r"## Claims.*?(?=^## |\Z)", text, re.S | re.M)
            if cb:
                notes_count = len(re.findall(r"(?:^|\s)Notes[\.:]|⚠", cb.group()))
        total_notes += notes_count
        print(f"  source {n}: {st:5}  claims={ct}, REPEATED={rep}, CF={cf}, urls={urls}, notes={notes_count}, "
              f"unmarked={v.get('claims_unmarked','?')}")
        if st != "ok":
            all_ok = False
            print(f"    violations: {v.get('violations', [])}")

    concepts = list((WIKI / "data" / "concepts").glob("*.md"))
    # Check first concept has touched_by + ## Definition
    canonical_template_ok = False
    for c in concepts[:3]:
        text = c.read_text()
        if "touched_by:" in text and "## Definition" in text:
            canonical_template_ok = True
            break
    n_events = len(conv.state.events)
    bytes_top = sum(len(json.dumps(ev.model_dump(mode="json"), default=str, ensure_ascii=False))
                    for ev in conv.state.events)
    print(f"\nTop orchestrator: {n_events} events, {bytes_top:,} bytes")
    print(f"concepts created: {len(concepts)}, canonical-template OK: {canonical_template_ok}")
    print(f"agg: claims={total_claims}, REPEATED={total_repeated}, CF={total_cf}, urls={total_urls}, notes={total_notes}")

    pass_all_ok = all_ok
    pass_rep = total_repeated >= 2
    pass_notes = total_notes >= 2
    pass_template = canonical_template_ok
    pass_bounded = n_events < 100

    if all([pass_all_ok, pass_rep, pass_notes, pass_template, pass_bounded]):
        print(f"\n=== STEP 5d-rev PASS ===")
        sys.exit(0)
    else:
        print(f"\n=== STEP 5d-rev FAIL: ok={pass_all_ok}, rep={pass_rep}({total_repeated}), "
              f"notes={pass_notes}({total_notes}), template={pass_template}, "
              f"bounded={pass_bounded}({n_events}) ===", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
