"""
Step 9 — Retrieval-augmented dedup synth gate (D8 Steps 4-7).

Falsifies the claim that the production source-author prompt actually
exercises `embed_helpers.py find-claims` per claim. Pilot v3 (2026-04-27)
showed the agent calling find-claims 8× total across 65 idea-classifier
delegations — i.e. retrieval was being skipped on most claims, and
REPEATED stayed at 0 even when the index contained relevant prior claims.

Synth scenario (reuses tests/synthetic/fixtures/raw/001.json + 002.json):
  - Source 001 introduces принцип Парето (80/20) + закон Мура.
  - Source 002 paraphrases принцип Парето + introduces Эверест.

After source 001 commits and the retrieval index is rebuilt,
source 002's source-author MUST:
  - Call find-claims for each of its claims (we count CLI invocations).
  - The classifier MUST output REPEATED for at least the Парето claim,
    because source 001's Парето claim is in the index with similarity > 0.85.

Falsification criteria (the gate):
  - 2/2 sources verified=ok
  - source 002 has claims_REPEATED ≥ 2
    (Парето principle definition + Парето historical attribution)
  - find-claims CLI was invoked ≥ 1 per claim of source 002
    (we sample by counting `find-claims` substrings in stderr — at least
    as many as claims_total of source 002)

If any assert fails — the prompt does not enforce retrieval. Iterate.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from openhands.sdk import (
    LLM, Agent, Conversation, Tool,
    register_agent, agent_definition_to_factory,
)
from openhands.sdk.subagent import AgentDefinition
from openhands.sdk.tool import register_tool
from openhands.tools.task import TaskToolSet
from openhands.tools.delegate import DelegationVisualizer


WS = Path("/tmp/step9-orch-ws")
WIKI = WS / "wiki"
# FIXTURES must work both on host (host path) and inside container
# (where the lab is bind-mounted at /lab).
FIXTURES = (
    Path("/lab/tests/synthetic/fixtures")
    if Path("/lab/tests/synthetic/fixtures").exists()
    else Path("/home/vmihaylov/forge/labs/wiki-bench/tests/synthetic/fixtures")
)
BENCH_GRADE = (
    "/opt/forge/bench_grade.py" if Path("/opt/forge/bench_grade.py").exists()
    else "/home/vmihaylov/forge/labs/wiki-bench/evals/grade/bench_grade.py"
)
EMBED_HELPERS = (
    "/opt/forge/embed_helpers.py" if Path("/opt/forge/embed_helpers.py").exists()
    else "/home/vmihaylov/forge/labs/wiki-bench/orchestrator/embed_helpers.py"
)
SOURCE_NUMBERS = [1, 2]
TOP_ORCH_EVENTS_PER_SOURCE_LIMIT = 30


# ─── Sub-agent prompts (mirror run-d8-pilot.py exactly) ─────────────────

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

Step 2: Pick a thematic_category.
Output ONE LINE: `<verdict> | category=<thematic-tag>`. Then call finish.
"""

FACT_CHECKER_PROMPT = """\
You are fact-checker. Each task contains: claim, lecture_transcript.

Step 1: `cd wiki && python3 skills/benchmark/scripts/factcheck.py "<claim>"`
Step 2: Pick BEST matching Wikipedia URL.
Step 3: Compose verdict + Notes.
Output 3 lines: marker / url / notes. Then call finish.
"""

