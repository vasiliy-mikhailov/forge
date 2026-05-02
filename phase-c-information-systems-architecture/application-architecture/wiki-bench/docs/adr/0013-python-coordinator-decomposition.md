# ADR 0013 — Decompose source-author monolith into a Python coordinator

Status: Accepted (implemented 2026-04-30)
Date: 2026-04-30
Lab: wiki-bench
Phase: C (information systems architecture / application architecture)
Related: ADR 0010 (test fidelity), ADR 0011 (NFC/NFD), P5 (cheap experiment), P6 (completeness over availability)

## Context

K1 v2 (2026-04-29 night → 2026-04-30 morning) finished 16 sources verified=ok
and crashed on SRC 17 with a verify-fail. Post-mortem in
[`й.md` § "The shape of a closing tag"](../../../../../й.md). Root cause:

1. The source-author agent's LLM (Qwen3.6-27B-FP8 over LiteLLM
   OpenAI-compatible) occasionally drifts from OpenAI-style JSON tool
   calling to Anthropic-style XML mid-output.
2. When that drift produces an *end-of-turn* output containing only
   closing XML tags (no opening tags, no parseable tool call), the
   OpenHands SDK has no action to execute and silently treats the
   response as a completed turn with a plain-text final message.
3. The top-orchestrator receives the source-author task as `completed`
   with the agent's mid-thought narrative as the result.
4. `verify_source` polls the target path; the file isn't there;
   verify-fail.

Per-call statistics (n=17 sources) confirm this is **not** a
context-pressure failure: SRC 17's last-call input was 40 K tokens,
the smallest of any source. Successful sources had max single-call
inputs from 155 K to 1.22 M and survived. The failure mode is
*agency-fragility*: the agent has unstructured authority to decide
what to do next, and any one of {wrong format, hallucinated finish,
SDK silent acceptance, lost workflow state} produces an undetected
incomplete artifact.

This is the third class of bug in seven days that traces back to
"the LLM has too much agency over a multi-step workflow." NFC/NFD
was tooling-side (orchestrator now normalises). Silent skip was
policy-side (P6 + ADR 0012). Agency fragility is structural — the
source-author runs a 50-step workflow inside one LLM Conversation
and depends on the model + SDK keeping perfect track of "where am I
in the workflow."

## Decision

Replace the source-author agent monolith with a **Python coordinator
that owns workflow control**. The LLM is invoked per discrete step,
each call having a tightly scoped JSON schema and bounded output.
The coordinator is plain Python: a `for` loop over claims, a `for`
loop over concepts, deterministic sequencing, explicit retries on
malformed responses, file written by Python at a fixed point in the
sequence.

Sub-agents (`idea-classifier`, `fact-checker`, `concept-curator`)
remain — they are well-bounded LLM tasks with simple contracts.
What's removed is the source-author *as an agent*. Its workflow
becomes Python.

### Workflow (Python, deterministic)

```python
def process_source(n, raw_path, target_path, slug, llm) -> SourceResult:
    raw = read_raw_json(raw_path)                                 # py
    transcript = compose_transcript(raw)                          # py
    claims = llm_extract_claims(llm, transcript)                  # 1 LLM call, schema-bound
    classified = [
        llm_classify(llm, c, retrieve_prior(c)) for c in claims   # N LLM calls, schema-bound
    ]
    facts = [
        llm_fact_check(llm, c) for c in classified if c.needs_factcheck  # M LLM calls
    ]
    concepts = collect_concepts(classified)                       # py
    body = compose_source_md(transcript, classified, facts)       # py template
    write_file(target_path, body)                                 # py — file exists from this point
    for concept in concepts:
        invoke_concept_curator_agent(llm, concept, slug)          # K agent runs, each its own
    update_concept_index(slug, concepts)                          # py
    return SourceResult(...)
```

Each `llm_*` call:
- has a JSON schema on the response (LiteLLM `response_format`)
- bounded `max_tokens` per the step's expected output size
- on parse failure: retry once with corrective instruction; on second failure: hard error to the coordinator
- no multi-turn agent state; each call is one round trip

### What this kills

- **Hallucinated finish**: there is no `finish` tool the LLM can call. The coordinator decides when work is done.
- **Wrong tool-call format**: each LLM call expects a JSON response per schema. Malformed JSON fails parse, retries, then errors. No silent acceptance.
- **Workflow state loss**: the coordinator has the workflow state in Python variables. The LLM can't lose track of step N because the LLM doesn't know about steps; it sees only the current sub-task.
- **SDK quirks**: no Conversation, no Agent, no SDK-managed turn counting. LiteLLM is the only abstraction below the coordinator.

