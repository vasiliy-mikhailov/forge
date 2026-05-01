# Requirements catalog

Open and recently-closed requirements. Each row is a quality-
dimension trajectory or top-level goal. When a requirement closes,
its row is **deleted from this catalog** (per the architecture
method's delete-on-promotion rule); git history keeps every prior
state.

ID convention: `R-<phase>-<short-slug>`. Numbering is per phase.

## Open

### Phase B — capability trajectories

| ID                       | Source                    | Quality dim                                                  | Level 1 (today)                                                                            | Level 2 (next)                                                                          | Closure attempt        | Status |
|--------------------------|---------------------------|---------------------------------------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|------------------------|--------|
| R-B-svcop-thruput        | A: Architect-velocity     | Service Operation / throughput                               | ~47 tok/s decode batch=1 (Qwen3.6-27B-FP8)                                                 | ≥ 100 tok/s decode                                                                       | (deferred — see below) | OPEN   |
| R-B-svcop-stable24h      | A: Architect-velocity     | Service Operation / stability                                | ≥ 169 min sustained (one full module-005 pilot v5)                                         | ≥ 24 h continuous over 200-source runs                                                   | not yet planned        | OPEN   |
| R-B-voice-preservation   | A: TTS (product value)    | Compile lecture into source.md / preserves speaker voice     | Prior style guide asked for "voice of good lecture notes" — neutral encyclopedic register, voice stripped. K1 first run produced 7 verified sources reading like a generic summary | Narrative sections (TL;DR + Лекция) preserve author tone, sceptical asides, characteristic metaphors; structural sections (Claims, concepts) stay neutral. Validated on K1 modules 000+001 + future Tarasov pilot | K1 (in flight, restarted with revised Style)  | OPEN   |
| R-B-wiki-req-collection  | A: Architect-velocity     | Wiki requirements collection / discipline                    | Ad-hoc — implementation choices (prompts, schemas, graders) made by intuition; quality regressions like "Лекция reads as long TL;DR" or "voice stripped" diagnosed by eye-read each time, no R-NN to point to | Per-wiki product file under `phase-b-business-architecture/products/<wiki>/` enumerates Reading modes / Goals / Use cases / Information architecture; every prompt rule and grader check cites an R-NN from `catalog.md`; the activity in `phase-requirements-management/wiki-requirements-collection.md` has been walked at least once for the wiki | activity walked for kurpatov-wiki (in flight, evidence at `phase-b-business-architecture/products/kurpatov-wiki/`)  | OPEN   |

R-B-svcop-thruput is **deferred** at the model-swap level. G2
(MoE) and G3 (dense Gemma) both closed-falsified at the contract-
enforcement layer, not the throughput layer. New sub-requirements
were emitted into Phase D as a result — see below.

### Phase D — technology service trajectories

| ID                       | Source                | Quality dim                                       | Level 1 (today)                                                       | Level 2 (next)                                                      | Closure attempt                                | Status |
|--------------------------|-----------------------|---------------------------------------------------|------------------------------------------------------------------------|----------------------------------------------------------------------|------------------------------------------------|--------|
| R-D-retrieval-cost       | G2 + G3 close-out     | Vector retrieval / per-call cost                 | ~5 s per CLI fork (e5-base reload per claim)                          | daemonize embed_helpers; one model load per pilot                    | not yet opened (Phase F)                       | OPEN   |
| R-D-orchestration-kvcache| G2 closeout: KV-cache reuse rate measured at 0% across same-Conversation sub-agent calls | Agent orchestration / KV-cache reuse              | 0 % reuse across same-Conversation sub-agent calls                    | reuse → ~5-10× fewer prefill tokens per source                       | not yet opened (Phase F)                       | OPEN   |
| R-D-contract-prewrite    | G3 close-out (gate-4) | Agent orchestration / contract enforcement       | curator can write `concepts_touched` for slugs that have no concept file | pre-write existence check inside source-author / curator loop       | not yet opened (Phase F); blocks any next model-swap | OPEN   |
| R-D-contract-xreflint    | G3 close-out (gate-4) | Quality grading / cross-ref linting              | violations surface only after the source is committed                  | run-level lint after each commit, fail-fast on broken cross-refs    | not yet opened (Phase F)                       | OPEN   |
| R-D-test-fidelity        | K1 verify-fail (false-green synth) 2026-04-29 | Synth tests / production parity         | unit synth uses `Path.write_text()` while production uses agent's `file_editor`; passing tests gave false confidence | integration tests inside bench container that drive the agent end-to-end against a small synth fixture | three-layer ladder (unit / integration / e2e) green; ADR 0010 captures the rule | CLOSED 2026-04-30 |
| R-D-no-silent-skip       | K1 silent-skip incident 2026-04-29 | Pipeline correctness / source coverage | `D8_PILOT_FAIL_POLICY=continue` skipped 6 of 14 module-001 sources without surfacing it; pilot reported "completed" anyway | fail-fast default; opt-in continue writes `skipped_sources.json` manifest, exits non-zero, prints `WIKI INCOMPLETE` banner; publish step refuses to run when manifest non-empty | ADR 0012 (wiki-bench) + P6 enforced in `run-d8-pilot.py`; verified by K1 v2 on 2026-04-30 (1 skip → manifest + non-zero exit fired correctly) | CLOSED 2026-04-30 |
| R-D-verify-source-bug    | K1 verify-fail recurrence 2026-04-29 | Agent file-write reliability | `verify_source` falsely reports "did not appear" for healthy files; reproduces in production but NOT in 3-layer synth ladder; root cause unknown | reproduce in synth via real-data e2e fixture (real raw.json + shortened transcript), then fix root cause | root cause = NFC/NFD path mismatch (macOS-NFD on disk, LLM tokenizer NFC in agent output); fixed by ADR 0011 M1 (orchestrator NFC-normalises raw at clone time); ADR 0013 (Python coordinator) closes the broader agency-fragility class | CLOSED 2026-04-30 |

### Phase A — top-level goals not yet decomposed

| ID         | Goal                                       | Decomposition status                                                                                       |
|------------|--------------------------------------------|------------------------------------------------------------------------------------------------------------|
| R-A-PTS    | PTS (Practical Time Saved) growing over time | Blocked on user count > 1. Cannot be addressed before that — currently a placeholder.                     |
| R-A-EB     | EB ≥ 0 (Economic Balance)                  | Implicit; no explicit measurement today. To open as Phase B requirement when first paying user lands.    |

