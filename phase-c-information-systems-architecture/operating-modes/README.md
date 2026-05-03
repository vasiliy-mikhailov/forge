# Operating modes

This directory documents forge's **operating modes** — mutually-exclusive operating capabilities on top of the enterprise architecture. A mode is not a lab; a mode is a high-level operating state that the system enters when an operator runs the corresponding `make` target.

In ArchiMate terms each mode is an **Application Service** (a service the system exposes to its environment), and its realisation is some subset of the underlying infrastructure (containers, GPU pinning, caddy config). Two modes can share underlying components but the modes themselves are exclusive at the operator level — one mode at a time.

## Modes vs labs

| Concept | What it is | Lives in |
|---|---|---|
| **Lab** | A self-contained implementation unit with its own `caddy/`, `docker-compose.yml`, `SPEC.md`, `AGENTS.md`. Owns containers + has a single architectural purpose. | `phase-c-…/application-architecture/<lab>/` |
| **Mode** | An operating capability — a logical state the system enters. May reuse components from one or more labs. Mutually exclusive with other modes (caddy ports, GPU). | `phase-c-…/operating-modes/<mode>/` (this directory) |

A lab can implement a mode (`wiki-compiler` lab implements `wiki-compiler mode`). A mode can also be lighter than a lab — using just a slice of architecture without a full lab structure. **`inference` is the first such mode.**

## Modes today

| Mode | Make target | What it does | Realising components | Mutex with |
|---|---|---|---|---|
| **wiki-compiler mode** | `make wiki-compiler` | Run wiki-compile pipeline; vLLM serves inference internally | [wiki-compiler/](../application-architecture/wiki-compiler/) lab (caddy + vllm-inference) | inference, rl-2048 (Blackwell + caddy ports) |
| **wiki-ingest mode** | `make wiki-ingest` | Whisper transcription + Jupyter + raw-pusher + watchers | [wiki-ingest/](../application-architecture/wiki-ingest/) lab | none on Blackwell side; mutex with rl-2048 / wiki-compiler / inference at caddy ports |
| **rl-2048 mode** | `make rl-2048` | GRPO sandbox: Jupyter + MLflow on the 2048 RL environment | [rl-2048/](../application-architecture/rl-2048/) lab | wiki-compiler, inference (Blackwell + caddy ports) |
| **inference mode** *(NEW)* | `make inference` | Provide vLLM HTTP API for external consumers (customer-interview agents, benchmark harnesses, ad-hoc usage) — without spinning up the wiki-compile pipeline | [inference/](./inference/) self-contained mode (caddy + vllm-inference) | wiki-compiler, rl-2048 (Blackwell + caddy ports). Independent of `wiki-compiler` lab. |
| **wiki-bench mode** *(non-exclusive)* | `make wiki-bench` | One-shot CPU client benchmarking against the active mode's vLLM endpoint | [wiki-bench/](../application-architecture/wiki-bench/) lab | none — co-runs with whatever provides the inference endpoint (`wiki-compiler` or `inference`) |

## Key relationships

- **wiki-compiler mode and inference mode are independent.** Neither needs the other. wiki-compiler runs its own vllm-inference container internally; inference mode runs its own minimal vllm-inference container. They are mutex at runtime (same Blackwell GPU, same caddy ports) but architecturally they don't reference each other.
- **Both modes share underlying architecture:** the same vLLM image, the same `${INFERENCE_GPU_UUID}` pinning, the same `${STORAGE_ROOT}/shared/models` HuggingFace cache, the same proxy-net. They reuse architecture layers but not each other.
- **wiki-bench remains a non-exclusive client mode** that needs SOME inference endpoint — it can co-run with `wiki-compiler` or `inference` mode (both expose `${INFERENCE_DOMAIN}`).

## Adding a new mode

To add a new mode:

1. Create `phase-c-…/operating-modes/<mode-name>/` with:
   - `SPEC.md` (Phase A-H scaffolding; light)
   - `docker-compose.yml` (the containers this mode needs)
   - `Makefile` (`up`, `down`, `smoke` targets following common.mk)
   - `caddy/Caddyfile` if HTTP-facing
2. Add the mode to the top-level `Makefile`'s `LABS` list (modes share the same Make-target pattern as labs).
3. Update this file's mode table.
4. Land an ADR.
5. Update `phase-d-technology-architecture/architecture.md` GPU↔lab mapping table.

## Cross-references

- [Top-level `Makefile`](../../Makefile)
- [Phase D — `architecture.md`](../../phase-d-technology-architecture/architecture.md) — physical-layer mapping
- [ADR 0005 — inference subsystem](../../phase-preliminary/adr/0005-inference-subsystem.md) — original decision; mode mutex
- [ADR 0028 — inference mode as separate operating capability](../../phase-preliminary/adr/0028-inference-mode.md) *(this commit)*

## Measurable motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: customer-interview cycle (per ADR 0027) needs vLLM endpoint without spinning up the wiki-compile pipeline. Today that requires `make wiki-compiler` which name-confuses operators (wiki-compiler mode for inference work). Per architect call: «the mode is the mode, it's like exclusive operating capability on top of ea».
- **Goal**: [Architect-velocity](../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Operating-mode-as-EA-concept removes per-cycle naming confusion; one make target per operator-intent.
- **Outcome**: this directory + ADR 0028 + minimal inference mode implementation. Operating modes documented as Application Services; inference mode added as the first non-lab mode.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: separates mode-as-operating-capability from lab-as-implementation-unit; makes future mode additions cheap (no new lab required).
- **Capability realised**: [Service operation](../../phase-b-business-architecture/capabilities/service-operation.md).
- **Function**: Document-operating-modes-as-EA-concept.
- **Element**: this directory.
