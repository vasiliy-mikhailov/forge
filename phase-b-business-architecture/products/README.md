# Products

R&D capability produces shippable products. Per-product detail
(value stream, capabilities, status, trajectories) lives in one
file per product in this folder.

| Product / line          | Realised across                                          | Status                                                            | Per-product detail                                       |
|-------------------------|----------------------------------------------------------|-------------------------------------------------------------------|----------------------------------------------------------|
| **Wiki product line**   | wiki-ingest + wiki-bench + wiki-compiler                 | Active                                                            | [`wiki-product-line.md`](wiki-product-line.md)           |
| ⤷ **Kurpatov Wiki**    | wiki-ingest + wiki-bench + wiki-compiler                 | Active — module 005 published as canonical Qwen3.6-27B-FP8 result | [`kurpatov-wiki.md`](kurpatov-wiki.md)                   |
| ⤷ **Tarasov Wiki**     | wiki-ingest + wiki-bench + wiki-compiler                 | Pre-pilot — content acquisition phase                             | [`tarasov-wiki.md`](tarasov-wiki.md)                     |
| **rl-2048**             | rl-2048 lab                                              | Pre-methodology phase                                             | [`rl-2048.md`](rl-2048.md)                               |

The wiki line's operations stack — what `wiki-*` labs do per
product, and which forge capability each operation draws on —
lives in [`wiki-product-line.md`](wiki-product-line.md) on this
side, since each row describes *what this product line does*,
not *what forge can do in the abstract*. The forge-level
capabilities those operations draw on are in
[`../capabilities/forge-level.md`](../capabilities/forge-level.md).
(rl-2048 still keeps its operations table under `../capabilities/`
for now; same category-error fix is queued.)
