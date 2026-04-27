"""
D7-rev4 production orchestrator — module 005 of "Психолог-консультант".

Same architecture as D7-rev3 but with these changes (per ADR 0009 + D7-rev4.md):
  1. Each sub-agent receives FULL lecture transcript in delegate task body.
  2. classifier returns `verdict | category=<thematic-tag>` (was just verdict).
  3. fact-checker returns 3-line structured output (marker / url / notes
     paragraph combining speaker caveats + Wikipedia status + journal refs).
  4. source-author at extraction marks `needs_factcheck: true|false` per
     claim; only true claims trigger fact-checker delegation. Confident
     claims (general anatomy, speaker's own concepts) skip fact-checker
     and get [NEW] without URL — saves ~50% Wikipedia API calls.
  5. concept-curator writes canonical template (touched_by + ## Definition).
  6. source-author at assembly groups New Ideas by thematic_category and
     embeds inline concept-links throughout body.

Validated on synth (Step 5d-rev): 4/4 sources verified=ok, claims=25,
REPEATED=8, CF=2, ~55% selective fact-check rate, canonical concept
templates, thematic groups, inline concept-links.

Cyrillic paths preserved literally (course="Психолог-консультант", module=
"005 Природа внутренних конфликтов. Базовые психологические потребности").

Wikipedia rate-limit mitigation: factcheck.py User-Agent updated to
identifiable form per Wikipedia bot policy (commit ca01301 on skill-v2).

Usage:
  python3 orchestrator/run-d7-rev4.py
Env:
  LLM_BASE_URL, LLM_API_KEY, LLM_MODEL — vLLM config
  GITHUB_TOKEN — for git push
  D7_REV4_WORKDIR (optional) — default /tmp/d7-rev4-prod
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

from openhands.sdk import (
    LLM, Agent, Conversation, Tool,
    register_agent, agent_definition_to_factory,
)
from openhands.sdk.subagent import AgentDefinition
from openhands.sdk.tool import register_tool
from openhands.tools.delegate import DelegateTool, DelegationVisualizer


# ─── Configuration ───────────────────────────────────────────────────────

WORKDIR = Path(os.environ.get("D7_REV4_WORKDIR", "/tmp/d7-rev4-prod"))
RAW_REPO = "kurpatov-wiki-raw"
WIKI_REPO = "kurpatov-wiki-wiki"
GH_USER = "vasiliy-mikhailov"
SKILL_BRANCH = "skill-v2"
COURSE = "Психолог-консультант"
MODULE = "005 Природа внутренних конфликтов. Базовые психологические потребности"

BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"


# ─── Sub-agent prompts (D7-rev4) ─────────────────────────────────────────

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim: the empirical claim text
  - lecture_transcript: full lecture transcript (read-only context)
  - prior_claims_json: output of get_known_claims.py (may be empty for source 0)

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
  REPEATED from Психолог-консультант/005…/000 Вводная | category=architecture-of-the-method

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

Step 3: Scan `lecture_transcript` for any caveats the speaker (Курпатов)
  makes ABOUT THIS SPECIFIC CLAIM. Quote the speaker's own qualifications
  verbatim using «...» where available.

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

SOURCE_AUTHOR_PROMPT = f"""\
You are source-author. Process ONE Курпатов lecture into a skill-v2 source.md.
DELEGATE per-claim work to sub-sub-agents. Do NOT classify, fact-check,
or curate concepts in your own reasoning — always delegate.

Selectively fact-check: only run fact-checker on claims where you have
doubts (specific dates, attributions, numbers, controversial assertions).
For confident claims (general anatomy, speaker's own concept definitions,
well-known psychology paradigms), skip fact-checker entirely and mark
`[NEW]` without a URL.

Task message:
  - source_n (integer)
  - raw_path (relative path)
  - target_path (relative path)

Tools: terminal, file_editor, DelegateTool.

Course: `{COURSE}`
Module: `{MODULE}`

