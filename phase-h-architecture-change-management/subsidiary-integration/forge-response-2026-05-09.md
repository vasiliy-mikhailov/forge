# Forge response to jarvis integration response -- 2026-05-09

| | |
|---|---|
| From | forge architecture (architect of record) |
| To | jarvis architecture team |
| Re | jarvis [response-2026-05-09](https://github.com/vasiliy-mikhailov/jarvis/blob/main/phase-h-architecture-change-management/forge-integration/response-2026-05-09.md) (commit `080d506`, follow-up `ecfad38`) |
| Status | Decisions on jarvis open questions 1-6; integration baseline closed |

This response answers jarvis's six open questions in section 11 of
the response document. The G3.1 refinement is treated separately
(landed as forge ADR 0030 before this response was written; jarvis
G3.1a now cites it).

## Q1 -- DNS rename schedule

**Decision: approved.** Jarvis-side rename `jarvis-eyes.mikhailov.tech`
-> `e1.internal` and `jarvis-hands.mikhailov.tech` -> `h1.internal`,
plus `busy-board.mikhailov.tech` -> `t1.internal`. Public ingress
collapses to `forge.mikhailov.tech:443` only. Move everything off
the public zone in one commit on jarvis side; forge-edge DNS
records change same-day in coordination.

**Rationale.** The leak is active and the proposed fix is correct.
The cost of staging the rename (per-host with overlap windows) is
higher than just doing it in one commit, since the only client of
the existing public hostnames is jarvis Brain, which can be
updated atomically alongside the rename.

**Actions on forge side.**

- Update DNS at the registrar: remove `jarvis-eyes`, `jarvis-hands`,
  `busy-board` A records from the public `*.mikhailov.tech` zone the
  same day jarvis pushes the rename commit.
- Confirm `forge.mikhailov.tech` already points at the GPU host
  edge; if not (it currently points to `inference.mikhailov.tech`),
  add the alias.
- Add a recurring audit step: scan public DNS for any
  jarvis-identifying hostnames; expected-empty after this rename.
  Spec lands in next audit cycle.

**Actions on jarvis side (for jarvis to confirm).**

- Single commit that renames hosts in jarvis SSH config, ADR-0003
  (SSH via port-forward on edge), Brain bootstrap scripts, and any
  remaining hardcoded references.
- Schedule the cutover; forge will do the registrar change in the
  same window.

## Q2 -- Subsidiary catalog location

**Decision: forge-public, with anonymised-but-URL-bearing entries.**
ADR 0030 makes interpretation (a) (forge-private companion repo)
unnecessary -- since bare URLs to auth-gated daughter repos are now
permitted on forge-public, the catalog can live in forge-public
with full URL references plus alias-only operational tags.

**Concrete spec.**

Location: `phase-b-business-architecture/subsidiaries/` on forge.

One file per daughter, named by Greek-letter alias:
- `omega.md` for jarvis
- `psi.md` for course-wiki when it lands

Each file contains:
- Daughter name (jarvis/course-wiki -- per ADR 0030 the name is
  permitted alongside the URL)
- Bare repo URL (per ADR 0030)
- One-line category tag (e.g. "private operational tenant",
  "private content pipeline")
- Pointer to the daughter's own `phase-b-...` for capability /
  product detail (auth-gated, not browseable from forge-public)
- Architect-of-record (= same person)

What the file does NOT contain:
- Capability descriptions
- Product names or descriptions
- Service-tenancy details
- Lab listings
- Quality numbers or operational metrics

The catalog directory MUST NOT have a top-level README that
enumerates daughters in prose -- the directory listing itself is
the catalog. Each file is its own entry; readers count files to
count daughters.

**Actions on forge side.**

- Create `phase-b-business-architecture/subsidiaries/` directory.
- Add `phase-b-business-architecture/subsidiaries/omega.md` for
  jarvis with the spec above.
- Update forge top-level `AGENTS.md` (root nav index) to mention
  the subsidiaries directory exists; do not enumerate.

## Q3 -- Audit report storage

**Decision: forge-public, audit reports keyed by alias, contents
follow ADR 0030.** Same answer as Q2 by ADR 0030 logic.

**Concrete spec.**

Location: `phase-h-architecture-change-management/subsidiary-audits/`
on forge.

Filename pattern: `<greek-letter>-YYYY-MM-DD.md`
(e.g. `omega-2026-05-09.md`, `psi-2026-08-15.md`).

Contents follow ADR 0030 split:
- Bare daughter URL is fine.
- Daughter name as a tag is fine.
- Operational identifiers (service names, host names, lab names
  that name what the daughter does, error message fields, log
  lines, capability quality numbers) MUST use the daughter's
  declared alias table.
- Audit findings cite opaque IDs (e.g. "omega lab forge-omega-vdi
  consumed N llm-inference-hours in window X") where the resolution
  table lives in the daughter's private repo.

**Actions on forge side.**

- Create `phase-h-architecture-change-management/subsidiary-audits/`
  directory at first audit.
- First audit (`omega-2026-MM-DD.md`) follows the next monthly
  audit cycle; it audits jarvis's adherence to its own G3.1a/b
  declarations and forge's adherence to ADR 0030.

## Q4 -- Token rotation tooling

**Decision: build a single rotation mechanism in forge before the
first 90-day window expires; rotate manually until then.**

**Honest answer.** Forge does not currently have automated token
rotation tooling for any of its tokens (`VLLM_API_KEY` is
manually-rotated, `HF_TOKEN` is manually-rotated, etc.). The
proposal in jarvis's section 4.3 (90-day cadence for
`bearer-token-llm-inference`, 180-day for `git-deploy-key`,
90-day for `audit-output-write-token`) requires tooling forge
does not have today.

The honest path:
- Treat token rotation tooling as a forge Phase D service that
  doesn't exist yet. File as a follow-up.
- Until tooling exists, both forge proper and the jarvis-tenant
  tokens rotate manually. Cadence matches jarvis's proposed
  90/180/90 from `ecfad38`+, on a calendar reminder.
- When tooling lands, jarvis's tokens enroll in the same mechanism
  -- single secrets store, single rotation pipeline, namespaced
  per-subsidiary per jarvis section 4.2.

**Actions on forge side.**

- Add follow-up to roadmap: token rotation as a Phase D service.
  Acceptance criterion: one CLI command rotates a named token,
  updates the secrets store, signals dependent processes (or
  notifies architect if no signal channel exists yet).
- Until then: calendar reminder for jarvis tokens at 90 days from
  issue, plus the same for forge's own tokens.
- Document the manual cadence in forge governance
  (`phase-g-implementation-governance/policies/`).

## Q5 -- Lab coordinator service

**Decision: not on immediate roadmap; manual-with-discipline
remains the pattern until concurrent labs become routine.**

**Rationale.** Today the lab schedule fits in one architect's
head: `llm-inference` runs one model at a time, jarvis labs that
consume it (`forge-omega-mc`, `forge-omega-vdi`, `forge-omega-2048`
Option B) wait their turn alongside forge's own
`reward-bench` / `wiki-compiler` / `wiki-bench` consumers. The
campaigns currently running are sequential by design (the
campaign script tears down and re-brings-up vLLM between sweeps).

Standing up a Phase D coordinator service makes sense when:
- Two or more campaigns want to run concurrently with different
  model loads (today: never).
- More than one human or agent wants to schedule against the same
  GPU pool (today: one architect).
- The cost of the manual scheduling exceeds the cost of standing
  up the service.

None of those conditions hold today. Promoting the coordinator to
a Phase D service prematurely would be an A-V cost (more code to
maintain, more abstraction for one architect to navigate) for no
G2 benefit.

**Actions on forge side.**

- Add follow-up to roadmap: "lab-mutex coordinator -- promote to
  Phase D service when concurrent demand emerges". No date.
- Document the current manual-with-discipline pattern explicitly
  in `phase-g-implementation-governance/policies/` so jarvis
  doesn't have to re-derive it.
- Acknowledge in the forge response that the lack of a coordinator
  binds A-V at higher cadences. If jarvis wants to drive a higher
  cadence (e.g. multiple Brain sessions per day across
  `control-2048` Option B / `control-mc` / `control-vdi`), revisit.

## Q6 -- G3.1 -> G3.1a refinement

**Already accepted.** Forge ADR 0030 (commit `e8f5753`) adopts the
G3.1a + G3.1b split as a forge-level principle applicable to all
present and future daughter companies. Jarvis G3.1a (commit
`ecfad38`) cites ADR 0030 as the parent principle.

This question is closed. ADR 0030 also queues a follow-up audit
predicate (P30) to enforce the URL-permitted /
operational-identifier-aliased distinction at the forge boundary.

## Closing notes

Integration baseline is closed. The five live decisions above
(Q1, Q2, Q3, Q4, Q5) translate to the following forge-side commits
in the next working session:

1. DNS registrar update (Q1) -- coordinated with jarvis cutover
   commit, same-day.
2. `phase-b-business-architecture/subsidiaries/omega.md` for jarvis
   (Q2) -- same session as DNS cutover.
3. `phase-h-architecture-change-management/subsidiary-audits/`
   directory created at next audit cycle (Q3).
4. Roadmap entries: token rotation Phase D service (Q4),
   lab-mutex coordinator (Q5).
5. `phase-g-implementation-governance/policies/` updates: manual
   token rotation cadence, manual lab-mutex pattern.

Future course-wiki integration brief will reference ADR 0030 + ADR
0018 + this response, and is expected to be shorter than jarvis's
brief by exactly the amount of vocabulary now established.

Joint review cadence: monthly, aligned with forge's
`phase-h-architecture-change-management` audit rhythm. First joint
review picks up any drift on the five live decisions.

-- forge architecture (architect of record), 2026-05-09
