"""
D8 pilot production orchestrator — module 005 of "Психолог-консультант".

Ports the validated step7 architecture to production, with retrieval
plugged in (D8 Steps 4-7):
  - Python `for` loop top-orchestrator (Invariant A — bounded context)
  - Canonical skill v2 concept shape (Invariant B — `## Contributions
    by source` + per-touched-by `### <slug>` sub-sections)
  - source-author extracts excerpt+timestamp_sec from whisper segments
  - Per-source git commit on success (each source = its own commit)
  - Fail-fast on first verify=fail
  - Retrieval-augmented dedup: orchestrator rebuilds embed_helpers index
    before each source; source-author calls find-claims per-claim and
    feeds top-K candidates to idea-classifier (replaces bulk
    prior_claims_json that didn't scale past ~7 sources).

Validated on synth (step7_orchestrator.py): 4/4 verified=ok,
claims=21, REPEATED=7, CF=2, urls=12, top-orch events=5-6 per source,
6/6 concepts pass template v3.

Cyrillic paths preserved. Wikipedia rate-limit mitigated via
identifiable User-Agent + selective fact-check.

Usage:
  python3 orchestrator/run-d8-pilot.py
Env:
  LLM_BASE_URL, LLM_API_KEY, LLM_MODEL — vLLM config
  GITHUB_TOKEN — for git push (via gh auth)
  D8_PILOT_WORKDIR (optional) — default /tmp/d8-pilot-prod
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
from openhands.tools.task import TaskToolSet
from openhands.tools.delegate import DelegationVisualizer


# ─── Configuration ───────────────────────────────────────────────────────

WORKDIR = Path(os.environ.get("D8_PILOT_WORKDIR", "/tmp/d8-pilot-prod"))
RAW_REPO = "kurpatov-wiki-raw"
WIKI_REPO = "kurpatov-wiki-wiki"
GH_USER = "vasiliy-mikhailov"
SKILL_BRANCH = "skill-v2"
COURSE = "Психолог-консультант"
MODULE = "005 Природа внутренних конфликтов. Базовые психологические потребности"

# bench_grade.py path: container has it baked at /opt/forge/, host venv runs use the repo path.
BENCH_GRADE = (
    "/opt/forge/bench_grade.py" if Path("/opt/forge/bench_grade.py").exists()
    else "/home/vmihaylov/forge/labs/wiki-bench/evals/grade/bench_grade.py"
)

# Per-source bounds — see openhands-sdk-orchestration.md
TOP_ORCH_INPUT_TOKENS_PER_SOURCE_LIMIT = 100_000
TOP_ORCH_EVENTS_PER_SOURCE_LIMIT = 30


# ─── Sub-agent prompts (same as step7 — validated GREEN on synth) ────────

IDEA_CLASSIFIER_PROMPT = """\
You are idea-classifier. Each task message contains:
  - claim: the empirical claim text
  - lecture_transcript: full lecture transcript (read-only context)
  - candidate_prior_claims: top-K nearest prior claims from the
    retrieval index (JSON array of {claim, source_slug, score}).
    Max 5 candidates. Empty for source 0.

Step 1: Decide NEW vs REPEATED based on candidate_prior_claims.
  - If `claim` covers the same proposition as one of the candidates
    (paraphrase, restatement, or near-lexical match) AND the
    candidate's `score` is ≥ 0.78 → output
    `REPEATED from <source_slug from that candidate>`.
  - Otherwise (no candidate, all scores < 0.78, or the high-scoring
    candidate is on a clearly different proposition) → `NEW`.

Calibration of the score field (multilingual-e5-base, normalised):
  - score ≥ 0.85 — near-lexical match (definitely REPEATED)
  - 0.78 ≤ score < 0.85 — paraphrase of the same idea (REPEATED)
  - 0.65 ≤ score < 0.78 — related topic but different proposition (NEW)
  - score < 0.65 — not returned (filtered by retrieval)

Step 2: Pick a thematic_category from this list (or propose new kebab-case):
  architecture-of-the-method | neuroanatomy | psychology-and-instinct |
  culture-and-society | dynamics-and-conflict | philosophy-and-method |
  history-and-attribution | empirical-paradigms

Output ONE LINE: `<verdict> | category=<thematic-tag>`. Then call finish.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Each task contains:
  - claim
  - lecture_transcript

