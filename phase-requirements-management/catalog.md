# Requirements catalog

Open and recently-closed requirements. Each row is a quality-
dimension trajectory or top-level goal. When a requirement closes,
its row is **deleted from this catalog** (per the architecture
method's delete-on-promotion rule); git history keeps every prior
state.

ID convention: `R-<phase>-<short-slug>`. Numbering is per phase.

## Open

### Phase B — capability trajectories

| ID                  | Source             | Quality dim                          | Level 1 (today)                                     | Level 2 (next)                                  | Closure attempt        | Status |
|---------------------|--------------------|---------------------------------------|------------------------------------------------------|-------------------------------------------------|------------------------|--------|
| R-B-svcop-thruput   | A: Architect-velocity | Service Operation / throughput     | ~47 tok/s decode batch=1 (Qwen3.6-27B-FP8)          | ≥ 100 tok/s decode                              | (deferred — see below) | OPEN   |
| R-B-svcop-stable24h | A: Architect-velocity | Service Operation / stability      | ≥ 169 min sustained (one full module-005 pilot v5)   | ≥ 24 h continuous over 200-source runs          | not yet planned        | OPEN   |

R-B-svcop-thruput is **deferred** at the model-swap level. G2
(MoE) and G3 (dense Gemma) both closed-falsified at the contract-
enforcement layer, not the throughput layer. New sub-requirements
were emitted into Phase D as a result — see below.

### Phase D — technology service trajectories

| ID                       | Source                | Quality dim                                       | Level 1 (today)                                                       | Level 2 (next)                                                      | Closure attempt                                | Status |
|--------------------------|-----------------------|---------------------------------------------------|------------------------------------------------------------------------|----------------------------------------------------------------------|------------------------------------------------|--------|
| R-D-retrieval-cost       | G2 + G3 close-out     | Vector retrieval / per-call cost                 | ~5 s per CLI fork (e5-base reload per claim)                          | daemonize embed_helpers; one model load per pilot                    | not yet opened (Phase F)                       | OPEN   |
| R-D-orchestration-kvcache| Phase D analysis      | Agent orchestration / KV-cache reuse              | 0 % reuse across same-Conversation sub-agent calls                    | reuse → ~5-10× fewer prefill tokens per source                       | not yet opened (Phase F)                       | OPEN   |
| R-D-contract-prewrite    | G3 close-out (gate-4) | Agent orchestration / contract enforcement       | curator can write `concepts_touched` for slugs that have no concept file | pre-write existence check inside source-author / curator loop       | not yet opened (Phase F); blocks any next model-swap | OPEN   |
| R-D-contract-xreflint    | G3 close-out (gate-4) | Quality grading / cross-ref linting              | violations surface only after the source is committed                  | run-level lint after each commit, fail-fast on broken cross-refs    | not yet opened (Phase F)                       | OPEN   |

### Phase A — top-level goals not yet decomposed

| ID         | Goal                                       | Decomposition status                                                                                       |
|------------|--------------------------------------------|------------------------------------------------------------------------------------------------------------|
| R-A-PTS    | PTS (Practical Time Saved) growing over time | Blocked on user count > 1. Cannot be addressed before that — currently a placeholder.                     |
| R-A-EB     | EB ≥ 0 (Economic Balance)                  | Implicit; no explicit measurement today. To open as Phase B requirement when first paying user lands.    |