CONCEPT_CURATOR_PROMPT = """\
You are concept-curator. Produce wiki concept articles in canonical
skill v2 shape:

  ---
  slug: <kebab-case-id>
  first_introduced_in: <full source slug>
  touched_by:
    - <full source slug 1>
  ---
  # <Russian title>

  ## Definition

  <2 paragraphs grounded in lecture content.>

  ## Contributions by source

  ### <source slug>
  - <bullet ≥30 chars>
  - <bullet ≥30 chars>
  - See [<short title>](../sources/<source slug>.md).

  ## Related concepts

  - [<other-slug>](<other-slug>.md) — relationship.

Task message contains: concept_slug, definition, source_slug,
lecture_transcript, related_concepts, this_source_bullets,
this_source_timestamp_sec.

Workflow:
1. `ls wiki/data/concepts/<concept_slug>.md` to check exists.
2. If NEW: file_editor (ABSOLUTE path) → CREATE per template.
   Update wiki/data/concept-index.json.
3. If EXISTS: file_editor str_replace → APPEND a new
   `### <source_slug>` sub-section under `## Contributions by source`,
   above `## Related concepts`. Update frontmatter `touched_by:`.
4. Output `concept <slug> ready` and finish.
"""

SOURCE_AUTHOR_PROMPT = f"""\
You are source-author (D8 retrieval-augmented dedup, synth step 9).

Task message: source_n, raw_path, target_path.

Tools: terminal, file_editor, task, finish, think.
Subagent_types for task(): idea-classifier, fact-checker, concept-curator.

Course: `ТестКурс`
Module: `999 Тестовый модуль`

## Workflow

### A. Read transcript
```
python3 -c "import json; d=json.load(open('<raw_path>')); \\
  print(json.dumps({{'segments': d['segments'], 'duration': int(d['info']['duration'])}}))"
```

### B. (Removed — retrieval is per-claim in step D)

### C. Extract claims (LLM reasoning, no tools)
Identify ALL distinct empirical claims (~1 per 60s; for 200s lecture
expect ~3-4 claims).

For EACH claim: pick 1-3 concept slugs (kebab-case), assign
needs_factcheck (default true).

### D. Per-claim sub-agent calls — record marker for EACH claim

🔴 MANDATORY: For EVERY claim, BEFORE calling idea-classifier, call
   `embed_helpers.py find-claims` to fetch candidate prior claims.
   This is NOT optional. Skipping it breaks the dedup contract and
   the synth gate will FAIL.

For claim i (sequential):
  1. RETRIEVE top-5 prior claim candidates:
     ```
     python3 /opt/forge/embed_helpers.py find-claims wiki \\
       --claim "<claim_text>" --k 5
     ```
     Output is JSON: `{{"results": [{{...}}], ...}}`. Capture the
     "results" array verbatim as `candidate_prior_claims`.
  2. ALWAYS task(idea-classifier, prompt=claim + lecture +
     candidate_prior_claims) → parse `<verdict> | category=<theme>`
  3. IF needs_factcheck[i]: task(fact-checker, prompt=claim + lecture)
     → parse marker/url/notes

  Combine into final_marker[i]:
    - factchecker said CONTRADICTS_FACTS → `[CONTRADICTS_FACTS]`
    - elif classifier said REPEATED      → `[REPEATED (from: <slug>)]`
    - else                                → `[NEW]`

### E. Concept curator calls — for EVERY concept in concepts_touched

For each concept slug in concepts_touched:
  - Find segments mentioning the concept; pick 1-2 substantive bullets
    (each ≥30 chars).
  - First segment's `start` (round int) → timestamp_sec.
  - task(concept-curator, …)

### F. Assemble source.md (CRITICAL — write to target_path)

Frontmatter:
  slug: <derive: drop "wiki/data/sources/" prefix from target_path, drop ".md">
  course: ТестКурс
  module: 999 Тестовый модуль
  extractor: whisper
  source_raw: <raw_path>
  duration_sec: <integer from STEP A>
  language: ru
  processed_at: 2026-04-27T00:00:00Z
  fact_check_performed: true
  concepts_touched: [<all slugs>]
  concepts_introduced: [<STRICT subset>]

Body — EXACTLY 5 `## ` sections in order. Use `# <Russian title>`.

  `## TL;DR` — paragraph
  `## Лекция (пересказ: только NEW и проверенное)` — 2-3 paragraphs
  `## Claims — provenance and fact-check` — numbered list. EVERY entry:
       `<n>. <claim_text> <final_marker[n]>`
       — <url> (if factchecker provided)
    🔴 EVERY claim ends with [NEW], [REPEATED (from: ...)], or
       [CONTRADICTS_FACTS]. NO bare claims.
  `## New ideas (verified)` — bullets
  `## All ideas` — flat bullets

mkdir -p target dir before file_editor (ABSOLUTE path).

### F.6. Update concept-index.json

After source.md is written, append source slug to
wiki/data/concept-index.json `processed_sources`.

### G. Finish: `done` (or `failed: <reason>`).
"""


