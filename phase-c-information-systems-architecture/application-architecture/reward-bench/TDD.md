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
