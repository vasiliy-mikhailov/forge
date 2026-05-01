# Phase B — Business Architecture

The capability layer: what forge can do, who does it, what products
those capabilities ship.

## Capabilities (what forge can do)

- [`capabilities/forge-level.md`](capabilities/forge-level.md) —
  the four forge-level capabilities (R&D; Service operation;
  Product delivery; Architecture knowledge management) and the
  quality dimension each is judged on.
- [`capabilities/rl-2048.md`](capabilities/rl-2048.md) — rl-2048
  capability stub.
- [`capabilities/service-operation.md`](capabilities/service-operation.md)
  — the active capability with its quality-dimension trajectory
  (throughput / stability / cost-per-token; G1 / G2 history).
- [`capabilities/develop-wiki-product-line.md`](capabilities/develop-wiki-product-line.md)
  — the capability exercised across every member of the
  [Wiki product line](products/wiki-product-line.md): take an
  author's lecture corpus and produce a smart-reading wiki that
  preserves the author's voice. Decomposes R&D + Product delivery +
  Architecture knowledge management for the wiki domain.

## Organization units (who does it)

- [`org-units.md`](org-units.md) — today: one architect of record.
  Labs are not org units (they are application components in
  Phase C).

## Products (what those capabilities ship)

- [`products/`](products/) — one file per product, plus the
  [`products/wiki-product-line.md`](products/wiki-product-line.md)
  file for the multi-author wiki line itself. Index in
  [`products/README.md`](products/README.md).

## ADRs