Step 1: `cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"`
Step 2: Pick BEST matching Wikipedia URLs. **Cite BOTH ru.wikipedia and
en.wikipedia URLs when both are returned for the same topic** (separate
each by ` ; `). Russian sources (ru.wiki) take priority when content
overlap is >70%; otherwise EN gives broader/deeper coverage.
Step 3: Scan lecture_transcript for speaker's caveats about THIS claim.
Step 4: Compose verdict + Notes.

Output exactly 3 lines:
  marker: <NEW|CONTRADICTS_FACTS|NO_MATCH>
  url: <best-Wikipedia-URL[;second-URL] or none>
  notes: <2-3 sentences combining (a) speaker's quote with «...», (b) Wikipedia
          status, (c) optional journal ref>

Then call finish with that 3-line text.
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator. You produce wiki concept articles per the
CANONICAL skill v2 contract from
`wiki/prompts/concept-article.md`. The shape is:

  ---
  slug: <kebab-case-id>
  first_introduced_in: <full source slug>
  touched_by:
    - <full source slug 1>
    - <full source slug 2>
  ---
  # <Russian title>

  ## Definition

  <2 paragraphs grounded in lecture content. If Kurpatov's usage
  diverges from mainstream — short paragraph labeled
  **How Kurpatov uses this**.>

  ## Contributions by source

  ### <source slug>
  - <bullet on what this source adds about the concept>
  - <bullet>
  - See [<short title>](../sources/<source slug>.md).
  - Timestamps `[mm:ss]` from that source's raw.json when they help.

  ## Related concepts

  - [<other-slug>](<other-slug>.md) — one-sentence relationship.

