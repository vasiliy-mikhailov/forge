# wiki-bench

Server-side, Docker-sandboxed **agent benchmark harness** for the
wiki product line. One `make bench` invocation runs an
[OpenHands](https://github.com/OpenHands/OpenHands) agent inside
an isolated Docker container against whatever model the local
[`wiki-compiler`](../wiki-compiler/) vLLM endpoint is currently
serving, against the
[`kurpatov-wiki-wiki/skills/benchmark/SKILL.md`](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/blob/main/skills/benchmark/SKILL.md)
authoring task.

This file is a casual entry point for readers landing on the lab
folder via GitHub. The substantive docs are:

- [`AGENTS.md`](AGENTS.md) — the agent context (Phase A-H scoped
  to this lab). Read this first when starting work in the lab.
- [`SPEC.md`](SPEC.md) — the lab's contract: inputs, outputs,
  invariants, image, build/run model, artifact layout,
  preflight contract, smoke-test contract.
- [`docs/adr/`](docs/adr/) — lab-scoped ADRs. ADR pointers are
  also indexed per phase from inside `AGENTS.md`.
- [`docs/STATE-OF-THE-LAB.md`](docs/STATE-OF-THE-LAB.md) — current
  capability trajectories (Level 1 → Level 2). Phase E gap audit
  for this lab.
- [`docs/experiments/`](docs/experiments/) — lab-scoped
  experiment specs (per-run, per-hypothesis docs).

## Quick orientation

- Bench is **content-agnostic**: the same harness benchmarks any
  wiki product (Kurpatov, Tarasov, future authors). What changes
  per product is the input corpus and the fact-check domain, not
  the lab.
- Bench is a **client** of `wiki-compiler` — it speaks
  OpenAI-compatible HTTP to `${INFERENCE_DOMAIN}` and does not
  need a caddy of its own.
- Bench's authoring contract (skill v2) lives in the wiki repo,
  not in this lab. The wiki repo's `prompts/per-source-summarize.md`
  + `prompts/concept-article.md` are the canonical authoring
  prompts; the lab calls the agent that follows them.

## Forge-level cross-references

- Forge architecture vision and capabilities:
  [`forge/AGENTS.md`](../../../../AGENTS.md).
- The product this lab realises:
  [`forge/phase-b-business-architecture/products/kurpatov-wiki.md`](../../../../phase-b-business-architecture/products/kurpatov-wiki.md)
  (and `tarasov-wiki.md`).
- The capability stack this lab carries:
  [`forge/phase-b-business-architecture/products/wiki-product-line.md`](../../../../phase-b-business-architecture/products/wiki-product-line.md).
