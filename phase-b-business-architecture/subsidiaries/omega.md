# omega -- subsidiary

| | |
|---|---|
| Subsidiary | jarvis |
| Repo (private, auth-gated) | `git@github.com:vasiliy-mikhailov/jarvis.git` |
| Category | private operational tenant |
| Architect of record | shared with forge (single architect) |

URL above is permitted on forge-public per [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md).
Operational details (capabilities, products, services, labs,
quality numbers, host names, model names) live inside the
auth-gated repo per ADR 0030 §2 and the daughter's own
G3.1b-equivalent strict-privacy regime.

## What lives where

- Capabilities, products, org-units: in jarvis at
  `phase-b-business-architecture/` (auth-gated).
- Lab participation in forge mutex: forge schedules per
  `phase-g-implementation-governance/policies/`; jarvis
  labs participate as named tenants when they consume
  `inference-mode`.
- Audit reports about jarvis: forge writes them at
  `../../phase-h-architecture-change-management/subsidiary-audits/omega-YYYY-MM-DD.md`,
  with operational identifiers aliased per ADR 0030.

## Integration history

- 2026-05-08: forge integration request -- see
  `../../phase-h-architecture-change-management/subsidiary-integration/request-to-jarvis-2026-05-08.md`.
- 2026-05-09: jarvis response, forge response, jarvis
  acknowledgement -- thread closed. See
  `../../phase-h-architecture-change-management/subsidiary-integration/forge-response-2026-05-09.md`.
- 2026-05-09: ADR 0030 (subsidiary URL visibility) lands.

## Related

- [ADR 0018](../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md) -- content-side privacy boundary (stacks with ADR 0030).
- [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md) -- name-side privacy boundary; this file is permitted by ADR 0030.
