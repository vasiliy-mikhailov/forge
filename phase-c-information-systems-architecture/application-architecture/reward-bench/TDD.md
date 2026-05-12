# reward-bench TDD application

Follows forge-wide TDD methodology in
[`../../../phase-g-implementation-governance/tdd.md`](../../../phase-g-implementation-governance/tdd.md).
Read that first. This file captures only the reward-bench-specific
choices on top of it.

## Lab-specific scope

- Reverse-engineer the legacy implementation in `_bak/bin/` and
  `_bak/test_*.py` into `bench/` via the seven-step cycle.
- Tier 1 is in scope. Tiers 2-4 are deferred until Tier 1 is fully
  green.
- Interactive submission protocol only (per SPEC.md *Submission
  protocols* section). Static mode is planned but not implemented.

## Lab folder layout

  reward-bench/
    SPEC.md                          bench spec
    AGENTS.md                        operator interface
    TDD.md                           this file
    spec/                            cross-tier functional specs
      parser.md                      interactive protocol parser
      models/<name>.md               per-model bench addendums
      tier1/                         tier-1 functional specs
    tests/
      specs/                         test case enumerations (mirror spec/)
        SPEC.md
        parser.md
        models/
        tier1/
      test_parser.py                 pytest for cross-tier code
      tier1/                         pytest for tier-1 code
    bench/                           clean implementation
      parser.py                      cross-tier code
      tier1/                         tier-1 code
    _bak/                            legacy code; read-only reference
    tasks/                           task definitions (2048, ...)

## Lab-specific 'when to ask the user'

In addition to the forge-wide stop-conditions:

- A new model card is being added — confirm hf_path, quant family,
  and target hardware before writing the .md.
- A regression we observed in the May 2026 campaign (BPE leak on
  Mistral HF quants, Mamba page-align on Qwen3.5+ family, etc.)
  could be reasonably either pinned (preserve broken legacy
  behavior) or fixed (clean impl diverges). Ask before deciding.
- A test would need to spin up vLLM. That is a smoke / integration
  test; mark it slow and confirm before adding because the cycle
  goes from ~1 second to several minutes.


## Use _bak as your first reverse-engineering reference

Before designing new behavior from scratch (a prompt, an extractor, a
parser, a driver), read the closest piece of legacy code in _bak/ and
copy its approach. Reasons:

  - Production legacy code already negotiated real-model quirks (BPE
    leaks, gen-cap truncation, reasoning preambles). Inventing fresh
    almost always rediscovers the same problems painfully.
  - When a cycle goes red on live-model output, the first question is
    "what did _bak do here?" — not "what should I invent?"
  - The legacy prompt (e.g. tasks/2048/SKILL_tier1.md) was tuned against
    the actual benched models; your hand-rolled prompt has not been.

The rule: if a TDD cycle requires touching prompt content, system
behavior, or any model-facing protocol, first grep _bak/ for the
nearest equivalent. Cite the source file in the spec or test docstring.
Do not invent until you have confirmed _bak does not address it.
