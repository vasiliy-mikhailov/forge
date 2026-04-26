---
name: tdd-on-synthetic-fixtures
description: >-
  Iterative TDD methodology for developing complex agent orchestrations —
  progressive step scripts on minimal hand-crafted fixtures, each with an
  explicit pass criterion, committed between greens. Use when the change
  spans multiple moving parts (new tool integrations, new sub-agent types,
  new control flows) and the production run cycle is expensive (≥10 min).
triggers:
  - tdd
  - test-driven
  - synthetic fixtures
  - iterative development
  - step1 step2 step3
  - orchestration test
  - subagent test
---

# TDD on synthetic fixtures — methodology

Captures the methodology used to develop D7-rev3 (Python SDK orchestrator + per-source sub-agent isolation + 3-level fan-out) on the `kurpatov-wiki-bench` lab. Steps 0–5d in `tests/synthetic-orchestrator/step{0..5d}_orchestrator.py` are the canonical example.

## When to use it

Reach for this methodology when **all** of the following hold:

- The change spans multiple moving parts (new tools, new agent types, new control flows, new persistence). One-line config tweaks don't need this.
- Each production run cycle is expensive in wall time (e.g. ≥10 min) or in GPU/API budget. Cheap iterations don't need synth.
- There's a non-trivial chance the design has unknowns that only execution will surface (new framework features, model behavior under unfamiliar prompt structures, cross-agent communication shape).
- A small set of hand-crafted fixtures can stand in for the full production input.

When the change is small or the production cycle is cheap, skip the methodology and iterate directly on production.

## Core practices

### One progressive step per script file

Each step is its own runnable Python (or bash) file: `step1_<name>.py`, `step2_<name>.py`, …

Why one-file-per-step: kills the temptation to refactor previous steps; each step is a self-contained executable proof; previous greens stay reproducible verbatim.

Cost: a small amount of duplication between consecutive steps. Worth it.

### Explicit pass criterion before writing any code

The first thing in every step's docstring is the pass criterion in measurable terms. Examples from D7-rev3:

- Step 1: "HELLO_FROM_SUB_AGENT appears in conversation events."
- Step 4: "`bench_grade.py --single-source-json` returns `verified: ok`."
- Step 5b: "claims_REPEATED_sum >= 2 in aggregate (synth fixtures 003/004 deliberately repeat Moore/Everest from 001/002)."
- Step 5d: "4/4 verified=ok AND REPEATED_sum >= 2 AND CF >= 1 AND URLs >= 6 AND concepts >= 4 AND top orchestrator events < 100."

The script's last action is `sys.exit(0)` if the criterion holds, `sys.exit(1)` otherwise — green/red is one bit, no ambiguity. Negative cases come back as concrete numbers in the failure message.

### Each step adds exactly one capability

| step | what was added                                                  |
|----: | ----                                                            |
|    0 | foundation — pip install + basic imports                       |
|    1 | basic delegation works at all (default builtin sub-agent)      |
|    2 | custom AgentDefinition registered and invokable                |
|    3 | sub-agent does file I/O                                        |
|    4 | sub-agent produces skill-v2-compliant artifact                 |
|    5 | orchestrator iterates N sources sequentially                   |
|   5a | shrink master prompt — context bloat fix                       |
|   5b | get_known_claims.py integration → REPEATED detection           |
|   5c | 3-level orchestration on 1 source — fan-out per claim          |
|   5d | 3-level on N sources + concept-curator                         |

If a step needs to add two capabilities, it becomes Step 5a + Step 5b. The progression stays linear.

### Synth fixtures are deliberate, not realistic

The synth fixtures for D7-rev3 (`tests/synthetic/fixtures/raw/{001..004}.json`) are designed to test specific properties:

- **001** has a deliberate factual error (1950-Pareto, actually 1896) to exercise CONTRADICTS_FACTS detection.
- **003** repeats Moore's law from 001 — to exercise REPEATED detection.
- **004** repeats Everest from 002 — same.
- All transcripts are short (~3 segments, ~300 chars each). Enough to surface behaviour, cheap enough that 4-source runs take 3–5 min.