### What this preserves

- **Sub-agents that work** (`idea-classifier`, `fact-checker`, `concept-curator`) — these are short, schema-able, and have not produced agency-fragility failures. They become explicit Python invocations with simple input/output shapes. `concept-curator` retains the file_editor tool because it does write a file.
- **NFC normalisation, manifest+banner+exit, image rebuild** — every previous architectural fix carries over. The coordinator participates in the same workspace contract.
- **Verify and grade** — `verify_source` and `bench_grade.py` are unchanged. The coordinator writes a file; `verify_source` confirms it.

## Consequences

- **Per-source latency**: roughly the same — same number of LLM round trips. Possibly faster because no source-author message-history accumulation.
- **Per-source LLM cost**: lower. The source-author currently accumulates median 3.45 M cumulative tokens across its conversation. Per-step calls without conversation history would total far less.
- **Per-source reliability**: dramatically higher. The class of failures *"agent claimed done but didn't do it"* becomes structurally impossible.
- **Operational debugging**: simpler. A failed source has a stack trace pointing to which step failed, not a mid-conversation transcript to interpret.
- **Sub-agent invocation**: still uses OpenHands Agent + Conversation for `concept-curator` (it writes a file via `file_editor`). The same agency-fragility risk exists there in a smaller form. Mitigations: shorter prompt, single-purpose, post-write verification (file exists check). If `concept-curator` proves fragile too, we apply the same pattern to it.
- **Cost of this decision**: a Phase F project. Rebuilds the production pipeline. The K1 v2 partial output (16 sources committed on `experiment/K1-v2-…`) sits on the shelf until the coordinator is shipped, then is replayed against it. Acceptable cost; the partial wiki was unpublishable anyway per P6.

## ADR-TDD plan

