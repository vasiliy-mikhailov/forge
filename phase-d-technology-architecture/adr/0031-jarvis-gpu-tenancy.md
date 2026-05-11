# ADR 0031 -- Forge GPU pool serves omega (jarvis) reptile + limbic as shared dynamic tenancy

## Status

Accepted (2026-05-10). Active.

## Measurable motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: jarvis (omega daughter) is moving from pure
  inference tenant (consuming `inference-mode` for ralph-loop
  reasoning) to a three-layer brain architecture in which
  jarvis-reptile-brain (openhands + vllm + vision + RLVR) and
  jarvis-limbic (context condenser) need persistent GPU
  residency on the forge pool. The existing
  `inference-mode` tenancy pattern (single served model on
  Blackwell, condenser on 5090) was sized for forge's own
  labs (reward-bench / wiki-*) and serves jarvis as a
  one-shot Bearer-token client. The new jarvis topology
  needs longer-lived allocation across both GPUs that
  forge currently treats as serial single-model devices.
- **Goal**: Architect-velocity (KR: <= 20 execution failures
  per 30-day window). Without an ADR fixing the tenancy
  model, jarvis cortex (Claude in Cowork) would re-derive
  GPU allocation on every session start and the answer
  would drift between sessions. Codifying once removes the
  drift class.
- **Outcome**: forge's Blackwell + 5090 form a single
  shared GPU pool. When omega-reptile and omega-limbic are
  active, they hold the pool. When forge's own labs
  (reward-bench / wiki-*) are active, they hold the pool.
  No partition; mutex membership prevents collision.
- **Measurement source**: audit-predicate: lab-mutex log
  shows exactly one mutex holder at a time across forge
  labs + jarvis omega-reptile + jarvis omega-limbic.
  Concurrent holders = audit FAIL.
- **Contribution**: ADR specifies the tenancy invariant
  the audit checks; removes one execution-failure class
  from forge-vs-jarvis coordination.

## Context

The integration baseline (forge-response-2026-05-09,
addendum 2026-05-10) established jarvis as a tenant of
forge's `inference-mode`. That covered jarvis Brain
(then = Claude) issuing single-shot completions over
HTTPS. The 2026-05-10 architectural pivot (control-minecraft
three-layer brain) splits jarvis-brain into three parts:

- **jarvis-cortex** (Claude in Cowork, cloud) -- no forge GPU.
- **jarvis-limbic** (condenser model, forge 5090) -- new
  persistent tenancy.
- **jarvis-reptile-brain** (openhands + vllm + vision +
  RLVR, forge Blackwell) -- new persistent tenancy.

The single-Bearer-token client model from the integration
baseline does not cover the new shape. Reptile-brain holds
a vllm process and KV cache continuously for a session's
duration; limbic holds a condenser model continuously.
Both compete with forge's own labs for the same physical
GPUs.

This ADR specifies the tenancy invariant: shared pool,
mutex-mediated.

## Decision

### 1. Pool definition

The forge GPU pool consists of:

| Device | Capacity | Identifier |
|---|---|---|
| RTX PRO 6000 Blackwell | 96 GB VRAM | `$GPU_BLACKWELL_UUID` |
| RTX 5090 | 32 GB VRAM | `$GPU_RTX5090_UUID` |

Both devices are forge-owned hardware. Both are tenant-
multiplexed across:

- forge's own labs (`reward-bench`, `rl-2048`, `wiki-ingest`,
  `wiki-compiler`, `wiki-bench`)
- omega (jarvis): `omega-reptile`, `omega-limbic`
- future psi (course-wiki) tenancy if/when psi gains its
  own runtime services (today: none)

### 1a. Tenancy modes (added 2026-05-11)

forge is a home-lab dev environment with no production/UAT/staging
stage gates. Within that flat environment, two tenancy modes share
the GPU pool:

