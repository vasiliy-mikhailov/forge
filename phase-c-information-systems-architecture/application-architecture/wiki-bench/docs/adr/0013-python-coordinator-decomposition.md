# ADR 0013 — Decompose source-author monolith into a Python coordinator

Status: Proposed
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
