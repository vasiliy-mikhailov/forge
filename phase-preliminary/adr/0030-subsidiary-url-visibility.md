# ADR 0030 -- Subsidiary URL visibility: bare URLs to private subsidiary repos may appear on forge-public surfaces if the URL is auth-gated

## Status

Accepted (2026-05-09). Active.

## Measurable motivation chain

Per [P7](../architecture-principles.md):

- **Driver**: forge is acquiring private daughter companies
  (jarvis is the first; course-wiki follows). Each daughter
  has a private GitHub repo. The original integration brief
  treated every appearance of a daughter-company name on a
  forge-public surface as a leak. Jarvis pushed back in
  [response-2026-05-09 section 7](https://github.com/vasiliy-mikhailov/jarvis/blob/main/phase-h-architecture-change-management/forge-integration/response-2026-05-09.md):
  hiding bare *existence* costs more than it buys (anyone
  can see private repos exist on github), while hiding
  *contents* is what actually matters. The architect agreed;
  this ADR records the principle at forge level so every
  present and future daughter inherits it without
  re-deriving.
- **Goal**: Architect-velocity (KR: <= 20 execution failures
  per 30-day window). Without this principle, every commit
  that names a daughter URL would require a re-derive of
  "is this leak acceptable"; with it, the rule is one-line:
  the URL is fine if it is auth-gated, the contents are not.
- **Outcome**: forge-public artefacts (any phase, any file)
  may contain bare URLs to a private daughter-company repo.
  forge-public artefacts may NOT contain operational
  identifiers (host names, service names, lab outputs,
  capability descriptions, audit findings citing daughter
  internals) -- those still pass through the per-daughter
  alias scheme defined in the daughter-company's own
  G3.1b-equivalent goal.
- **Measurement source**: audit-predicate: P30 (queued --
  scan forge-public for non-aliased daughter operational
  identifiers; bare URLs to auth-gated repos exempt).
- **Contribution**: ADR removes one false-positive class
  from the privacy audit; contributes to A-V KR by
  eliminating a recurring "is this a leak" deliberation.

## Context

Forge's pre-2026-05-09 framing (in the integration request
sent to jarvis on 2026-05-08) treated subsidiary opacity
as absolute: nothing forge-public could name a daughter
company. Jarvis's first-pass response (commit 080d506)
split G3.1 into two sub-sub-goals:

- **G3.1a -- Name privacy** (relaxed). A URL to a private
  repo on a forge-public surface is acceptable *if and only
  if* the URL is just a pointer that bounces off
  authentication. The URL leaks the bare fact that a private
  repo by that name exists; the auth wall protects what is
  inside.
- **G3.1b -- Content privacy** (strict). The contents of a
  daughter repo -- architecture, products, services, code,
  calibration data, tenancy details, operational
  identifiers -- never leave the auth-gated boundary.

This ADR adopts the same split as a forge-level principle
applicable to **any** private daughter company (jarvis,
course-wiki, future entities), so each daughter's own
G3.1a-equivalent goal cites this ADR rather than re-deriving
the rationale.

## Decision

### 1. Bare URLs to auth-gated daughter repos are permitted on forge-public

Concretely: forge-public files (README, ADRs, Phase B
catalogs, audit reports, anywhere in the public tree) MAY
contain references like
`git@github.com:vasiliy-mikhailov/jarvis.git` or
`https://github.com/vasiliy-mikhailov/jarvis`.

The rule for "auth-gated" is operational, not theoretical:
the repo MUST currently require authentication to clone or
read. If the repo flips public, this ADR's permit dissolves
and the URL becomes a content reference.

### 2. Operational identifiers still require aliases

Every other class of identifier -- service names, host
names, model IDs, image tags, error fields, log lines,
lab names that name what the daughter actually does --
remains under the daughter's G3.1b-equivalent strict-
privacy regime. Each daughter publishes (in its own private
repo) an alias table mapping internal names to
forge-public-safe aliases; forge-public uses the aliases.

The split is summarised:

| Surface element | forge-public permitted? |
|---|---|
| URL to auth-gated daughter repo | yes |
| Daughter company name as a one-line catalog tag (e.g. "subsidiary: jarvis") | yes if the name is also the auth-gated repo's URL slug |
| Service / host / lab name (operational) | no -- use alias |
| Capability / product description content | no -- lives in the daughter |
| Lab output content (datasets, calibration data, dashboards) | no -- lives in the daughter |
| Audit findings citing daughter internals | no -- use opaque IDs that resolve in private |

### 3. Daughter goals docs SHOULD cite this ADR

