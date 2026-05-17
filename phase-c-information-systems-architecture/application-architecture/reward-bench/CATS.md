# reward-bench CATS application

Follows forge-wide CATS methodology in
[`../../../phase-preliminary/cats.md`](../../../phase-preliminary/cats.md).
Read that first. This file captures only the reward-bench-specific
choices on top of it.

## Lab-specific scope

- Reverse-engineer `_bak/bin/` + `_bak/test_*.py` into `src/` via the 11-step cycle.
- Tier 1 only; Tiers 2-4 deferred until Tier 1 is green.
- Interactive submission protocol only (per SPEC.md). Static mode is planned.

## Lab folder layout

  reward-bench/
    SPEC.md                          bench spec — the document UNDER
                                     implementation (TOGAF-facing).
    AGENTS.md                        operator interface
    CATS.md                           this file
    src-spec/                       CODE-facing functional specs.
                                     ONE file per behavior, named
                                     src_spec_when_X_then_Y.md.
      tier1/
        src_spec_when_*.md           one per behavior
      models/<name>.md               per-model bench addendums (cross-tier)
    tests-spec/                      CODE-facing test case specs.
                                     ONE file per test, named
                                     test_spec_when_X_then_Y.md, mirroring
                                     src-spec/ files 1:1.
      tier1/
        test_spec_when_*.md          one per test
    tests/                           pytest implementations of tests-spec/.
      conftest.py
      tier1/
        test_end_to_end.py
    src/                             clean implementation. Satisfies
                                     src-spec/. Symmetric to tests/ which
                                     satisfies tests-spec/.
      tier1/
    _bak/                            legacy code; read-only reference
    tasks/                           task definitions (2048, ...)
    pyproject.toml                   pytest testpaths = ["tests"]
                                     so _bak/ stays out of test discovery

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

Before designing new behaviour (prompt, extractor, parser, driver), read the closest legacy code in `_bak/` and copy its approach. Legacy code already negotiated real-model quirks (BPE leaks, gen-cap truncation, reasoning preambles); inventing fresh almost always rediscovers the same problems painfully.

**Rule**: if a cycle touches prompt content, system behaviour, or any model-facing protocol, first grep `_bak/` for the nearest equivalent and cite it in the spec or test docstring. Don't invent until you've confirmed `_bak` doesn't address it.
