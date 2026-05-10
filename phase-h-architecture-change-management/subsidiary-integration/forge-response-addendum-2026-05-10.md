# Forge response addendum -- Q1 reframed under ADR 0030 -- 2026-05-10

| | |
|---|---|
| From | forge architecture (architect of record) |
| To | jarvis architecture team |
| Re | [forge-response-2026-05-09](forge-response-2026-05-09.md) Q1 (DNS rename schedule) and jarvis [ack ec0f0e0](https://github.com/vasiliy-mikhailov/jarvis/blob/main/phase-h-architecture-change-management/forge-integration/forge-response-acknowledgement-2026-05-09.md) |
| Status | Q1 framing corrected; outstanding forge-side action removed |

## What was wrong

`forge-response-2026-05-09.md` Q1 approved the DNS rename
proposed in jarvis [response-2026-05-09 §3.1-3.2](https://github.com/vasiliy-mikhailov/jarvis/blob/main/phase-h-architecture-change-management/forge-integration/response-2026-05-09.md)
on the grounds that `jarvis-eyes.mikhailov.tech`,
`jarvis-hands.mikhailov.tech`, and `busy-board.mikhailov.tech`
in public DNS were a G3.1b violation that needed fixing.

That framing was inconsistent with [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md),
which the same forge-response document also accepted.
ADR 0030 says a name (URL, hostname, identifier) is
permitted on a public surface *if and only if* the auth
gate behind it protects the contents. That logic was applied
to git URLs (`git@github.com:vasiliy-mikhailov/jarvis.git`
explicitly permitted on forge-public) but not symmetrically
to DNS records (`jarvis-eyes.mikhailov.tech` treated as a
leak to fix).

A DNS record and a git URL are equivalent under ADR 0030's
threat model:

| Surface | What it reveals | What auth protects |
|---|---|---|
| Git URL on forge-public | "a private repo with this name exists at github" | the contents of the repo (clone fails without auth) |
| DNS A record in public zone | "a hostname with this name exists at this IP" | what's served at the hostname (connection / TLS / SSH key fails without auth) |

Both reveal the bare *name*. Both bounce off auth for the
*contents*. Treating one as permitted and the other as a
leak was the false-positive class ADR 0030 was written to
eliminate.

## Corrected position

Under ADR 0030, the three jarvis-identifying public DNS
records are **permitted** provided every service that
listens on those hostnames is auth-gated. SSH on port 22
on each host already requires a key (per ADR 0003 and
jarvis ssh_config) -- that's auth-gated by definition. The
remaining check is the perception HTTP endpoint on Eyes
and any other listener: each must require auth before
serving content. If that's true (probably is; worth a
five-minute verification), the public DNS records do not
violate G3.1a/b.

Likewise the proposed rename `inference.mikhailov.tech` ->
`forge.mikhailov.tech` was driven by the same pre-ADR-0030
"single public ingress" framing. Under ADR 0030 that
collapse is unnecessary: `inference` is a legitimate Phase
D technology-layer service name; the auth gate (Bearer
token) protects what's behind it. Forge does not rename
`inference.mikhailov.tech`. The Phase D service keeps its
Phase D name.

## What this changes

| Item | Previous (forge-response-2026-05-09 Q1) | Corrected |
|---|---|---|
| Forge registrar change to remove `jarvis-eyes`, `jarvis-hands`, `busy-board` from public zone | required, urgent | not required by ADR 0030; optional operational cleanup at jarvis's discretion |
| Forge registrar change to add `forge.mikhailov.tech` superseding `inference.mikhailov.tech` | required | rejected -- `inference.mikhailov.tech` is the correct Phase D name |
| Jarvis ssh_config / bootstrap rename to `*.internal` (already pushed in [ec0f0e0](https://github.com/vasiliy-mikhailov/jarvis/commit/ec0f0e0)) | proceeded | jarvis's call -- can stand as operational hygiene (LAN-internal name resolution off public registrar, cleaner two-zone topology) or revert to public FQDNs; either is consistent with ADR 0030 |
| Auth posture verification on every service listening on the three jarvis-identifying FQDNs | implicit | explicit follow-up: confirm every endpoint requires auth (SSH already does; HTTP services on Eyes need confirmation) |

## Forge-side action update

Cancelled (per this addendum):
- Registrar change to remove `jarvis-eyes`, `jarvis-hands`, `busy-board` from public zone.
- Registrar change to rename `inference.mikhailov.tech` -> `forge.mikhailov.tech`.

Added (per this addendum):
- Auth posture verification: confirm every service listening on `jarvis-eyes.mikhailov.tech`, `jarvis-hands.mikhailov.tech`, `busy-board.mikhailov.tech` requires auth. Owned by jarvis, reportable in next monthly audit cycle.

Unchanged from forge-response-2026-05-09:
- `phase-b-business-architecture/subsidiaries/omega.md` (landed in [`67aab00`](https://github.com/vasiliy-mikhailov/forge/commit/67aab00)).
- `phase-h-architecture-change-management/subsidiary-audits/` directory (landed in [`67aab00`](https://github.com/vasiliy-mikhailov/forge/commit/67aab00)).
- Token rotation as Phase D follow-up (Q4) and lab-mutex coordinator (Q5) -- still on roadmap.

## Jarvis-side ask

Confirm whether to:

1. Keep the `*.internal` rename in `ec0f0e0` as operational
   hygiene (no public DNS dependency for LAN-internal
   service-to-service resolution; cleaner topology). The
   public DNS records would be torn down because they are
   no longer used by anything, not because they leak.
2. Revert to public FQDNs since ADR 0030 permits them and
   reverting saves a maintenance moving part.

Either is consistent with ADR 0030; the choice is jarvis's
operational preference. Forge does not have a stake unless
the public records cost forge anything (they don't --
registrar fees are flat, DNS query traffic is negligible).

## Related

- [forge-response-2026-05-09](forge-response-2026-05-09.md) -- the document this addendum corrects.
- [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md) -- the principle that drove the correction.
- [jarvis ack ec0f0e0](https://github.com/vasiliy-mikhailov/jarvis/blob/main/phase-h-architecture-change-management/forge-integration/forge-response-acknowledgement-2026-05-09.md) -- jarvis's prior ack assumed Q1 framing as written; the rename in `ec0f0e0` may stand or be reverted per the ask above.

-- forge architecture (architect of record), 2026-05-10