Each daughter's `phase-a-architecture-vision/goals.md`
G3.1a-equivalent text MUST link to this ADR as the
forge-level source of the principle, so the daughter's
goal text becomes "inherits ADR 0030; daughter-specific
notes follow" rather than re-deriving the rationale per
daughter. Jarvis's G3.1a (commit 080d506+) gets a follow-up
edit citing this ADR.

### 4. Course-wiki forward compatibility

When course-wiki spins up, its goals.md will include a
G3.1a citing this ADR by reference, with course-wiki-
specific examples of what "content" means in its case
(probably the Kurpatov / Tarasov compiled wiki contents,
which are already private per [ADR 0018](0018-privacy-boundary-public-vs-private-repos.md)).
ADR 0018's content-privacy regime and ADR 0030's URL-
permission regime stack: ADR 0030 says "course-wiki's URL
on forge-public is fine"; ADR 0018 says "the *contents* of
the kurpatov-wiki repo do not come back into forge".

### 5. Sanitization rules unchanged for content

Log-aggregation strip-rules, error-response wrapping,
container-image-tag aliases, and model-registry aliases --
all unchanged from the original integration brief. This ADR
moves only one cell: the URL itself.

## Consequences

- **Plus**: removes a false-positive leak class from every
  forge-public artefact that needs to point to a daughter.
  Subsidiary catalog entries can include the literal URL
  without an aliasing dance.
- **Plus**: daughter goals docs simplify -- one ADR-0030
  citation rather than a per-daughter re-derivation.
- **Plus**: makes the future course-wiki integration
  cheaper; the aliasing machinery already designed for
  jarvis applies symmetrically.
- **Minus**: an outside observer of forge-public learns the
  list of daughter companies (their names, their URLs).
  Accepted: the cost of hiding that list is high (every
  catalog entry rewritten through an alias) and the
  benefit is low (anyone scanning vasiliy-mikhailov's
  github account would see the same private-repo entries
  with no auth required).
- **Minus**: introduces a second invariant for audits to
  enforce (P30): bare URLs OK, operational identifiers not
  OK -- auditor must distinguish. P30 spec covers this; the
  distinction is clean (URL = scheme + host + path matching
  a known auth-gated repo; operational identifier = anything
  else).

## Invariants

- A forge-public artefact containing a bare URL to a
  currently-auth-gated daughter repo passes P30.
- A forge-public artefact containing a daughter operational
  identifier (host name, service name, capability description,
  lab output content) fails P30 unless the identifier is the
  daughter's declared public alias.
- If a previously-private daughter repo flips public, this
  ADR's permit dissolves and the URL becomes a content
  reference -- auditor escalates to architect-of-record.
- Daughter goals docs that cite this ADR for G3.1a inherit
  the rationale; daughter-specific G3.1b text remains the
  daughter's responsibility.

## Alternatives considered

- **Hold the original line -- no daughter URL on forge-public,
  ever.** Rejected per the cost/benefit above. Forces a
  per-catalog alias dance that buys little (private repos
  are not actually hidden by forge-side aliasing if the
  github.com listing is browseable) and costs ongoing
  vigilance.
- **URL allowed, daughter name not.** Rejected as
  unnecessarily fine-grained: the URL contains the name.
  Treating the URL as permitted and the name as not yields
  a contradiction.
- **Defer until course-wiki actually lands.** Rejected: the
  jarvis integration is in flight now; deferring leaves
  jarvis's G3.1a as a daughter-specific principle that
  course-wiki would re-derive. Establishing the rule at
  forge level once is cheaper than twice.

## Follow-ups

- **P30 audit predicate**: scan forge-public for daughter
  operational identifiers not in the daughter-declared
  alias table; bare URLs to currently-auth-gated daughter
  repos exempt. Spec lands in
  `phase-h-architecture-change-management/audit-process.md`
  next audit cycle.
- **Jarvis G3.1a edit**: jarvis architecture team adds a
  sentence to G3.1a citing this ADR as the parent principle.
  Tracked in jarvis's own change log.
- **Subsidiary-catalog directory on forge**: needed to land
  before the first jarvis-named entry appears. Proposed
  location: `phase-b-business-architecture/subsidiaries/`,
  one file per daughter, naming-scheme: file name uses the
  Greek-letter alias (`omega.md` for jarvis, `psi.md` for
  course-wiki). The URL inside the file is the daughter's
  bare URL, permitted by this ADR.
- **Course-wiki integration brief**: when issued, will
  reference this ADR and ADR 0018; the daughter-specific
  brief is shorter than jarvis's by exactly the amount this
  ADR generalised.