# ─── Helpers ──────────────────────────────────────────────────────────────

def setup_workspace():
    """Build /tmp/step9-orch-ws fresh from fixtures.

    WS may itself be a bind-mount (Device or resource busy on rmtree),
    so we clean its *contents* instead of removing the directory.
    """
    WS.mkdir(parents=True, exist_ok=True)
    for child in WS.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    (WS / "raw").mkdir(parents=True)
    (WIKI / "data" / "sources").mkdir(parents=True)
    (WIKI / "data" / "concepts").mkdir(parents=True)
    (WIKI / "skills" / "benchmark" / "scripts").mkdir(parents=True)

    # Copy raw fixtures (only 001, 002 — the Парето repetition pair).
    for n in SOURCE_NUMBERS:
        shutil.copy(FIXTURES / "raw" / f"{n:03d}.json", WS / "raw" / f"{n:03d}.json")

    # Copy helper scripts (factcheck, get_known_claims).
    for s in ["factcheck.py", "get_known_claims.py"]:
        shutil.copy(FIXTURES / "wiki" / "scripts" / s,
                    WIKI / "skills" / "benchmark" / "scripts" / s)

    # Empty concept-index.json.
    (WIKI / "data" / "concept-index.json").write_text(
        json.dumps({"sources": [], "concepts": [], "processed_sources": []},
                   ensure_ascii=False, indent=2)
    )

    # Empty concept _template.md so bench_grade's L1.5 doesn't choke.
    (WIKI / "data" / "concepts" / "_template.md").write_text(
        "---\nslug: _template\nfirst_introduced_in: \ntouched_by: []\n---\n"
        "# Template\n\n## Definition\n\n(template)\n"
    )

    print(f"[setup] workspace ready at {WS}", file=sys.stderr)


def measure_top_orch(conv: Conversation):
    n_events = len(conv.state.events)
    return n_events