Real production transcripts are 30 KB each and behave differently from short fixtures (model attention, tool-use patterns). Synth catches **architectural** failures (wrong contract, wrong control flow, missing tool plumbing). It does NOT catch capability failures (model can't sustain a 12-step ritual). Production is still required at the end.

### Commit between greens

Each green step gets a commit. Logical history visible in `git log`:

```
177f6ac bench/D7-rev3: TDD steps 5b/5c/5d GREEN — REPEATED detection + 3-level orchestration
1eae7b1 bench/D7-rev3: TDD steps 0-5 GREEN — Python SDK orchestrator + sub-agent isolation works
```

If a later step regresses, the bisect target is concrete.

### Failure mode: exhaust the easy explanations before changing the design

When a step fails, the order of investigation:

1. **Read the failure message.** Concrete numbers, exception traces.
2. **Read the script's last 30 lines of log.** What did the agent actually do?
3. **Check fixtures.** Did the synth fixture match the assertion's expectation?
4. **Check known framework gotchas.** `.agents/skills/openhands-sdk-orchestration.md` lists the ones we have hit (DelegateTool spawn cap, master prompt bloat, PyInstaller LD_LIBRARY_PATH leak, parser regex inconsistencies).
5. Only then — change the design.

Discovered failures we did NOT misdiagnose into design changes thanks to this discipline:

- Step 4 verified=fail with claims_unmarked=1 → **was a bench_grade.py regex bug** (expected `[CONTRADICTS FACTS]` with space, sub-agent wrote `[CONTRADICTS_FACTS]` with underscore per skill v2 spec). Fixed parser, not contract.
- Step 5d failed with "Cannot spawn 1 agents. Already have 5 agents, maximum is 5" → **was a known DelegateTool parameter** (`max_children=5`, default), workaround per upstream example 41 is spawn-once-reuse. Adjusted prompt, not architecture.

### Side-findings get recorded immediately

When a TDD step uncovers a project-wide bug (parser regex, deprecation, environmental issue), it's recorded the same commit:

- Step 4 found bench_grade.py CONTRADICTS_FACTS regex bug → fix shipped in `1eae7b1`, recorded in `AGENTS.md` "Known issues with metric history" with retro-grade caveats per affected branch.
- Steps 5c/5d hit DelegateTool spawn cap and discovered deprecation → recorded in `openhands-sdk-orchestration.md`.

## Anti-patterns

- **Don't bundle two changes into one step.** "Step 5d adds 3-level fan-out AND concept-curator" was OK because both are small extensions of the same architectural primitive (delegation). "Step X adds 3-level fan-out AND switches to TaskToolSet AND introduces parallelism" would be three steps.
- **Don't over-mock the fixture.** A synth fixture should drive the real script paths (real factcheck.py making real Wikipedia calls when the test exercises factcheck integration). Mocking too aggressively removes the value.
- **Don't skip "verify the artifact, not the agent's claim".** When the orchestrator asks a sub-agent for a result, `bench_grade.py --single-source-json` is the source of truth, not the sub-agent's "done" reply. Pattern is: agent action → artifact on disk → deterministic script reads it → boolean pass.
- **Don't write the production code inside the step script.** The step script is the **test**. The production code (`orchestrator/run-d7-rev3.py`) lives separately. Step scripts can shamelessly inline things; production code respects normal modularity.

## How this differs from unit testing

This methodology is **integration TDD on stochastic behavior**. Each step exercises real model + real network + real subprocess. There's no mock LLM. The pass criterion is not deterministic on rerun (different stochastic outputs each time); it's a measurable property of the artifact.

If a step is GREEN once but a later run is RED on the same code, the noise is signal: either the model's behavior on this prompt is unreliable (worth raising as a concern), or there's a flake (worth retry budget). Don't dismiss as test flake without checking.

## See also

- `tests/synthetic/` — the original synthetic test (single-agent skill v2 regression baseline, 10/10 GREEN). Different scope from `tests/synthetic-orchestrator/` (Python SDK orchestrator with per-source sub-agent isolation).
- `.agents/skills/openhands-sdk-orchestration.md` — SDK-specific findings discovered through this TDD progression.
- `docs/adr/0009-per-source-agent-isolation.md` — architectural decision validated end-to-end via Steps 0-5d.
- `docs/experiments/D7-rev3.md` — production experiment using the validated architecture.