Per repo convention (P5 + Vasiliy's preference): **ADR first, tests
second, implementation third**. Tests codify the coordinator's
contract before any code is written.

1. **ADR** (this file). Captures the rationale, the decision, the
   consequences. Reviewed by Vasiliy.
2. **Tests** (next commit, before any production code):
   - `test_coordinator_unit.py` — fixture coordinator with a fake
     `llm` callable; verifies the workflow sequence, schema
     enforcement, retry behaviour, file write at the right step.
   - `test_coordinator_integration.py` — runs the coordinator inside
     the bench container with the real `concept-curator` sub-agent
     and a mocked LLM callable for the structured calls. Verifies
     that the full chain produces a verified=ok source.md against
     `bench_grade.py`.
   - `test_coordinator_e2e.py` — runs against the e2e fixture (4
     real raw.json files, compacted transcripts) with the real
     vLLM. Verifies 4/4 verified=ok.
3. **Implementation** (next commit after tests are green-failing):
   `orchestrator/source_coordinator.py` + integration into
   `run-d8-pilot.py` (replaces the per-source source-author task
   with a coordinator call). Each commit makes one test pass.
4. **Replay K1 v2** on the new coordinator, with the `experiment/K1-v2-…`
   branch as the resume point.

## Anti-patterns rejected

- **"Just retry the source-author when verify fails."** Treats the
  symptom. Doesn't address why the model fails to write — when it
  does, the retry will fail the same way. Adds 25 minutes of GPU
  time per occurrence. Hides the architectural defect.
- **"Patch the OpenHands SDK to reject malformed turns."** Right
  fix at the wrong level. Upstream patch is slow to land; meanwhile
  every other source-author conversation is at risk. Also doesn't
  address the multi-step workflow fragility, only the single-turn
  acceptance bug.
- **"Tighter source-author prompt."** Will not work. The prompt
  already includes explicit "write source.md before calling finish"
  instructions and an NFC HAZARD section. The model still drifts.
  Prompt-only fixes plateau against agency-fragility.
- **"Write source.md skeleton first."** Considered. Reduces the
  blast radius (file exists, structurally valid frontmatter even
  if content is incomplete) but does not eliminate
  silent-incompleteness. The coordinator approach delivers the
  same skeleton-first benefit AND the workflow-control benefit in
  one step.

## Why this is the right level of decomposition

The coordinator does not eliminate the LLM. It restricts the LLM to
the operations it is good at: extracting structured information from
a Russian transcript, classifying a claim against candidates,
fact-checking a specific empirical statement. It removes the LLM
from the operations it is bad at: maintaining workflow state across
tens of round trips, tracking which steps are complete, deciding
when to call `finish`, formatting tool calls consistently for an
hour straight.

Per P5 (prefer the cheap experiment that yields the same signal):
the coordinator IS the cheap experiment for "what does production
look like with the LLM responsible only for content generation, not
workflow control?" If the coordinator works at e2e fidelity, the
agency-fragility class is closed. If something else fails, the
coordinator's deterministic surface makes the next bug far easier
to pin.

## Implementation notes (2026-04-30)

Things tuned during the first K1 v2 runs that warrant being on record:

- **Transcript chunking** in `extract_claims`. A single LLM call over
  a 50K-char Russian transcript hung well past timeout. Chunked at
  8 K chars per call, broken on whitespace, deduped by lowercased
  prefix on output. Per-chunk wall ~6–15 s.
- **Batched classification.** Per-claim classify calls were ~9 s
  each at vLLM serial throughput. Batched to 8 claims per LLM call
  via the `claims_batch_classification` schema; LLM returns an array
  indexed by `claim_index`. Net: 5–7× per-batch speedup before
  parallelism.
- **Parallelism.** `ThreadPoolExecutor(max_workers=_MAX_PARALLEL)`
  wraps each phase (chunk extract, classify batches, fact-check).
  `_MAX_PARALLEL` reads from `D8_PILOT_MAX_PARALLEL` env var
  (default 13). Sweep on a real K1 source: per-claim throughput at
  parallel=5/10/13/15/20/30 was 0.70 / 0.64 / **0.44** / 0.57 /
  0.59 / 0.57 s/claim — vLLM saturates around 13 concurrent
  requests.
- **Fact-check cap.** The LLM over-flagged `needs_factcheck=true`
  (89/107 in early SRC 0). Hard cap at 8 fact-checks per source;
  excess claims keep their classification but skip fact-check.
- **Fact-check output bound.** SRC 20 (K1 v2 first run) failed
  because the LLM rambled inside the fact-check JSON's `notes`
  field — recursive "wait, let me re-evaluate" with nested escapes
  that broke `json.loads` AND the corrective retry. Tightened the
  prompt with hard rules (one sentence, ≤240 chars, plain ASCII, no
  nested escapes) and dropped `max_tokens` from 600 to 300.
- **Concept curator.** First cut uses a deterministic stub that
  writes minimal `concept.md` per concept slug. The real
  concept-curator OpenHands sub-agent integration is a follow-up;
  the stub keeps cross-references resolvable so per-source
  `bench_grade` still passes.
- **Vestigial code cleanup.** With the coordinator owning the per-
  source loop, `setup_agents()`, `measure_top_orch()`, the four
  agent prompts (`IDEA_CLASSIFIER_PROMPT`, `FACT_CHECKER_PROMPT`,
  `CONCEPT_CURATOR_PROMPT`, `SOURCE_AUTHOR_PROMPT`), and the
  OpenHands SDK Agent/Conversation/Tool imports were removed from
  `run-d8-pilot.py` (1391 → 885 lines).

Status as of 2026-04-30: 20 sources verified=ok via coordinator
(parallel=10), 1 source skipped on the rambling-JSON failure mode
now patched. Clean re-run with parallel=13 + tightened fact-check
expected to clear all 44 sources in ~1 hour wall.

## Output contract: language preservation

The wiki content language must match the source content language.
For a Russian raw.json, every wiki artifact derived from it — TL;DR,
Лекция сжато, claim text, fact-check notes, concept slugs, concept
file names, concept frontmatter, concept definitions, concept
contributions — is in Russian. No English fall-through, no
translation, no transliteration to ASCII.

Why this needs to be a contract, not a prompt detail: bench_grade
checks structural validity (sections present, markers present,
frontmatter fields populated). It does NOT check what language the
content is in. A wiki of English summaries of a Russian lecture
passes bench_grade verified=ok and ships looking correct. The
language regression is invisible to every automated check we have.
The user catches it by reading.

Enforcement points (all in `source_coordinator.py`):

- `_prompt_extract_claims` — explicit "Output every claim in the SAME
  LANGUAGE as the TRANSCRIPT below."
- `_prompt_classify_batch` — explicit "category: kebab-case slug IN
  THE SAME LANGUAGE as the claim. If the claim is Russian, the slug
  is Russian (e.g. 'академическая-фрагментация')." Concept file
  names derive from this slug, so Russian slug → Russian filename.
- `_prompt_fact_check` — explicit "notes: ONE sentence in the SAME
  LANGUAGE as the CLAIM." (Earlier "Plain ASCII" rule, added to
  prevent rambling-JSON, was found to silently force English notes;
  removed in favor of nested-escape constraint.)
