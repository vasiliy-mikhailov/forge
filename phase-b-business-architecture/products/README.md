# Products

R&D capability produces shippable products. Per-product detail
(value stream, capabilities, status, trajectories) lives in one
file per product in this folder for forge-owned products.

| Product / line          | Realised across                                          | Status                                                            | Per-product detail                                       |
|-------------------------|----------------------------------------------------------|-------------------------------------------------------------------|----------------------------------------------------------|
| **Wiki product line**   | wiki-ingest + wiki-bench + wiki-compiler                 | Active                                                            | [`wiki-product-line.md`](wiki-product-line.md)           |
| **rl-2048**             | rl-2048 lab                                              | Pre-methodology phase                                             | [`rl-2048.md`](rl-2048.md)                               |

The wiki product line is realised by per-author wikis owned by
the **psi** subsidiary (course-wiki). Per-author product files
(Kurpatov Wiki, Tarasov Wiki, future authors) live in the
daughter at `phase-b-business-architecture/products/` --
catalog entry [`../subsidiaries/psi.md`](../subsidiaries/psi.md)
holds the URL. Per [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md)
the URL is permitted on forge-public; the per-author content
(including which corpora exist, status per author, quality
numbers per release) stays in the auth-gated daughter repo
per [ADR 0018](../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

The wiki line's Capability Map -- what `wiki-*` labs do per
product, and which forge capability each operation draws on --
lives in [`wiki-product-line.md`](wiki-product-line.md) on this
side, since each row describes *what this product line does*,
not *what forge can do in the abstract*. The forge-level
capabilities those operations draw on are in
[`../capabilities/forge-level.md`](../capabilities/forge-level.md).
(rl-2048 still keeps its operations table under `../capabilities/`
for now; same category-error fix is queued.)
