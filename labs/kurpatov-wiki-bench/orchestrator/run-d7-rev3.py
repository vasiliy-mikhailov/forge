"""
D7-rev3 production orchestrator — module 005 of "Психолог-консультант".

Architecture (per ADR 0009 + skill openhands-sdk-orchestration):
  - Python script as the outer driver — does git ops, verify, fail-fast logic.
  - One Conversation drives the orchestrator agent; orchestrator iterates
    7 sources internally via DelegateTool.
  - Each source delegates to source-author (registered AgentDefinition) which
    fans out per-claim to idea-classifier + fact-checker, per-concept to
    concept-curator (3-level architecture validated in synth Step 5d).
  - Shared workspace: one /workspace/raw + /workspace/wiki cloned once;
    sub-agents share filesystem (sequential — no race).
  - Python wrapper post-run: bench_grade per-source, commit per-source, push.
  - Fail-fast: if sub-agent returns 'failed:' or verify=fail, stop, write
    partial bench-report, exit non-zero.

Skill v2 ritual scoped to one source via source-author's system_prompt.
Cyrillic paths preserved literally (course="Психолог-консультант", module=
"005 Природа внутренних конфликтов. Базовые психологические потребности").

Usage:
  python3 orchestrator/run-d7-rev3.py
Env:
  LLM_BASE_URL, LLM_API_KEY, LLM_MODEL — vLLM config
  GITHUB_TOKEN — for git push
  D7_REV3_WORKDIR (optional) — default /tmp/d7-rev3-prod
"""
import json
import os
import re
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

WORKDIR = Path(os.environ.get("D7_REV3_WORKDIR", "/tmp/d7-rev3-prod"))
RAW_REPO = "kurpatov-wiki-raw"
WIKI_REPO = "kurpatov-wiki-wiki"
GH_USER = "vasiliy-mikhailov"
SKILL_BRANCH = "skill-v2"
COURSE = "Психолог-консультант"
MODULE = "005 Природа внутренних конфликтов. Базовые психологические потребности"

BENCH_GRADE = "/home/vmihaylov/forge/labs/kurpatov-wiki-bench/evals/grade/bench_grade.py"


# ─── Sub-agent prompts (3-level architecture, scoped to skill v2) ────────

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim: the empirical claim text
  - prior_claims_json: output of get_known_claims.py (may be empty for source 0)

Decide:
  - If `claim` essentially matches a claim in any prior source's claims
    (same factual proposition, possibly rephrased), output:
      `REPEATED from <exact slug from that prior source>`
  - Otherwise output: `NEW`

Output ONE LINE only. Then call finish with that line.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Task message: `claim: <text>`.

Step 1: Run via terminal:
  cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"

Step 2: Inspect the JSON output. Pick the BEST matching Wikipedia URL.