- `_prompt_tldr` — explicit "🇷🇺 LANGUAGE: same as the TRANSCRIPT."
- `_prompt_lecture` — explicit "🇷🇺 LANGUAGE: same as the
  TRANSCRIPT."
- `_make_concept_curator` (in `run-d8-pilot.py`) — uses claim text
  verbatim as Definition / Contribution; if claims are Russian,
  concept content is Russian. No translation step.

Future LLM steps (e.g. real concept-curator agent integration) MUST
include the same language-preservation directive in their prompt.
ADRs that introduce new content-generation paths MUST state the
language contract explicitly.

This contract was emergent in practice — the coordinator originally
defaulted to English claim text and English fact-check notes, the
user caught both by eye, the prompts were iterated. Codifying it
here so a future change won't silently regress.

## Quality contract: what bench_grade does NOT check

P6 ("completeness over availability for compiled artifacts") was
written about silent skips of source files. The same logic applies
to silent skips of CONTENT inside files. A wiki that ships every
source.md with structurally-valid frontmatter and the five required
sections, but where every Лекция is one paragraph from the first
30 minutes of a 90-minute lecture and every concept article has a
one-claim Definition, satisfies the LETTER of P6 (no missing
files, no skipped sources) and violates the SPIRIT (the artifact
does not capture what readers will use it for).

bench_grade today checks **structure**: required sections, claim
markers, frontmatter fields, marker validity. It does NOT check:

- **Лекция coverage** — whether the condensed retelling covers the
  whole transcript or just the model's input window. A 1-paragraph
  Лекция from a 90-minute lecture passes bench_grade.
- **Concept article richness** — whether the Definition is
  encyclopedic prose or just the most-recent claim text repeated
  verbatim. A `Definition\n\n{claim_text}` block passes
  bench_grade.
- **Concept dedup** — whether 1523 concept files represent 1523
  distinct ideas or ~150 ideas with multiple spellings. K1 v2
  produced 10× more concept files than K1 v1 from the same source
  set; bench_grade reported neither as a violation.
- **Fact-check coverage** — whether every `needs_factcheck=true`
  claim was actually fact-checked, or capped at 8. Capped claims
  keep their classification but lose URL + notes; bench_grade
  doesn't notice.
- **Concept-to-concept cross-references** — whether each concept
  article links to ≥ 1 related concept. K1 v2 concept articles are
  islands; bench_grade doesn't notice.
- **concept-index.json maintenance** — whether
  `processed_sources` and `first_introduced_in` are kept current.
  K1 v2 doesn't update the file; bench_grade doesn't read it.
- **concepts_introduced precision** — whether the
  `concepts_introduced` field is a strict subset of
  `concepts_touched` filtered to "first appearance in the
  retrieval index" (K1 v1) or just a copy of `concepts_touched`
  (K1 v2). bench_grade only checks subset, not source-of-truth.

Quality gates that bench_grade SHOULD enforce, queued as work:

- `lecture_word_count >= 0.5% * transcript_word_count`
- `concept Definition word_count >= 30 AND not exact-match any
  single claim in concept's Contributions`
- `concept_dedup_ratio = (count of slugs with cosine > 0.85
  against another slug) / total_slugs <= 0.10`
- `fact_check_coverage = (claims with fact_marker set) /
  (claims with needs_factcheck=true) >= 0.90`
- `concept_xref_count >= 1 per concept article`
- `concept-index.json processed_sources covers the run's commits`

Until those gates exist and pass, the coordinator's output is
*structurally correct, content-thin* — a faster pipeline producing
a thinner artifact, not a publishable wiki.

The K1 v2 run that produced this ADR section was structurally
44/44 verified=ok. By the quality contract above it was a draft.
The wall-time win came partly from real efficiency (~5× from no
agent state accumulation, ~3× from parallelism, ~1.4× from
schema-bound outputs) and partly from skipping work that
bench_grade couldn't measure — concept-curator depth (~3×) and
fact-check breadth (~1.2×). Naming the trade-off here so future
runs cannot quietly cash in on the same skip.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