def rebuild_index(label):
    print(f"[retrieval] rebuilding index ({label})…", file=sys.stderr)
    r = subprocess.run(
        ["python3", EMBED_HELPERS, "rebuild", str(WIKI)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"rebuild failed: {r.stderr[:400]}")
    print(f"[retrieval] {r.stdout.strip()}", file=sys.stderr)


def main():
    setup_workspace()

    register_tool("task_tool_set", TaskToolSet)
    for spec in [
        ("idea-classifier", "Classify NEW vs REPEATED via retrieval candidates.",
         [], IDEA_CLASSIFIER_PROMPT),
        ("fact-checker", "factcheck.py + Notes.",
         ["terminal"], FACT_CHECKER_PROMPT),
        ("concept-curator", "Canonical skill v2 concept shape.",
         ["terminal", "file_editor"], CONCEPT_CURATOR_PROMPT),
        ("source-author", "Process ONE lecture; per-claim find-claims; selective factcheck.",
         ["terminal", "file_editor", "task_tool_set"], SOURCE_AUTHOR_PROMPT),
    ]:
        name, desc, tools, prompt = spec
        ad = AgentDefinition(name=name, description=desc, tools=tools, system_prompt=prompt)
        register_agent(ad.name, agent_definition_to_factory(ad), ad)

    llm = LLM(
        model=os.getenv("LLM_MODEL", "openai/qwen3.6-27b-fp8"),
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL"),
        usage_id="step9-loop",
    )

    per_source_metrics = []
    src_results = {}

    for n in SOURCE_NUMBERS:
        rebuild_index(f"before SRC {n}")

        raw = json.loads((WS / "raw" / f"{n:03d}.json").read_text())
        first_words = " ".join(raw["segments"][0]["text"].split()[:5])
        target = f"wiki/data/sources/ТестКурс/999 Тестовый модуль/{n:03d} {first_words}.md"
        slug = target[len("wiki/data/sources/"):-len(".md")]

        main_agent = Agent(llm=llm, tools=[Tool(name="task_tool_set")])
        conv = Conversation(
            agent=main_agent, workspace=str(WS),
            visualizer=DelegationVisualizer(name=f"OrchStep9.src{n}"),
        )
        msg = (
            f"Process source N={n}. raw_path=raw/{n:03d}.json. "
            f"target_path={target}. "
            "Use the `task` tool with subagent_type='source-author' and "
            f"prompt='Process source N={n}. raw_path=raw/{n:03d}.json. "
            f"target_path={target}. Follow your system_prompt.'\n"
            "Wait for `done` ack from source-author, then finish."
        )
        print(f"\n=== SRC {n}: {slug}", file=sys.stderr)
        conv.send_message(msg)
        conv.run()

        n_events = measure_top_orch(conv)
        per_source_metrics.append({"source": n, "events": n_events})
        print(f"=== SRC {n}: top-orch events={n_events} ===", file=sys.stderr)

        assert n_events <= TOP_ORCH_EVENTS_PER_SOURCE_LIMIT, (
            f"INVARIANT A BROKEN: source {n} top-orch has {n_events} events"
        )

        # Verify functional via bench_grade.
        result = subprocess.run(
            ["python3", BENCH_GRADE, str(WIKI),
             "--single-source", str(n), "--single-source-json"],
            capture_output=True, text=True,
        )
        try:
            v = json.loads(result.stdout)
        except Exception:
            v = {"verified": "fail",
                 "violations": [f"non-JSON: {result.stdout[:200]}"]}
        src_results[n] = v
        print(f"=== SRC {n}: verified={v.get('verified')}, "
              f"claims={v.get('claims_total')}, "
              f"REPEATED={v.get('claims_REPEATED')}, "
              f"CF={v.get('claims_CF')} ===", file=sys.stderr)

    # ─── ASSERTS — the gate ──────────────────────────────────────────
    print("\n=== STEP 9 GATE ===", file=sys.stderr)
    ok_sources = sum(1 for v in src_results.values()
                     if v.get("verified") == "ok")
    src2_repeated = src_results.get(2, {}).get("claims_REPEATED", 0)
    src2_claims = src_results.get(2, {}).get("claims_total", 0)

    print(f"  verified ok: {ok_sources}/2", file=sys.stderr)
    print(f"  src 2 claims: {src2_claims}", file=sys.stderr)
    print(f"  src 2 REPEATED: {src2_repeated}", file=sys.stderr)

    pass_verified = ok_sources == 2
    pass_repeated = src2_repeated >= 2

    if pass_verified and pass_repeated:
        print("\n=== STEP 9 PASS ===", file=sys.stderr)
        print("  retrieval is wired and exercised end-to-end ✓", file=sys.stderr)
        sys.exit(0)
    else:
        print("\n=== STEP 9 FAIL ===", file=sys.stderr)
        if not pass_verified:
            print(f"  verified: {ok_sources}/2 (need 2/2)", file=sys.stderr)
            for n, v in src_results.items():
                if v.get("verified") != "ok":
                    print(f"    src {n} violations: {v.get('violations', [])[:3]}",
                          file=sys.stderr)
        if not pass_repeated:
            print(f"  src 2 REPEATED: {src2_repeated} (need ≥ 2)", file=sys.stderr)
            print(f"    → agent likely skipped find-claims; or candidates "
                  f"didn't cross 0.85 score; check logs.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
