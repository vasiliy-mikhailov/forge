# Phase D — Technology Architecture

The Forge platform realises Phase B capabilities through a small set
of **technology services**, each provided by one or more **technology
components / system software**. Capabilities live upstairs (Phase A/B);
this folder is about *how* they are realised, not *what* they are.

## Technology services

One file per service in [`services/`](services/):

- [`llm-inference.md`](services/llm-inference.md)
- [`agent-orchestration.md`](services/agent-orchestration.md)
- [`vector-retrieval.md`](services/vector-retrieval.md)
- [`container-runtime.md`](services/container-runtime.md)
- [`transcription.md`](services/transcription.md)
- [`source-of-truth.md`](services/source-of-truth.md)

## Cross-service docs

- [`invariants.md`](invariants.md) — forge-wide rules every service
  obeys (single-server, containers-only, GPU power mgmt).
- [`service-tenancy.md`](service-tenancy.md) — which services are
  forge-wide vs lab-local; where a change lands.
- [`architecture.md`](architecture.md) — physical topology
  (network, ports, storage layout).
- [`components/`](components/) — physical components and their
  on-host realisation (when a service is provided by more than one
  artifact).
- [`adr/`](adr/) — Phase D scoped ADRs.
