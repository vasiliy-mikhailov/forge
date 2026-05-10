# Subsidiary audits

Audit reports about forge's daughter companies. Per
[ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md):

- Filename pattern: `<greek-letter>-YYYY-MM-DD.md`
  (e.g. `omega-2026-05-09.md` for jarvis,
  `psi-2026-08-15.md` when course-wiki spins up).
- Bare daughter URL inside reports is permitted.
- Operational identifiers (host names, service names,
  lab names that name what the daughter does, error
  message fields, log lines, capability quality
  numbers) MUST use the daughter's declared alias table.
- Audit findings cite opaque IDs that resolve to private
  content (`omega lab forge-omega-vdi consumed N
  llm-inference-hours in window X`).

First audit lands in the next monthly audit cycle.

See `../../phase-b-business-architecture/subsidiaries/`
for the daughter catalog.