Task message contains:
  - concept_slug (kebab-case)
  - definition (one paragraph in Russian, derived from this source)
  - source_slug (the source CALLING you NOW — full slug,
    `Course/Module/<stem>` form)
  - lecture_transcript (this source's transcript)
  - related_concepts (list of related concept slugs)
  - this_source_bullets (list of 2-4 strings, what this source says
    about this concept; ≥30 chars per bullet)
  - this_source_timestamp_sec (int or null; e.g. 1842 → `[30:42]`)

Workflow:

Step 0. `pwd` to know the workspace absolute path. file_editor
        requires ABSOLUTE paths.

Step 1. Check existence:
        `ls wiki/data/concepts/<concept_slug>.md 2>/dev/null && \\
         echo EXISTS || echo NEW`

Step 2a. **If NEW** (file does not exist):
   Use file_editor (ABSOLUTE path) to CREATE with the canonical
   template above. The first `### <source slug>` sub-section in
   `## Contributions by source` is THIS source.

   Bullets in the sub-section: from `this_source_bullets`.
   Last bullet is always
   `- See [<short title>](../sources/<source_slug>.md). [<mm:ss>]`
   where `<mm:ss>` is from `this_source_timestamp_sec` (omit if null).

   Then update wiki/data/concept-index.json to register the concept:
   `python3 -c "import json; p='wiki/data/concept-index.json'; \\
    d=json.load(open(p)); d.setdefault('concepts',{})['<slug>']= \\
    {'first_introduced_in':'<source>'}; \\
    d.setdefault('processed_sources',[]); \\
    json.dump(d, open(p,'w'), ensure_ascii=False, indent=2)"`

Step 2b. **If EXISTS** (file already exists):
   APPEND a new `### <source_slug>` sub-section under
   `## Contributions by source`, BELOW all existing sub-sections and
   ABOVE `## Related concepts`. Use file_editor str_replace on the
   `## Related concepts` line as the anchor.

   Format of the new sub-section is the same as 2a.
   ALSO update frontmatter `touched_by:` to include `<source_slug>`
   (deduplicate).
   DO NOT modify `## Definition` or any earlier sub-section.
   DO NOT change `first_introduced_in`.

Step 3. Output `concept <slug> ready` and finish.

Rules:
- Each bullet in `this_source_bullets` ≥ 30 chars.
- The `### <source_slug>` heading uses the FULL source slug, not the
  short label (e.g. `Психолог-консультант/005 …/000 Вводная лекция …`).
- Cross-link target uses `../sources/<source_slug>.md` (relative path
  from concepts/ to sources/).
- Timestamp format: `[mm:ss]` if < 600s, `[mm:ss]` otherwise (always
  zero-padded). Brackets are square. Omit if `timestamp_sec` is null.
- If `this_source_bullets` describes a contradiction with an earlier
  source, quote both sides explicitly per the
  `CONTRADICTS EARLIER` rule.
"""

SOURCE_AUTHOR_PROMPT = f"""\
You are source-author (D8 pilot — concept template v3 + selective factcheck).

Task message: source_n, raw_path, target_path.

Tools: terminal, file_editor, task, finish, think.
Subagent_types for task(): idea-classifier, fact-checker, concept-curator.

Course: `{COURSE}`
Module: `{MODULE}`

Cyrillic paths: course / module are LITERAL — do NOT romanize.

## Workflow

### A. Read transcript + segments
```
python3 -c "import json; d=json.load(open('<raw_path>')); print(json.dumps({{'segments': d['segments'], 'duration': int(d['info']['duration'])}}))"
```
**FAIL-FAST**: if JSON read fails — call finish with
  `failed: cannot read transcript at <raw_path>: <reason>`.

Save segments list (each has start, end, text). You'll search them
in step E for excerpts/timestamps.

### B. (Removed — retrieval is per-claim in step D)

The idea-classifier no longer receives the bulk `prior_claims_json`.
Instead, the orchestrator pre-builds a numpy + sqlite retrieval index
of all prior claims (across every committed source). In step D you
will call `embed_helpers.py find-claims` per-claim to fetch the
top-K nearest candidates (~3 KB context) and pass those to the
classifier.

Skip directly to step C.

### C. Extract claims (LLM reasoning, no tools)
Identify ALL distinct empirical claims. Density target:
**~1 claim per 60 seconds of transcript**.
For a 50-minute lecture this means **≈ 50 claims, NOT 13**.
For a 20-minute lecture this means **≈ 20 claims, NOT 5-7**.
Do NOT under-extract. If you have <30 claims for a lecture above 30 min,
re-scan the transcript for missed propositions.

For EACH claim: pick 2-5 concept slugs (kebab-case), assign needs_factcheck.

`needs_factcheck: false` — confident: speaker's own concepts, well-known
anatomy, methodological framings.
`needs_factcheck: true` — uncertain: specific dates, named-person
attributions, specific numbers, controversial. Default true when unsure.

### D. Per-claim sub-agent calls — record marker for EACH claim
For claim i (sequential):
  1. RETRIEVE top-5 prior claim candidates via the embed_helpers CLI:
     ```
     python3 /opt/forge/embed_helpers.py find-claims wiki \\
       --claim "<claim_text>" --k 5
     ```
     The output is a JSON array of objects
     `[{{"claim": "...", "source_slug": "...", "score": 0.91}}, ...]`
     (empty `[]` for source 0 or when no neighbours pass the
     threshold). Capture this verbatim as `candidate_prior_claims`.
  2. ALWAYS task(idea-classifier, prompt=claim + lecture +
     candidate_prior_claims)
     → parse `<verdict> | category=<theme>`
  3. IF needs_factcheck[i]: task(fact-checker, prompt=claim + lecture)
     → parse marker/url/notes

  Combine into final_marker[i]:
    - factchecker said CONTRADICTS_FACTS → `[CONTRADICTS_FACTS]`
    - elif classifier said REPEATED      → `[REPEATED (from: <slug>)]`
    - else                                → `[NEW]`

  ⚠️ Persist (claim_text, final_marker, url, notes, thematic_category)
     for every claim — you will need ALL of these in step F.

⚙️ Retrieval contract: the index is built/updated by the orchestrator
   BEFORE this source-author runs (covers every prior committed
   source). You do NOT rebuild it. You only QUERY via find-claims.

### E. Concept curator calls — for EVERY concept in concepts_touched

🔴 Call concept-curator for EVERY concept the lecture mentions, NOT just
the ones first-introduced here. The curator handles NEW vs EXISTS:
- NEW → creates a new concept article via canonical skill v2 template
- EXISTS → appends a new `### <source_slug>` sub-section under
  `## Contributions by source`, updates `touched_by:` frontmatter

For each concept slug in concepts_touched:
  - Find segments where the concept is discussed (search by Russian
    title or kebab keyword translation). Pick 2-4 substantive bullets
    summarizing what THIS source adds about THIS concept (each ≥ 30
    chars). These go in the `### <source_slug>` sub-section.
  - Find the FIRST such segment's `start` field (round int) as
    `timestamp_sec` — used as `[mm:ss]` annotation on the See-link
    bullet.
  - task(concept-curator, prompt with: concept_slug, definition
    (1 paragraph grounded in lecture, used only if NEW), source_slug
    (full slug — Course/Module/Stem form), lecture_transcript,
    related_concepts, this_source_bullets (the 2-4 strings),
    this_source_timestamp_sec)

Do NOT skip concepts you think "already exist" — the curator handles
that case via the EXISTS branch. Skipping is the source of cross-ref
violations: source.md lists slug in `concepts_touched` but no concept
file exists yet.

Strict subset rule: `concepts_introduced ⊂ concepts_touched`.
- `concepts_introduced` = slugs you BELIEVE are first-mentioned in this
  source (curator EXISTS-check confirms or downgrades them).
- `concepts_touched` = ALL slugs mentioned, including REPEATED from
  prior sources.
- Always: introduced ⊆ touched. Never: introduced = touched (unless
  every concept is genuinely new, which is unusual past source 0).

### F. Assemble source.md (CRITICAL — write to target_path)

Frontmatter (between --- fences, FIRST):
  slug: <derive: drop "wiki/data/sources/" prefix from target_path, drop ".md">
  course: {COURSE}
  module: {MODULE}
  extractor: whisper
  source_raw: <raw_path>
  duration_sec: <integer from STEP A>
  language: ru
  processed_at: 2026-04-26T00:00:00Z
  fact_check_performed: true
  concepts_touched: [<all 5+ slugs from claims>]
  concepts_introduced: [<STRICT subset: only first-mentioned-here>]

CRITICAL: slug must NOT include "data/sources/" or "wiki/" prefix.
CRITICAL: concepts_introduced ⊂ concepts_touched (strict subset).

Body — EXACTLY 5 `## ` sections in order. Use `# <Russian title>` for H1.

  `## TL;DR` — one paragraph
  `## Лекция (пересказ: только NEW и проверенное)` — 3-5 paragraphs
    with inline `[<concept-slug>](../../../concepts/<slug>.md)` links
  `## Claims — provenance and fact-check` — numbered list. EVERY entry:
       `<n>. <claim_text> <final_marker[n]>`
       <notes paragraph if fact-checked>
       — <url> (if factchecker provided)
    🔴 EVERY claim MUST end with one of `[NEW]`, `[REPEATED (from: ...)]`,
       or `[CONTRADICTS_FACTS]`. NO bare claims allowed.
  `## New ideas (verified)` — bullets grouped by thematic_category:
       `**<Theme>**`
       `- <bullet> ([<concept-link>](...))`
  `## All ideas` — flat bullet list

mkdir -p target dir before file_editor (ABSOLUTE path).

### F.6. Update concept-index.json

After writing source.md, append the source slug to
`wiki/data/concept-index.json` `processed_sources` list (deduplicate).
Use python3 inline:
```
python3 -c "import json; p='wiki/data/concept-index.json'; \\
  d=json.load(open(p)); s='<full source slug>'; \\
  d.setdefault('processed_sources', []); \\
  s in d['processed_sources'] or d['processed_sources'].append(s); \\
  json.dump(d, open(p,'w'), ensure_ascii=False, indent=2)"
```

This is the registry consumed by future runs to know which sources are
already canonicalized. Skipping this step causes cross-ref violations
in bench_grade.py.

### G. Finish: `done` (or `failed: <reason>`).
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
    # Clean *contents* of WORKDIR rather than the directory itself —
    # avoids EBUSY on mount points (containers).
    WORKDIR.mkdir(parents=True, exist_ok=True)
    if any(WORKDIR.iterdir()):
        print(f"[setup] cleaning existing contents of {WORKDIR}", file=sys.stderr)
        for child in WORKDIR.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()

    # git author identity for in-container commits — env vars or fallback.
    user_email = os.environ.get("GIT_AUTHOR_EMAIL", "bench@wiki-bench.local")
    user_name = os.environ.get("GIT_AUTHOR_NAME", "wiki-bench")
    subprocess.run(["git", "config", "--global", "user.email", user_email], check=True)
    subprocess.run(["git", "config", "--global", "user.name", user_name], check=True)

    # GitHub token: env first (canonical for containers), then `gh` CLI fallback (host).
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    if not token:
        raise RuntimeError("no GITHUB_TOKEN env nor `gh auth token` available")
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{RAW_REPO}.git raw", cwd=str(WORKDIR))
    run_cmd(f"git clone -q https://x-access-token:{token}@github.com/{GH_USER}/{WIKI_REPO}.git wiki", cwd=str(WORKDIR))
    run_cmd(f"cd wiki && git checkout {SKILL_BRANCH} && git pull --ff-only", cwd=str(WORKDIR))

    served = os.environ.get("LLM_MODEL", "openai/qwen3.6-27b-fp8").replace("openai/", "")
    branch = f"experiment/D8-pilot-{date.today().isoformat()}-{served}"
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


def build_inputs(sources):
    inputs = []
    for s in sources:
        n = s["index"]
        abs_raw = s["raw_json_path"]
        prefix = str(WORKDIR) + "/"
        if not abs_raw.startswith(prefix):
            raise RuntimeError(f"unexpected raw_json_path: {abs_raw}")
        raw_path = abs_raw[len(prefix):]
        target_path = f"wiki/data/sources/{s['slug']}.md"
        inputs.append((n, raw_path, target_path, s["slug"]))
    return inputs


def setup_agents():
    register_tool("task_tool_set", TaskToolSet)
    for spec in [
        ("idea-classifier", "Classify NEW vs REPEATED + thematic_category.",
         [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "factcheck.py + paragraph Notes.",
         ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Concept template v3 — backlinks + excerpts.",
         ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Process ONE lecture; selective factcheck; concept v3.",
         ["terminal", "file_editor", "task_tool_set"], SOURCE_AUTHOR_PROMPT),
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


def commit_and_push_per_source(n, slug, branch):
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


def measure_top_orch(conv: Conversation):
    n_events = len(conv.state.events)
    total_input = 0
    for ev in conv.state.events:
        ts = getattr(ev, "tokens_input", None)
        if ts is not None:
            total_input += int(ts)
    return n_events, total_input


# ─── Concept template v3 validator (L1.5) ──────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)
_TOUCHED_BY_RE = re.compile(r"^touched_by:\s*\n((?:\s+-\s+.+\n)+)", re.MULTILINE)
_BULLET_RE = re.compile(
    r"^- \[([^\]]+)\]\((\.\./sources/[^)]+)\)\s*"
    r"(.+?)(?=\n- \[|\n## |\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_frontmatter(text):
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip() if v.strip() else None
    tb = _TOUCHED_BY_RE.search(m.group(1))
    if tb:
        fm["touched_by"] = [
            ln.strip().lstrip("- ").strip()
            for ln in tb.group(1).splitlines() if ln.strip()
        ]
    return fm


def validate_concept_v3(concept_path):
    """Canonical skill v2 concept shape (matches bench_grade.py L1.5):

      ## Definition
      ## Contributions by source
        ### <source-slug 1>
          - bullets …
          - See [<short title>](../sources/<slug>.md). [optional mm:ss]
        ### <source-slug 2>
          - …
      ## Related concepts
    """
    violations = []
    name = concept_path.name
    if name == "_template.md":
        return violations
    text = concept_path.read_text()
    fm = parse_frontmatter(text)
    touched_by = fm.get("touched_by", [])
    if not touched_by:
        violations.append(f"{name}: touched_by empty/missing")
        return violations
    if "## Definition" not in text:
        violations.append(f"{name}: ## Definition heading missing")
    if "## Contributions by source" not in text:
        violations.append(f"{name}: ## Contributions by source heading missing")
        return violations
    contrib_match = re.search(
        r"^## Contributions by source\s*\n(.*?)(?=\n## |\Z)",
        text, re.MULTILINE | re.DOTALL,
    )
    contrib_section = contrib_match.group(1) if contrib_match else ""
    sub_headings = re.findall(r"^### (.+)$", contrib_section, re.MULTILINE)
    sub_set = {h.strip() for h in sub_headings}
    for slug in touched_by:
        if slug not in sub_set:
            violations.append(
                f"{name}: touched_by '{slug[:60]}…' has no "
                f"### sub-section in Contributions by source"
            )
    if "## Related concepts" not in text:
        violations.append(f"{name}: ## Related concepts heading missing")
    return violations


# ─── Bench report ──────────────────────────────────────────────────────

def write_bench_report(state, branch, partial=False):
    report = WORKDIR / "wiki" / "bench-report.md"
    lines = [f"# bench report — D8 pilot {'(partial)' if partial else ''}",
             "", f"branch: `{branch}`",
             f"sources processed: {len(state)}/7",
             "",
             "## Architectural invariants",
             "",
             "- INVARIANT A (top-orch context bounded per source): see "
             "per-source events column",
             "- INVARIANT B (concept template v3): see concept_violations row",
             "",
             "## Per-source", ""]
    for entry in state:
        v = entry.get("verify", {})
        m = entry.get("orch_metrics", {})
        lines.append(
            f"- source {entry['n']}: verified={v.get('verified','?')}, "
            f"claims={v.get('claims_total','?')} "
            f"(NEW={v.get('claims_NEW','?')}, "
            f"REPEATED={v.get('claims_REPEATED','?')}, "
            f"CF={v.get('claims_CF','?')}, "
            f"unmarked={v.get('claims_unmarked','?')}), "
            f"urls={v.get('wiki_url_count','?')}, "
            f"orch_events={m.get('events','?')}, "
            f"commit={entry.get('commit','?')}"
        )
    lines.append("")
    if partial:
        lines.append("## Stop point\n\nRun stopped fail-fast at first failure.")
    report.write_text("\n".join(lines))


def main():
    print("=" * 70, file=sys.stderr)
    print("D8 pilot production orchestrator (Python-loop top-orch + concept v3)", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    branch, served = setup_workspace()
    sources = list_sources()
    print(f"[main] {len(sources)} sources in module 005", file=sys.stderr)
    if not sources:
        print("FATAL: no sources found", file=sys.stderr); sys.exit(2)

    inputs = build_inputs(sources)
    setup_agents()

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="d8-pilot",
    )

    # ─── PYTHON-LOOP TOP-ORCHESTRATOR (INVARIANT A) ──────────────────
    state = []
    stopped_at = None
    t0_total = time.time()

    # Resolve embed_helpers.py path (container-baked vs host).
    embed_helpers_path = (
        "/opt/forge/embed_helpers.py"
        if Path("/opt/forge/embed_helpers.py").exists()
        else "/home/vmihaylov/forge/labs/wiki-bench/orchestrator/embed_helpers.py"
    )

    for (n, raw_path, target_path, slug) in inputs:
        print(f"\n{'=' * 70}", file=sys.stderr)
        print(f"=== SRC {n}: {slug}", file=sys.stderr)
        print(f"{'=' * 70}", file=sys.stderr)

        # ── Rebuild retrieval index over committed sources (every prior
        # source.md + concept.md is now embedded). For source 0 the
        # index will be empty; for source N≥1 it covers sources 0..N-1.
        # The source-author calls find-claims via embed_helpers.py.
        print(f"[retrieval] rebuilding index before SRC {n}…", file=sys.stderr)
        rebuild_r = subprocess.run(
            ["python3", embed_helpers_path, "rebuild", str(WORKDIR / "wiki")],
            capture_output=True, text=True,
        )
        if rebuild_r.returncode != 0:
            print(f"!!! retrieval rebuild failed before SRC {n}: "
                  f"{rebuild_r.stderr[:400]}", file=sys.stderr)
            stopped_at = n
            state.append({"n": n, "slug": slug,
                          "stopped": "retrieval_rebuild_fail"})
            break
        else:
            print(f"[retrieval] {rebuild_r.stdout.strip()}", file=sys.stderr)

        # FRESH Conversation per source
        main_agent = Agent(llm=llm, tools=[Tool(name="task_tool_set")])
        conv = Conversation(
            agent=main_agent, workspace=str(WORKDIR),
            visualizer=DelegationVisualizer(name=f"OrchD8.src{n}"),
        )
        msg = (
            f"Process source N={n}. raw_path={raw_path}. "
            f"target_path={target_path}. "
            "Use the `task` tool with subagent_type='source-author' and "
            f"prompt='Process source N={n}. raw_path={raw_path}. "
            f"target_path={target_path}. Follow your system_prompt.'\n"
            "Wait for `done` ack from source-author, then finish."
        )

        t0 = time.time()
        conv.send_message(msg)
        conv.run()
        wall_min = (time.time() - t0) / 60

        n_events, input_tokens = measure_top_orch(conv)
        orch_metrics = {"events": n_events, "input_tokens": input_tokens, "wall_min": wall_min}
        print(f"=== SRC {n}: top-orch events={n_events}, input_tokens={input_tokens:,}, "
              f"wall {wall_min:.1f}min ===", file=sys.stderr)

        # Hard architectural assert (Invariant A)
        if n_events > TOP_ORCH_EVENTS_PER_SOURCE_LIMIT:
            print(f"!!! INVARIANT A BROKEN: top-orch events={n_events} > {TOP_ORCH_EVENTS_PER_SOURCE_LIMIT}",
                  file=sys.stderr)
            stopped_at = n
            state.append({"n": n, "slug": slug, "orch_metrics": orch_metrics,
                          "stopped": "invariant_A"})
            break

        # Functional verify
        v = verify_source(n)
        if v.get("verified") == "ok":
            try:
                commit = commit_and_push_per_source(n, slug, branch)
            except Exception as e:
                # Don't let a transient git/push failure stop the whole pipeline;
                # source.md is on disk and verify=ok, that's the canonical truth.
                commit = f"commit-failed: {type(e).__name__}: {e}"
                print(f"=== SRC {n}: commit_and_push failed but verify=ok, continuing: {e}",
                      file=sys.stderr)
            state.append({"n": n, "slug": slug, "verify": v,
                          "orch_metrics": orch_metrics, "commit": commit})
            print(f"=== SRC {n}: verified=ok, claims={v.get('claims_total')}, "
                  f"REPEATED={v.get('claims_REPEATED')}, CF={v.get('claims_CF')}, "
                  f"commit={commit} ===", file=sys.stderr)
        else:
            stopped_at = n
            state.append({"n": n, "slug": slug, "verify": v,
                          "orch_metrics": orch_metrics, "stopped": "verify_fail"})
            print(f"!!! SRC {n}: verify=fail, violations={v.get('violations')[:3]}",
                  file=sys.stderr)
            break

    wall_total_min = (time.time() - t0_total) / 60
    print(f"\n[main] total wall: {wall_total_min:.1f} min", file=sys.stderr)

    # ─── INVARIANT B — concept template v3 validation ──────────────
    print(f"\n{'=' * 70}", file=sys.stderr)
    print("=== INVARIANT B (concept template v3) ===", file=sys.stderr)
    print(f"{'=' * 70}", file=sys.stderr)
    concepts = list((WORKDIR / "wiki" / "data" / "concepts").glob("*.md"))
    template_violations = []
    for c in concepts:
        v = validate_concept_v3(c)
        template_violations.extend(v)
    if template_violations:
        print(f"  TEMPLATE VIOLATIONS ({len(template_violations)}):", file=sys.stderr)
        for v in template_violations[:15]:
            print(f"    - {v}", file=sys.stderr)
    else:
        print(f"  all {len(concepts)} concepts pass template v3", file=sys.stderr)

    # ─── Bench report + commit ─────────────────────────────────────
    partial = stopped_at is not None
    write_bench_report(state, branch, partial=partial)
    run_cmd("git add bench-report.md && git commit -m 'bench-report' && git push origin " + branch,
            cwd=str(WORKDIR / "wiki"), check=False)
    print(f"\n[main] branch pushed: {branch}", file=sys.stderr)

    # ─── Final summary ─────────────────────────────────────────────
    sources_ok = sum(1 for s in state if s.get("verify", {}).get("verified") == "ok")
    total_claims = sum(s.get("verify", {}).get("claims_total", 0) for s in state)
    total_repeated = sum(s.get("verify", {}).get("claims_REPEATED", 0) for s in state)
    total_cf = sum(s.get("verify", {}).get("claims_CF", 0) for s in state)

    print(f"\nFINAL: {sources_ok}/{len(inputs)} sources verified=ok", file=sys.stderr)
    print(f"agg: claims={total_claims}, REPEATED={total_repeated}, CF={total_cf}", file=sys.stderr)
    print(f"concepts: {len(concepts)} (template v3 violations: {len(template_violations)})",
          file=sys.stderr)
    print(f"per-source orch events: "
          f"{[s.get('orch_metrics', {}).get('events', '?') for s in state]}", file=sys.stderr)

    if partial:
        print("\n=== EXIT FAILED ===", file=sys.stderr); sys.exit(1)
    print("\n=== EXIT OK ===", file=sys.stderr); sys.exit(0)


if __name__ == "__main__":
    main()
