# Roadmap

The cross-lab prioritised backlog: what gets built next and in what
order. TOGAF lists the **Architecture Roadmap** as a Phase E
deliverable; this is forge's realisation. Per-lab gap details still
live in each lab's `STATE-OF-THE-LAB.md`; this file is the cross-
lab digest.

The order is **prioritised by binding-lever rank**, not by date.
Items at the top should land before items below them; they unblock
the items below.

## Top of the queue (active or imminently active)

### 1. R-D-contract-prewrite — pre-write concept-file existence check

**Source:** G3 closure (gate-4 falsification).

**Why it's top:** load-bearing gate that blocks any further
LLM-component swap experiment. G2 (MoE) and G3 (Gemma) both
falsified at the contract-enforcement layer, not the throughput
layer. Without this, no model swap can be evaluated cleanly —
faster models will keep producing more concept slugs than concept
files.

**Where it lands:** [`phase-c-…/application-architecture/wiki-bench/orchestrator/run-d8-pilot.py`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator/run-d8-pilot.py)
plus the source-author / curator sub-agent prompts in
`kurpatov-wiki-wiki:skill-v2/`.

**Spec:** open Phase F experiment (id TBD — likely `H1-contract-prewrite.md`).

### 2. R-D-contract-xreflint — run-level cross-ref linter

**Source:** G3 closure (gate-4 falsification).

**Why second:** complements item 1. Item 1 prevents a class of
violations from being written; item 2 catches the rest at commit
time so the agent can self-correct before fail-fast. Together they
make the canonical-skill-v2 contract enforceable regardless of
which LLM is serving.

**Where it lands:** `bench_grade.py` gets a `--check-xrefs-only
--exit-nonzero` mode; `run-d8-pilot.py` invokes it after each
source's commit; on failure the source is rolled back and the
source-author is re-prompted with the lint output.

**Spec:** open Phase F experiment (id TBD — likely `H2-xref-linter.md`).

### 3. R-D-retrieval-cost — daemonize embed_helpers + factcheck cache

**Source:** G2 closure (binding-lever finding).

**Why third:** the actual pilot-wall lever. ~5 s × claims (cold-fork
embed_helpers) + ~5-15 s × needs_factcheck claims (Wikipedia HTTP)
= the dominant component of source-author wall. Closing this opens
the door to re-test model swaps under the now-stricter contract
enforcement.

**Where it lands:** `embed_helpers.py` becomes a long-lived
process per pilot (load model once, serve queries over a Unix
socket or HTTP); `factcheck.py` adds a per-pilot cache of
Wikipedia article fingerprints.

**Spec:** open Phase F experiment (id TBD — likely `J1-daemonize-embed.md`).

## Mid queue (deferred until top three land)

### 4. R-D-orchestration-kvcache — KV-cache reuse across sub-agents

vLLM 0.19 has prefix caching; OpenHands SDK doesn't currently
keep KV cache warm across same-Conversation sub-agent calls.
Estimated impact ~5-10× fewer prefill tokens per source.
Independent lever from items 1-3 but multiplies their effect.

### 5. R-B-svcop-thruput — re-test model swap (post items 1-3)

After items 1-3 land, R-B-svcop-thruput (currently OPEN, twice-
falsified at the model layer) becomes testable cleanly. Candidates
for re-test in priority order: Gemma-4-31B (already shows wall
gain even without contract), Qwen3.6-35B-A3B (largest decode
gain), then any new dense model in the 27-35B range that ships.

### 6. R-B-svcop-stable24h — 24 h continuous run

Today's L1 is "≥ 169 min sustained without crash." L2 is "≥ 24 h."
Closing this requires a multi-pilot stress test; not the binding
lever for any current goal. Park until pilot-wall is at L2 (so
each pilot is cheap enough to run repeatedly).

## Bottom queue (parked, status-conditional)

- **R-A-PTS** — needs > 1 user before it can be measured. Park.
- **R-A-EB** — implicit; will open as a Phase B requirement when
  the first paying user lands.

## Forward to Phase F

Items 1-3 are the next three Phase F experiments to open. Sequence
in [`../phase-f-migration-planning/migration-plan.md`](../phase-f-migration-planning/migration-plan.md).


## Measurable motivation chain (OKRs)
Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: Phase E maps gaps (current → target Plateau)
  to Work Packages; without an explicit roadmap, the gap → WP
  mapping is implicit.
- **Goal**: Architect-velocity (one place to see the gap →
  WP map).
- **Outcome**: every Phase F experiment cites a Phase E gap.
- **Measurement source**: experiment-closure: K1, K2, G1, G2, G3 (count of closed Phase F experiments cited as gap-closures)
- **Capability realised**: Architecture knowledge management
  ([../phase-b-business-architecture/capabilities/forge-level.md](../phase-b-business-architecture/capabilities/forge-level.md)).
- **Function**: Sequence-gaps-into-Work-Packages.
- **Element**: this file.