Cyrillic paths: course / module are LITERAL — do NOT romanize. If you
find yourself typing 'Psychologist-consultant' or '05-conflicts' — STOP.

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"
```
**FAIL-FAST**: if JSON read fails (json.JSONDecodeError, KeyError on
'segments') — DO NOT make up claims. Call finish with:
  `failed: cannot read transcript at <raw_path>: <reason>`

Save the transcript text as `lecture_transcript`. You will pass it INTO
each delegate call below.

### B. Get known claims from prior sources
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```
Save the full JSON output as `prior_claims_json`.

### C. Extract claims (LLM reasoning, no tools)
Identify ALL distinct empirical claims you can find. Aim for 20+ on a
substantial transcript (~30 KB). Do NOT under-extract.

For EACH claim, also pick 2-5 concept slugs (kebab-case English) that
this claim references.

For EACH claim, also assign confidence:

`needs_factcheck: false` — confident, no fact-check needed:
  - Speaker's own conceptual definitions ("Курпатов вводит понятие химер…")
  - Well-known general anatomy / neuroanatomy
  - Well-known psychology paradigms (Maslow, Freud's basics, etc)
  - Methodological framings of the speaker
  - Claims about the speaker's own synthesis

`needs_factcheck: true` — uncertain, requires verification:
  - Specific dates / years
  - Specific attributions to named people ("Дарвин сказал…", "Адлер ввёл…")
  - Specific numbers / statistics / percentages
  - Names of laws / theories tied to person
  - Claims that cross into other disciplines (history, biology, economics)
  - Any claim where the speaker himself caveats it

When in doubt, default to `needs_factcheck: true`.

### D. Spawn-once-reuse — ONE pair of sub-agents serves all claims:
```
DelegateTool spawn ids=['classifier', 'factchecker', 'curator']
                   agent_types=['idea-classifier', 'fact-checker', 'concept-curator']
```

For EACH claim i (sequential):
  - ALWAYS delegate to classifier (need thematic_category and REPEATED detection)
  - ONLY IF needs_factcheck[i]=true → also delegate to factchecker
  - Pass `lecture_transcript` (the full text from Step A) into both calls

If needs_factcheck=true:
```
DelegateTool delegate tasks={{
  'classifier':  'claim: <claim>\\nlecture_transcript:\\n<full text>\\nprior_claims_json: <full JSON>',
  'factchecker': 'claim: <claim>\\nlecture_transcript:\\n<full text>'
}}
```

If needs_factcheck=false:
```
DelegateTool delegate tasks={{
  'classifier': 'claim: <claim>\\nlecture_transcript:\\n<full text>\\nprior_claims_json: <full JSON>'
}}
```

Parse classifier output: `<verdict> | category=<theme>`:
  - REPEATED → marker=`[REPEATED (from: <slug>)]`
  - else    → marker=`[NEW]`
  - thematic_category from `category=...`

If factchecker invoked, parse 3-line output:
  marker: <NEW|CONTRADICTS_FACTS|NO_MATCH>
  url: <url>
  notes: <text>
  - if factchecker said `CONTRADICTS_FACTS`, OVERRIDE marker → `[CONTRADICTS_FACTS]`
  - URL goes inline in `## Claims` after the marker
  - notes goes as a paragraph under the claim line

### E. For EACH new concept introduced (NOT in prior_claims_json):
DelegateTool delegate task to 'curator':
  `concept_slug: <slug>\\ndefinition: <one paragraph>\\nsource_slug: <derived from target_path>\\nlecture_transcript:\\n<full text>\\nrelated_concepts: <list>`

### F. Assemble source.md and write to target_path

Frontmatter (YAML between --- fences, FIRST):
  slug: <derive: drop "wiki/data/sources/" prefix from target_path, drop ".md">
  course: {COURSE}
  module: {MODULE}
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
    where each concept is first mentioned.

  `## Claims — provenance and fact-check` — numbered list. For each claim:
    `<n>. <claim text> [<marker>]`
    `<notes paragraph if fact-checked, otherwise omit>`
    `— <url>` (only if fact-checker provided one)

  `## New ideas (verified)` — bullet list, GROUPED BY thematic_category:
    `**<Theme 1 name>**`
    `- <bullet> ([<concept-link>](...))`
    `- <bullet> ([<concept-link>](...))`
    ``
    `**<Theme 2 name>**`
    `- ...`

  `## All ideas` — flat bullet list of all extracted concepts/claims.

mkdir -p the parent dir before file_editor.

### G. Finish
Single word `done` (or `failed: <reason>`).
"""


# ─── Helpers ──────────────────────────────────────────────────────────────

def run_cmd(cmd, cwd=None, check=True):
    print(f"[cmd] {cmd}", file=sys.stderr)
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if r.stdout: print(r.stdout, file=sys.stderr)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        if check: raise RuntimeError(f"command failed: {cmd}")
    return r


def setup_workspace():
    if WORKDIR.exists():
        print(f"[setup] cleaning existing {WORKDIR}", file=sys.stderr)
        shutil.rmtree(WORKDIR)
    WORKDIR.mkdir(parents=True)

    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{RAW_REPO}.git raw", cwd=str(WORKDIR))
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{WIKI_REPO}.git wiki", cwd=str(WORKDIR))
    run_cmd(f"cd wiki && git checkout {SKILL_BRANCH} && git pull --ff-only", cwd=str(WORKDIR))

    served = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8").replace("openai/", "")
    branch = f"experiment/D7-rev4-{date.today().isoformat()}-{served}"
    print(f"[setup] experiment branch: {branch}", file=sys.stderr)

    run_cmd(f"cd wiki && git push origin --delete {branch} 2>&1 || true", cwd=str(WORKDIR), check=False)
    run_cmd(f"cd wiki && git checkout -b {branch} && git push -u origin {branch}", cwd=str(WORKDIR))
    return branch, served


def list_sources():
    r = run_cmd("python3 wiki/skills/benchmark/list_sources.py", cwd=str(WORKDIR))
    data = json.loads(r.stdout)
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"list_sources.py: {data['error']}")
    in_module = [s for s in data if MODULE in s.get("slug", "")]
    return [s for s in in_module if 0 <= s.get("index", -1) <= 6]


def build_inputs_text(sources):
    inputs = []
    for s in sources:
        n = s["index"]
        abs_raw = s["raw_json_path"]
        prefix = str(WORKDIR) + "/"
        if not abs_raw.startswith(prefix):
            raise RuntimeError(f"unexpected raw_json_path: {abs_raw}")
        raw_path = abs_raw[len(prefix):]
        target_path = f"wiki/data/sources/{s['slug']}.md"
        inputs.append((n, raw_path, target_path))
    return inputs


def setup_agents():
    register_tool("DelegateTool", DelegateTool)
    for spec in [
        ("idea-classifier", "Classify NEW vs REPEATED + thematic_category given full lecture context.",
         [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "Run factcheck.py + write paragraph Notes; only invoked on doubtful claims.",
         ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Create canonical concept article (touched_by + ## Definition).",
         ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Process ONE lecture; selective fact-check + thematic grouping.",
         ["terminal", "file_editor", "DelegateTool"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)


def verify_source(n):
    r = subprocess.run(
        ["python3", BENCH_GRADE, str(WORKDIR / "wiki"),
         "--single-source", str(n), "--single-source-json"],
        capture_output=True, text=True
    )
    try: return json.loads(r.stdout)
    except Exception: return {"verified": "fail", "violations": [f"non-JSON: {r.stdout[:200]}"]}


def commit_and_push_per_source(n, slug, branch, first_source):
    msg = f"source: {slug}"
    run_cmd("git add -A", cwd=str(WORKDIR / "wiki"))
    diff_r = subprocess.run("git diff --cached --quiet", shell=True, cwd=str(WORKDIR / "wiki"))
    if diff_r.returncode == 0:
        print(f"[commit] no changes for source {n}", file=sys.stderr)
        return None
    run_cmd(f'git commit -m "{msg}"', cwd=str(WORKDIR / "wiki"))
    run_cmd(f"git push origin {branch}", cwd=str(WORKDIR / "wiki"))
    sha = subprocess.run("git rev-parse --short HEAD", shell=True, cwd=str(WORKDIR / "wiki"),
                         capture_output=True, text=True).stdout.strip()
    return sha


def write_bench_report(state, branch, partial=False):
    report = WORKDIR / "wiki" / "bench-report.md"
    lines = [f"# bench report — D7-rev4 {'(partial)' if partial else ''}",
             "", f"branch: `{branch}`",
             f"sources processed: {len(state)}/7", "",
             "## Per-source", ""]
    for entry in state:
        v = entry.get("verify", {})
        lines.append(f"- source {entry['n']}: verified={v.get('verified','?')}, "
                     f"claims={v.get('claims_total','?')} (NEW={v.get('claims_NEW','?')}, "
                     f"REPEATED={v.get('claims_REPEATED','?')}, CF={v.get('claims_CF','?')}, "
                     f"unmarked={v.get('claims_unmarked','?')}), urls={v.get('wiki_url_count','?')}, "
                     f"commit={entry.get('commit','?')}")
    lines.append("")
    if partial:
        lines.append("## Stop point\n\nRun stopped fail-fast at first failure.")
    report.write_text("\n".join(lines))


def main():
    print("=" * 70, file=sys.stderr)
    print("D7-rev4 production orchestrator", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    branch, served = setup_workspace()
    sources = list_sources()
    print(f"[main] {len(sources)} sources in module 005", file=sys.stderr)
    if not sources:
        print("FATAL: no sources found", file=sys.stderr); sys.exit(2)

    inputs = build_inputs_text(sources)
    setup_agents()

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="d7-rev4-prod",
    )
    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(agent=main_agent, workspace=str(WORKDIR),
                        visualizer=DelegationVisualizer(name="OrchD7Rev4"))

    inputs_lines = [f"  N={n}: raw_path={raw}, target_path={target}"
                    for (n, raw, target) in inputs]
    master = (
        f"You are the D7-rev4 orchestrator. Process {len(inputs)} sources of module 005 sequentially.\n"
        "For each source N (in the order given below):\n"
        "  1. DelegateTool spawn ids=['src{N}'] agent_types=['source-author'].\n"
        "  2. DelegateTool delegate tasks={'src{N}': 'Process source N=<N>. raw_path=<raw>. "
        "target_path=<target>. Follow your system_prompt.'}.\n"
        "  3. If reply starts with 'failed:' — finish with 'STOPPED at N=<N>: <reply>'.\n"
        "  4. Else proceed.\n"
        "\nInputs:\n" + "\n".join(inputs_lines) + "\n"
        "\nDo NOT do source-authoring yourself. Substitute <N>, <raw>, <target> with actual values.\n"
        "After all sources processed, finish with 'all done'."
    )
    print(f"[main] master_prompt: {len(master):,} chars", file=sys.stderr)
    print(f"[main] starting conv.run() — wall ~60-90 min expected", file=sys.stderr)

    t0 = time.time()
    conv.send_message(master)
    conv.run()
    wall_min = (time.time() - t0) / 60
    print(f"[main] conv.run finished in {wall_min:.1f} min", file=sys.stderr)

    # Per-source verify + commit + push
    state = []
    stopped_at = None
    first = True
    for (n, raw_path, target_path) in inputs:
        slug = target_path[len("wiki/data/sources/"):-len(".md")]
        v = verify_source(n)
        ack = "done" if v.get("verified") == "ok" else "missing-or-fail"
        commit = None
        if v.get("verified") == "ok":
            commit = commit_and_push_per_source(n, slug, branch, first)
            first = False
        state.append({"n": n, "ack": ack, "verify": v, "commit": commit})
        if v.get("verified") != "ok":
            stopped_at = n
            print(f"[main] STOP at source {n}: verify=fail", file=sys.stderr)
            break

    partial = stopped_at is not None
    write_bench_report(state, branch, partial=partial)
    run_cmd("git add bench-report.md && git commit -m 'bench-report' && git push origin " + branch,
            cwd=str(WORKDIR / "wiki"), check=False)
    print(f"[main] branch pushed: {branch}", file=sys.stderr)

    if partial:
        print("=== EXIT FAILED ===", file=sys.stderr); sys.exit(1)
    print("=== EXIT OK ===", file=sys.stderr); sys.exit(0)


if __name__ == "__main__":
    main()
