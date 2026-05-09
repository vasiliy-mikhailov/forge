# Integration request: jarvis → forge

**From:** forge architecture team
**To:** jarvis architecture team
**Subject:** Information needed to incorporate jarvis as a private daughter company of forge
**Status:** Request for inputs

## Context

forge is establishing jarvis as a private, wholly-owned daughter company. jarvis must mirror forge's TOGAF-style architecture repository structure (phase-a through phase-h, preliminary, requirements-management), and its operational artifacts (labs, services, inference modes) must be reachable from forge — appearing to forge users as a natural extension of forge's labs and operating modes.

The defining constraint is **opacity to the outer world**: nothing in forge's externally-visible artifacts (public docs, code repos that ever ship outside forge, model registry entries that reach external partners, container labels, serving names, model IDs returned to API clients, log lines that leave the boundary) may identify jarvis as a separate legal entity, name jarvis directly, or expose jarvis-internal hostnames, IPs, paths, or repo URLs. From the outside it must look like forge.

A separate, future daughter company **course-wiki** will absorb the existing `kurpatov-wiki` content (and likely the Tarasov material slated for the same domain). That migration is out of scope for this request but is on the roadmap, so the integration patterns we agree on with jarvis should generalize to course-wiki.

## What forge needs from jarvis

### 1. Architecture repository inventory

A directory listing (depth ≥ 3) of jarvis's architecture repo, formatted to align with forge's structure. Specifically:

- Confirmation that jarvis uses the same top-level layout (`phase-a-architecture-vision`, `phase-b-business-architecture`, `phase-c-information-systems-architecture`, `phase-d-technology-architecture`, `phase-e-opportunities-and-solutions`, `phase-f-migration-planning`, `phase-g-implementation-governance`, `phase-h-architecture-change-management`, `phase-preliminary`, `phase-requirements-management`).
- For each phase that diverges, a note explaining why and a proposed bridge.
- The full ADR index across phases, with each ADR's title and status.
- The list of capabilities, products, and org-units defined under `phase-b-business-architecture/`.

### 2. Service catalog

For each runtime service jarvis operates that forge will consume:

- Internal service name (jarvis-side) and the **public alias** under which it should appear in forge.
- Protocol and interface (HTTP/gRPC/MCP/SSE), full schema or OpenAPI spec.
- Stability level (experimental, beta, stable) and SLO.
- Data classification (public, internal, confidential, restricted).
- Whether the service may produce outputs that reference jarvis-internal identifiers; if so, the sanitization rule we should apply at the boundary.

### 3. Network topology and tenancy

- The subnet/VPC jarvis services live on, and the gateway through which forge will reach them (preferred: a single forge-side reverse proxy that terminates jarvis identity at the boundary).
- DNS plan — internal-only zone for jarvis (e.g. `*.jarvis.internal`) and the forge-side cnames that map to it (e.g. `*.labs.forge.internal`).
- Firewall posture — which forge subnets are permitted, which jarvis services are inbound vs. outbound only, mTLS or VPN requirements.
- Whether GPU resources (Blackwell/5090 class hosts, others) are shared with forge or strictly partitioned.

### 4. Authentication and secrets

- The auth model forge → jarvis (mTLS, OIDC, scoped API keys, signed JWT, other).
- Where forge should source jarvis credentials — preferred: forge's existing secrets store with namespaced keys, never inline in jarvis-named env vars.
- Token rotation cadence and revocation procedure.
- Whether jarvis needs reciprocal credentials into forge; if so, scope.

### 5. Repository and code organization

- Public repo URLs (if any) and the corresponding private repo URLs.
- The submodule, monorepo-subtree, or package-pull mechanism jarvis prefers for forge to depend on jarvis code.
- Branch policy for cross-company changes (who reviews, who merges).
- CI/CD integration: where jarvis builds run, how artifacts are published to forge, and the artifact-name convention that will prevent jarvis-identifying strings from appearing in forge's container labels, image tags, or build logs.

### 6. Lab inventory and integration plan

forge currently exposes its labs at `/mnt/steam/forge/labs/{lab-name}` with corresponding architecture entries under `phase-c-information-systems-architecture/application-architecture/{lab-name}/`. We need:

- jarvis's full lab inventory.
- For each lab: proposed forge-side mount path (e.g. `/mnt/steam/forge/labs/{public-alias}`), proposed forge-side architecture path, and the public alias to use.
- Confirmation that lab outputs do not embed jarvis-internal paths in their on-disk artifacts; if they do, the rewriting rule we should apply when mirroring into forge.

### 7. Branding, aliasing, and identifier hygiene

- The naming convention jarvis services will use externally. Proposal: every jarvis-originated artifact that forge re-exports gets a forge-prefixed alias, and the jarvis name appears nowhere in forge-public surfaces.
- A canonical aliasing table (jarvis-internal name → forge-public alias) for all services, models, datasets, and labs we'll integrate.
- Sanitization rules for log lines, error messages, stack traces, model output fields, and API response headers — anywhere a jarvis identifier could leak across the boundary.

### 8. Governance interlock

- Designated jarvis architecture owner who will review forge ADRs that touch the boundary.
- Designated forge owner on the jarvis side (reciprocal).
- Cadence for joint architecture review (proposed: monthly, aligned with forge's `phase-h-architecture-change-management` audit rhythm).
- Postmortem and incident-comms protocol when a boundary failure occurs.

### 9. course-wiki transition note

The future course-wiki spinoff will follow the same daughter-company pattern as jarvis. Anything jarvis proposes here that depends on assumptions specific to "there is exactly one daughter company" should be flagged so we can generalize before course-wiki lands. In particular: aliasing tables, network topology, and the secrets namespace need to be daughter-company-plural from day one.

## Format and timeline

Plain markdown, one document per section is fine. ADR lists and service catalogs as tables. We'd like a first pass within two weeks; the boundary-sensitive items (sections 3, 4, 7) should be in the first batch since they gate everything else.

If any item is not applicable to jarvis as currently scoped, please reply with "n/a" and a one-line reason rather than omitting — that itself is information forge needs to plan around.