Step 3: Output ONE LINE:
  - `CONTRADICTS_FACTS: <reason> | <url>`  (Wikipedia clearly contradicts the claim's specific date/year/name/attribution)
  - `URL: <url>`                            (clear topic match)
  - `NO_MATCH`                              (factcheck returned empty even after fallback ladder)

Then call finish with that line.
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator. Task message contains:
  - concept_slug (kebab-case)
  - definition (one paragraph in Russian)
  - source_slug (the source that introduced this concept)

Workflow:
1. Check if `wiki/data/concepts/<concept_slug>.md` exists:
     `ls wiki/data/concepts/<concept_slug>.md 2>/dev/null && echo EXISTS || echo NEW`
2. If NEW:
   a. Use file_editor to create wiki/data/concepts/<concept_slug>.md:
       ```
       ---
       slug: <concept_slug>
       introduced_in: <source_slug>
       ---
       # <Title in Russian>

       <definition paragraph>
       ```
   b. Read wiki/data/concept-index.json, append concept_slug to concepts list, write back.
3. If EXISTS, do nothing (idempotent).

Output ONE LINE: `concept <slug> ready` and finish.
"""

SOURCE_AUTHOR_PROMPT = f"""\
You are source-author. Process ONE lecture into a skill-v2 source.md.
DELEGATE per-claim work to sub-sub-agents. Do NOT classify, fact-check,
or curate concepts in your own reasoning — always delegate.

Task message:
  - source_n
  - raw_path
  - target_path

Tools: terminal, file_editor, DelegateTool.

Course: `{COURSE}`
Module: `{MODULE}`

Cyrillic paths: course / module are literal — do NOT romanize. If you find
yourself typing 'Psychologist-consultant' or '05-conflicts' — STOP, that
is wrong.

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); print('\\n'.join(s['text'] for s in d['segments'])); print('DURATION', int(d['info']['duration']))"
```
**FAIL-FAST**: If the JSON read fails (json.JSONDecodeError, KeyError on
'segments'), DO NOT make up claims. Call finish with:
  `failed: cannot read transcript at <raw_path>: <one-line reason>`

### B. Get known claims
```
cd wiki && python3 skills/benchmark/scripts/get_known_claims.py
```
Save full JSON output as `prior_claims_json`.

### C. Extract claims (LLM reasoning, no tools)
Identify 5–15 distinct empirical claims (a real lecture has many; do NOT
under-extract). For each, prepare a concise claim string in Russian.

Also identify 5–10 concept slugs the lecture introduces or references
(kebab-case English).

### D. Spawn-once-reuse — ONE pair of sub-agents serves all claims:
```
DelegateTool spawn ids=['classifier', 'factchecker', 'curator']
                   agent_types=['idea-classifier', 'fact-checker', 'concept-curator']
```

For EACH claim (sequential, but classifier+factchecker fan out IN PARALLEL):
```
DelegateTool delegate tasks={{
  'classifier':  'claim: <claim>\\nprior_claims_json: <full JSON>',
  'factchecker': 'claim: <claim>'
}}
```

Combine into marker for the claim:
  - fact-checker → CONTRADICTS_FACTS:... → marker `[CONTRADICTS_FACTS]`, url
  - classifier  → REPEATED from X        → marker `[REPEATED (from: X)]`, url-if-any
  - else                                  → marker `[NEW]`, url-if-any

### E. For EACH new concept introduced (NOT in prior_claims_json):
DelegateTool delegate task to 'curator':
  `concept_slug: <slug>\\ndefinition: <one paragraph>\\nsource_slug: <derive from target_path>`

### F. Assemble source.md and write to target_path

Frontmatter (YAML between --- fences, FIRST):
  slug: <derive from target_path: drop "wiki/" prefix, drop .md>
  course: {COURSE}
  module: {MODULE}
  extractor: whisper
  source_raw: <raw_path>
  duration_sec: <integer from STEP A>
  language: ru
  processed_at: 2026-04-26T00:00:00Z
  fact_check_performed: true
  concepts_touched: [<5+ kebab-case slugs>]
  concepts_introduced: [<3+ kebab-case slugs>]

Body — exactly five `## ` sections in order:
  `# <Russian title>` (H1, NOT a section)
  `## TL;DR` — one paragraph in Russian
  `## Лекция (пересказ: только NEW и проверенное)` — 3-5 paragraphs in Russian
  `## Claims — provenance and fact-check` — numbered list, each claim:
      `<n>. <claim text in Russian> <marker> — <url-if-any>`
  `## New ideas (verified)` — bullet list (-)
  `## All ideas` — bullet list (-)

mkdir -p the parent dir before file_editor.

