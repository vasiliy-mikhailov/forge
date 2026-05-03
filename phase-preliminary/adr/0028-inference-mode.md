# ADR 0028 — `inference` mode as a separate operating capability; modes vs labs as an EA distinction

## Status

Accepted (2026-05-03). Active.

## Measurable motivation chain

Per [P7](../architecture-principles.md):

- **Driver**: customer-interview cycle (per [ADR 0027](0027-product-development-approach.md)) needs a vLLM endpoint without spinning up the full wiki-compile pipeline. Today only `make wiki-compiler` exposes vLLM, which name-confuses operators (a "wiki-compiler" target serving a non-wiki-compile inference workload). Architect call (2026-05-02): *"wiki compiler stays as is, but inference mode emerges which can also use underlying architecture layers if needed, but this mode definitely does not need underlying wiki compiler and wiki compiler does not need this mode. The mode is the mode, it's like exclusive operating capability on top of EA."*
- **Goal**: [Architect-velocity](../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). One Make target per operator-intent removes per-cycle naming confusion and the mistakes it causes.
- **Outcome**: this ADR + a new EA-level concept ("operating mode" as ArchiMate Application Service) + a minimal `inference` mode landing in the same commit (`phase-c-information-systems-architecture/operating-modes/inference/`). `make inference` brings up caddy + vllm-inference without any wiki-compile pipeline scripts. wiki-compiler lab stays as is.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: separates **mode-as-operating-capability** from **lab-as-implementation-unit** — a distinction forge had implicitly (every lab's `make` target was treated as a mode) but never named at the EA level. Naming it makes future modes cheap (no new lab required) and prevents future operator-intent / lab-name name collisions.
- **Capability realised**: [Service operation](../../phase-b-business-architecture/capabilities/service-operation.md).
- **Function**: Introduce-operating-modes-as-EA-concept-and-add-inference-mode.

## Context

Pre-this-ADR forge had four labs (`wiki-compiler`, `wiki-ingest`, `wiki-bench`, `rl-2048`), each with a self-contained `caddy/`, `docker-compose.yml`, `SPEC.md`, `AGENTS.md`. The labs are mutex on host ports 80/443 (each binds them via own caddy) and on the Blackwell GPU when one of them takes it. So far so good.

A subtler distinction was implicit: each lab has a `make <lab>` target that an operator runs to **enter a mode of operation** — the system in `wiki-compiler mode` runs the wiki-compile pipeline; the system in `rl-2048 mode` runs the GRPO sandbox; etc. Lab and mode were 1:1. The 1:1 broke when the customer-interview cycle (per ADR 0027) needed a vLLM endpoint without the wiki-compile pipeline.

Three options were considered — (A) add a new `inference` lab parallel to wiki-compiler; (B) rename `wiki-compiler` to a more generic name; (C) refactor wiki-compiler into a shared inference layer with a wiki-compile addon. The architect rejected all three: *"the mode is the mode, it's like exclusive operating capability on top of EA."* The right move is to recognise that **mode is a concept distinct from lab**, and to add the new mode without touching the existing labs.

## Decision

### 1. Name "operating mode" as an ArchiMate Application Service at the EA level

Forge introduces a new EA-level concept: an **operating mode** is an ArchiMate Application Service the system exposes to its environment when an operator runs a corresponding `make` target. Operating modes are mutually exclusive at the operator level (one mode at a time on the Blackwell GPU + caddy ports 80/443), but they can share underlying architecture layers (vLLM image, model registry, proxy-net).

A **lab** remains an implementation unit — a self-contained directory with its own caddy + compose + SPEC + AGENTS.md.

A lab can implement a mode (the `wiki-compiler` lab implements `wiki-compiler mode`). A mode can also be lighter than a lab — using just a slice of architecture without a full lab structure. **`inference` is the first such non-lab mode.**

### 2. New directory tree — `phase-c-…/operating-modes/`

Modes that are NOT labs live under [`phase-c-information-systems-architecture/operating-modes/<mode-name>/`](../../phase-c-information-systems-architecture/operating-modes/):

- [`README.md`](../../phase-c-information-systems-architecture/operating-modes/README.md) — EA-level documentation of the modes-vs-labs concept and the modes table.
- One subdirectory per non-lab mode, with:
  - `SPEC.md` — Phase A-H scaffolding; light.
  - `docker-compose.yml` — the containers this mode needs.
  - `Makefile` — `up` / `down` / `smoke` targets following `common.mk`.
  - `caddy/Caddyfile` + `caddy/Makefile` + `caddy/docker-compose.yml` if HTTP-facing.

### 3. `inference` mode — first non-lab mode

[`phase-c-information-systems-architecture/operating-modes/inference/`](../../phase-c-information-systems-architecture/operating-modes/inference/) contains:

- A minimal `vllm-inference` container — same image (`vllm/vllm-openai:v0.19.1-cu130-ubuntu2404`), same `${INFERENCE_GPU_UUID}` Blackwell pinning, same `${STORAGE_ROOT}/shared/models` HuggingFace cache, same `${INFERENCE_DOMAIN}` as the wiki-compiler lab uses for ITS OWN vllm-inference container. The two are mutex at runtime; architecturally they don't reference each other.
- A minimal `inference-caddy` reverse_proxy → `vllm-inference:8000`, Bearer auth (per [ADR 0005](0005-inference-subsystem.md)), no basic auth.
- Reuses wiki-compiler's `bin/load-active-model.sh` and `tests/smoke.sh` (single source of truth for the model registry per [ADR 0008 — model registry](../../phase-d-technology-architecture/adr/0008-model-registry-single-source-of-truth.md)). Reusing scripts ≠ depending on the lab — wiki-compiler-mode does not need to be running for inference-mode to work; the script just lives in wiki-compiler's tree.

### 4. Top-level `Makefile` extended — `LABS` + `MODES`

The top-level `Makefile` adds `MODES := inference` next to `LABS := wiki-compiler wiki-ingest wiki-bench rl-2048`. Both lists feed the `make <name>` / `<name>-down` / `<name>-logs` / `<name>-build` pattern; the dispatch rule branches on whether the name lives under `application-architecture/` or `operating-modes/`. `make stop-all` now stops every lab AND every mode.

### 5. Mutex declared explicitly

`inference` mode is mutex with `wiki-compiler` and `rl-2048` (Blackwell GPU + caddy ports). It is NOT mutex with `wiki-bench` (bench is a non-caddy client lab — co-runs with whatever provides the inference endpoint). Mutex is operator-managed (`make stop-all` first if another mode holds the resources).

### 6. Independence rule

`wiki-compiler` lab and `inference` mode are architecturally independent. Neither references the other in a `realises` / `depends-on` sense. They both happen to use the same vLLM image and the same model registry, but those are shared LAYERS, not cross-references between the two units. If wiki-compiler were deleted tomorrow, inference mode would still work (after relocating `bin/load-active-model.sh` to a shared location, which is queued as a follow-up).

## Consequences

- **Plus**: clean operator-intent model — one `make` target per intent (`make inference` for "I just want vLLM"; `make wiki-compiler` for "I want the wiki-compile pipeline").
- **Plus**: new modes become cheap. Future operating capabilities (e.g., a customer-interview mode bundling vLLM + an interview agent) land as a new `operating-modes/<mode>/` directory + a `MODES` line + an ADR; no lab restructure needed.
- **Plus**: EA gains a concept it was missing — "operating mode" is now first-class in `phase-c-…/operating-modes/README.md` instead of implicit in lab names.
- **Plus**: forge-as-public-reference becomes more useful: any architect adopting forge's method now sees the mode-vs-lab distinction documented.
- **Minus**: a tiny amount of duplication — the inference mode's `docker-compose.yml` is a copy of wiki-compiler's `vllm-inference` service. Mitigation: keep the duplication shallow (the copy is ~40 lines). When the next mode arrives that also needs vLLM, factor a shared compose fragment.
- **Minus**: operators must understand the mode-vs-lab distinction (one new concept). Mitigation: `phase-c-…/operating-modes/README.md` is short and the modes table makes the distinction one read away.

## Invariants

- A new operating mode landing in forge ships its own `Makefile` (`up` / `down` / `smoke`), `docker-compose.yml`, and `SPEC.md`; lacking any of these is a P3 / P4 / P10 FAIL on the next audit walk.
- The top-level `MODES` list is the single source of truth for which non-lab modes exist; `phase-c-…/operating-modes/README.md`'s table must match.
- Mode mutex is operator-managed (no automatic mutex enforcement). Operators run `make stop-all` before switching modes.
- The wiki-compiler lab and the inference mode remain architecturally independent — neither references the other in any dependency direction.

## Alternatives considered

- **Option A — add an `inference` lab parallel to wiki-compiler**. Rejected by the architect: a lab has more scaffolding than this needs (no AGENTS.md operating environment, no SPEC-extra, no compile pipeline). Adding a full lab for what is essentially "vllm + caddy" is over-structured.
- **Option B — rename `wiki-compiler` to something more inference-generic**. Rejected: wiki-compiler is wiki-compiler; renaming it would erase its identity to dodge a separate concern.
- **Option C — refactor wiki-compiler into shared inference + wiki-compile addon**. Rejected: makes wiki-compiler lab depend on an inference layer it currently encapsulates. Adds coupling for no operator-visible benefit.
- **Option D (chosen) — introduce mode-vs-lab as an EA distinction; land inference as the first non-lab mode**. Accepted: smallest concept addition that fits the architect's framing ("the mode is the mode, it's like exclusive operating capability on top of EA"); zero impact on wiki-compiler.

## Follow-ups

- Move `bin/load-active-model.sh` and `tests/smoke.sh` from `wiki-compiler/` to a shared location (e.g., `phase-c-…/application-architecture/_shared/` or `scripts/`) once a second consumer demands it. Today's reuse via cross-Makefile call is acceptable but inverts dependency direction (mode references lab path).
- When a future mode also needs vLLM, factor a shared `compose.vllm.yml` fragment that both `wiki-compiler` and `inference` modes can `--file` together. Today's duplication is shallow enough that doing this prematurely would cost more than it saves.
- Audit-process P3/P4 currently assume one Makefile per `application-architecture/<lab>/`; extend to also enumerate `operating-modes/<mode>/`.
- Update `audit-process.md` to add a P32 predicate: every entry in `MODES` and `LABS` must have a corresponding directory + `Makefile` + `SPEC.md` (catches drift between the orchestrator and the EA tree).