| Mode | Definition |
|---|---|
| **Lab** | Formally architected workload: SPEC, ADR(s), smoke tests, catalog entry (in `phase-c-.../application-architecture/` for forge labs, in the daughter\'s subsidiary catalog for daughter labs). Claims an explicit resource set in the mutex at start. Not preemptable. |
| **Playground** | Informal exploration of what a future lab might become. May implement only part of the future lab\'s architecture. May have only a SPEC drafted, or none. Uses resources NOT currently held by any lab. Held on architect permission; released on architect request. No catalog entry; no formal preemption protocol (the architect controls both sides of the request). |

**Concurrency rule:** at most **one lab** and at most **one
playground** active at a time. Two labs concurrently are still
forbidden (the cognitive-bandwidth argument in section 2 stands).
Two playgrounds simultaneously also forbidden, same reason.

**Resource priority:** **lab has priority over playground for any
resource.** A playground borrows what no lab currently holds; if a
lab claim arrives for a playground-held resource, the playground
releases it within the architect-requested window. The kid-using-
the-workshop metaphor: the playground uses dad\'s tools when dad
isn\'t using them and hands them back the moment dad asks.

**Transition:** a playground becomes a lab when it earns the
paperwork -- SPEC committed, ADR landed, catalog entry created,
explicit resource set declared in the mutex. After that it is
subject to the lab rules including non-preemption.

**Today\'s state at 2026-05-11:** reward-bench campaign is a lab
holding the Blackwell. control-minecraft on 5090 with
Nemotron-3-Nano-Omni NVFP4 (planned next) is a playground; it has
a SPEC ([reptile-brain SPEC](../../phase-c-information-systems-architecture/application-architecture/jarvis-reptile-brain/SPEC.md)
on the daughter side) but no formal resource claim and may be
torn down at any time on architect request.

### 2. Mutex membership

All seven principals listed above belong to the **forge
lab-mutex**: at most one principal holds the pool at any
time. The principal currently holding the pool is
identified by the active mutex token at
`/mnt/steam/forge/lab-mutex/holder.json` (existing forge
mechanism; jarvis-side mirror lives at
`/home/vmihaylov/jarvis/mutex/holder.json` reading the
same file via the forge-mount).

When omega-reptile or omega-limbic want to start, they
acquire the mutex via the existing lab-coordinator
manual-with-discipline protocol per
[forge response Q5](../../phase-h-architecture-change-management/subsidiary-integration/forge-response-2026-05-09.md#q5--lab-coordinator-service).
Until forge stands up the lab-coordinator as a Phase D
service, the architect is the coordinator.

### 3. Dynamic split, not dedicated assignment

omega-reptile + omega-limbic together draw from the shared
pool. Within a single jarvis session:

- omega-reptile runs vllm on Blackwell with `qwen3.6-27b-fp8`
  (campaign winner per reward-bench 2026-05-08 campaign,
  trial best 21,079). Vision model time-multiplexes on the
  same Blackwell.
- omega-limbic runs condenser model on 5090 with
  `llama-3.1-8b-nvfp4` (existing reward-bench condenser
  binary -- shared, not duplicated).

The split is **not dedicated**: if reptile-brain needs more
VRAM than 96GB (it won't in v1, but might once RLVR LoRA
training joins the same process), the next iteration may
migrate part of reptile-brain to the 5090. Today: the
default placement holds, with the explicit understanding
that this is an experiment configuration. Re-partitioning
is a daughter-side change, not a forge ADR change.

### 4. Sanitisation rules

The vllm process serving `qwen3.6-27b-fp8` to omega-reptile
emits standard vllm access logs (request ID, token counts,
latency). Per ADR 0030 §2 and forge response §7.4:

- The vllm process's access logs MUST NOT include the
  request body (game-state, vision-derived structured
  state, openhands tool outputs). vllm's default behaviour
  is to log only metadata; this default is invariant.
- The container running vllm MUST be labelled with the
  alias `omega-reptile` and never `jarvis-reptile-brain`
  in image tags, container names, or process titles
  reaching forge-public surfaces. The internal-LAN
  hostname `forge-omega-reptile.internal` is acceptable
  per the addendum's relaxation of G3.1a/b for
  LAN-private FQDNs.
- Frames from jarvis-eyes that reach the Blackwell never
  hit disk on forge. They live in vllm's request buffer,
  get processed, and are dropped. Forge MUST NOT add
  frame-logging at any layer.

### 5. Aliases on forge-public per ADR 0030

| Surface | Internal name (jarvis-side) | forge-public alias |
|---|---|---|
| Container / image tag | jarvis-reptile-brain | omega-reptile |
| Container / image tag | jarvis-limbic | omega-limbic |
| vllm served-model-name | qwen3.6-27b-fp8-omega | (same -- forge service name OK) |
| Audit findings | reptile-brain finding | omega-reptile finding |
| Tenancy entry on this side | -- | tenant: omega |

forge-public surfaces NEVER mention jarvis-reptile-brain
or jarvis-limbic directly. forge-private companion
artefacts (this ADR's working tree, forge-internal
governance docs) MAY use the full names.

### 6. Lab-mutex implications for the running reward-bench campaign

The 2026-05-08 reward-bench campaign + its quant addendum
is currently the mutex holder. Per the campaign's
single-mutex design, jarvis-reptile-brain experiments
must EITHER:

- wait for the campaign + addendum to complete (~3 days
  from 2026-05-10 if no further interruption); OR
- preempt the campaign via architect call. The campaign
  is checkpointed at sweep boundary; preempting between
  sweeps loses no completed-trial data. Preempting mid-
  trial loses the in-flight trial only.

The preemption protocol: architect (or jarvis cortex
acting on architect's behalf) writes `preempt: omega-reptile`
to `holder.json` requested field; the campaign's
`run_sweep` loop reads this between trials and yields
the mutex. Implementation lands in a follow-up commit on
the campaign side.

### 7. Tenancy entry in service-tenancy.md

Forge `phase-d-technology-architecture/service-tenancy.md`
gets two new tenant rows for omega-reptile and omega-limbic
under the Blackwell + 5090 sections. Same pattern as the
existing reward-bench / wiki-* / inference-mode rows.

## Consequences

- **Plus**: jarvis cortex on session start reads this ADR
  and knows the mutex protocol without re-deriving it.
  Removes a per-session execution-failure class.
- **Plus**: the existing reward-bench condenser binary is
  shared with omega-limbic -- no duplication, no second
  llama-3.1-8b model load.
- **Plus**: psi (course-wiki) gets the same tenancy model
  for free if/when it grows a runtime component, by
  symmetry.
- **Minus**: the mutex prevents concurrency between
  reward-bench and jarvis. For development phases that's
  fine; for production-cadence operation it would bind
  G2 (Architect-velocity) and force the Phase D lab-
  coordinator service forward. Acceptable for the v1
  experiment.
- **Minus**: the 96GB Blackwell holding vllm + vision +
  RLVR LoRA simultaneously is tight. ADR records this as
  acceptable for the experiment; partitioning may be
  needed once RLVR scales. That's a daughter-side ADR.

## Invariants

- The forge lab-mutex log shows at most one principal
  holding the pool at any time. Concurrent holders =
  audit FAIL.
- forge-public surfaces use `omega-reptile` /
  `omega-limbic` aliases per ADR 0030, never the
  jarvis-internal names.
- vllm serving omega-reptile MUST NOT log request bodies.
  Frames from jarvis-eyes never hit forge disk.
- New principals joining the pool (psi runtime, future
  daughters) update this ADR with a new row in §1 and
  §2; mutex membership is the single source of truth for
  who can hold the pool.

## Alternatives considered

- **Partition the pool**: dedicate Blackwell to omega-reptile
  and 5090 to omega-limbic, partition forge labs onto
  whichever GPU is free. Rejected for v1: forge labs need
  both GPUs (reward-bench currently uses Blackwell for
  candidate + 5090 for condenser); partitioning would
  block forge from running its own work. The mutex model
  keeps both GPUs available to whichever principal holds
  the pool.
- **Dedicate a third GPU to jarvis**: would solve
  concurrency. Rejected: capital cost, no GPU available.
- **Run omega-reptile in cloud (not on forge GPUs)**:
  considered. Rejected: latency budget for the per-action
  loop is too tight to cross the public internet on every
  vllm call. Local-GPU residency is the architecture; the
  shared pool is the consequence.

## Follow-ups

- **forge campaign preemption protocol**: implement the
  `preempt: <principal>` field in `holder.json` and the
  campaign-side yield logic. Spec lands in a follow-up
  commit on the reward-bench side. Until then, manual
  preemption (kill + restart campaign) is the practice.
- **Lab-coordinator Phase D service** (forge response Q5):
  this ADR raises the value-of-having-it because every new
  daughter tenant adds mutex-coordination cost. Still not
  on the immediate roadmap; revisit when cadence binds.
- **Frame-no-disk audit predicate** (P31 queued): scan
  forge logs for image-byte fields under
  omega-reptile-named containers. Default WARN, FAIL if
  found.

## References

- [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md)
  -- subsidiary URL visibility and operational alias regime.
- [ADR 0018](../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md)
  -- content-privacy boundary; this ADR extends content-no-
  forge-disk to live frames.
- [forge response 2026-05-09](../../phase-h-architecture-change-management/subsidiary-integration/forge-response-2026-05-09.md)
  Q4, Q5 -- token rotation and lab-coordinator follow-ups
  cited above.
- jarvis ADR 0008 (three-layer brain) -- daughter-side
  counterpart establishing the architecture this ADR
  supports.