### G. Finish
Single word: `done` (or `failed: <reason>`).
"""


# ─── Helpers ──────────────────────────────────────────────────────────────

def run_cmd(cmd, cwd=None, check=True):
    """Run a shell command, return CompletedProcess. Print on stderr."""
    print(f"[cmd] {cmd}", file=sys.stderr)
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if r.stdout: print(r.stdout, file=sys.stderr)
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        if check: raise RuntimeError(f"command failed: {cmd}")
    return r


def setup_workspace():
    """Clone raw + wiki, switch wiki to skill-v2, create experiment branch, push empty branch."""
    if WORKDIR.exists():
        print(f"[setup] cleaning existing {WORKDIR}", file=sys.stderr)
        shutil.rmtree(WORKDIR)
    WORKDIR.mkdir(parents=True)

    token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{RAW_REPO}.git raw",
            cwd=str(WORKDIR))
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{WIKI_REPO}.git wiki",
            cwd=str(WORKDIR))
    run_cmd(f"cd wiki && git checkout {SKILL_BRANCH} && git pull --ff-only", cwd=str(WORKDIR))

    served = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8").replace("openai/", "")
    branch = f"experiment/D7-rev3-{date.today().isoformat()}-{served}"
    print(f"[setup] experiment branch: {branch}", file=sys.stderr)

    # Purge stale remote branch (best effort)
    run_cmd(f"cd wiki && git push origin --delete {branch} 2>&1 || true", cwd=str(WORKDIR), check=False)
    run_cmd(f"cd wiki && git checkout -b {branch} && git push -u origin {branch}",
            cwd=str(WORKDIR))

    return branch, served


def list_sources():
    """Run list_sources.py to get the source indices for module 005."""
    r = run_cmd("python3 wiki/skills/benchmark/list_sources.py", cwd=str(WORKDIR))
    data = json.loads(r.stdout)
    if "error" in data:
        raise RuntimeError(f"list_sources.py: {data['error']}")
    # Filter to module 005
    return [s for s in data.get("sources", []) if MODULE in s.get("path", "")]


def build_inputs_text(sources):
    """For each source, derive raw_path + target_path."""
    inputs = []
    for s in sources:
        n = s["index"]
        slug_filename = s["filename"]   # "000 Вводная лекция. ...Md"
        raw_path = f"raw/{s['raw_path']}/raw.json" if s.get("raw_path") else f"raw/{s['filename']}/raw.json"
        target_path = f"wiki/data/sources/{COURSE}/{MODULE}/{slug_filename}.md"
        inputs.append((n, raw_path, target_path))
    return inputs


def setup_agents():
    register_tool("DelegateTool", DelegateTool)
    for spec in [
        ("idea-classifier", "Pure-LLM classifier for one claim.", [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "Calls factcheck.py for one claim.", ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Creates/updates concept article + index entry.",
         ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Processes ONE lecture; delegates per-claim work.",
         ["terminal", "file_editor", "DelegateTool"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)


def parse_finish_reply(conv):
    """Get the orchestrator's last finish message."""
    for ev in reversed(conv.state.events):
        d = ev.model_dump(mode="json")
        if "finish" in str(type(ev)).lower() or "FinishAction" in str(type(ev)):
            for f in ("message", "thought", "text"):
                if f in d and isinstance(d[f], str):
                    return d[f]
    return ""


def verify_source(n, branch):
    """Run bench_grade --single-source N --json. Returns dict."""
    r = subprocess.run(
        ["python3", BENCH_GRADE, str(WORKDIR / "wiki"),
         "--single-source", str(n), "--single-source-json"],
        capture_output=True, text=True
    )
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"verified": "fail", "violations": [f"non-JSON: {r.stdout[:200]}"]}


def commit_and_push_per_source(n, slug, branch):
    """Add, commit (per-source), push."""
    msg = f"source: {slug}"
    run_cmd("git add -A", cwd=str(WORKDIR / "wiki"))
    # Check there are staged changes
    diff_r = subprocess.run("git diff --cached --quiet", shell=True, cwd=str(WORKDIR / "wiki"))
    if diff_r.returncode == 0:
        print(f"[commit] no changes to commit for source {n}", file=sys.stderr)
        return None
    run_cmd(f'git commit -m "{msg}"', cwd=str(WORKDIR / "wiki"))
    run_cmd(f"git push origin {branch}", cwd=str(WORKDIR / "wiki"))
    sha = subprocess.run("git rev-parse --short HEAD", shell=True, cwd=str(WORKDIR / "wiki"),
                          capture_output=True, text=True).stdout.strip()
    return sha


def write_bench_report(state, branch, partial=False):
    report = WORKDIR / "wiki" / "bench-report.md"
    lines = [f"# bench report — D7-rev3 {'(partial)' if partial else ''}",
             "",
             f"branch: `{branch}`",
             f"sources processed: {len(state)}/{7}",
             "",
             "## Per-source",
             ""]
    for entry in state:
        v = entry.get("verify", {})
        lines.append(f"- source {entry['n']}: status={entry.get('ack','?')}, "
                      f"verified={v.get('verified','?')}, "
                      f"claims={v.get('claims_total','?')} "
                      f"(NEW={v.get('claims_NEW','?')}, REPEATED={v.get('claims_REPEATED','?')}, "
                      f"CF={v.get('claims_CF','?')}, unmarked={v.get('claims_unmarked','?')}), "
                      f"urls={v.get('wiki_url_count','?')}, "
                      f"commit={entry.get('commit','?')}")
    lines.append("")
    if partial:
        lines.append("## Stop point\n\nRun stopped fail-fast at first failure. See last per-source entry.")
    report.write_text("\n".join(lines))
    return report


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 70, file=sys.stderr)
    print("D7-rev3 production orchestrator", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    branch, served = setup_workspace()
    sources = list_sources()
    print(f"[main] {len(sources)} sources in module 005", file=sys.stderr)
    if not sources:
        print("FATAL: no sources found", file=sys.stderr)
        sys.exit(2)

    inputs = build_inputs_text(sources)

    setup_agents()

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="d7-rev3-prod",
    )

    main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
    conv = Conversation(
        agent=main_agent, workspace=str(WORKDIR),
        visualizer=DelegationVisualizer(name="OrchD7Rev3"),
    )

    inputs_lines = [f"  N={n}: raw_path={raw}, target_path={target}"
                    for (n, raw, target) in inputs]
    master = (
        f"You are the D7-rev3 orchestrator. Process {len(inputs)} sources of module 005 sequentially.\n"
        "For each source N (in the order given below):\n"
        "  1. DelegateTool spawn ids=['src{N}'] agent_types=['source-author'].\n"
        "  2. DelegateTool delegate tasks={'src{N}': 'Process source N=<N>. raw_path=<raw>. "
        "target_path=<target>. Follow your system_prompt.'}.\n"
        "  3. Inspect reply. If starts with 'failed:' — call finish with 'STOPPED at N=<N>: <reply>'. "
        "DO NOT proceed to next source.\n"
        "  4. Else proceed to next.\n"
        "\nInputs:\n" + "\n".join(inputs_lines) + "\n"
        "\nDo NOT do source-authoring yourself. Substitute <N>, <raw>, <target> with the actual values.\n"
        "After all sources processed without failure, finish with 'all done'."
    )
    print(f"[main] master_prompt: {len(master):,} chars", file=sys.stderr)
    print(f"[main] starting Conversation.run() — wall time will be ~30-90 min", file=sys.stderr)

    t0 = time.time()
    conv.send_message(master)
    conv.run()
    wall_min = (time.time() - t0) / 60
    print(f"[main] Conversation finished in {wall_min:.1f} min", file=sys.stderr)

    # Parse finish message (for fail-fast detection)
    finish_msg = parse_finish_reply(conv)
    print(f"[main] orchestrator finish: {finish_msg[:200]!r}", file=sys.stderr)

    # Per-source verification + commit + push
    state = []
    stopped_at = None
    for (n, raw_path, target_path) in inputs:
        slug = target_path.replace("wiki/", "").rsplit(".md", 1)[0]
        v = verify_source(n, branch)
        ack = "done" if v.get("verified") == "ok" else "missing-or-fail"
        commit = None
        if v.get("verified") == "ok":
            commit = commit_and_push_per_source(n, slug, branch)
        state.append({"n": n, "ack": ack, "verify": v, "commit": commit})
        if v.get("verified") != "ok":
            stopped_at = n
            print(f"[main] STOPPED at source {n}: verify=fail; partial bench-report will be written",
                  file=sys.stderr)
            break

    partial = stopped_at is not None
    report = write_bench_report(state, branch, partial=partial)
    run_cmd("git add bench-report.md && git commit -m 'bench-report' && git push origin " + branch,
            cwd=str(WORKDIR / "wiki"), check=False)
    print(f"[main] bench-report at {report}", file=sys.stderr)
    print(f"[main] branch pushed: {branch}", file=sys.stderr)

    if partial:
        print("=== EXIT FAILED ===", file=sys.stderr)
        sys.exit(1)
    print("=== EXIT OK ===", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
