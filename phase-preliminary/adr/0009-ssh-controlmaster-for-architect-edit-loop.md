# ADR 0009 — ssh ControlMaster for the architect edit loop

## Status
Accepted (2026-04-28).

## Context

The forge production-framework lives on `mikhailov.tech` (single-server
deployment, Phase A principle). The architect edits source on that box;
the previous failure mode was to mirror code into a workstation
checkout, edit there, push, ssh in, pull. That doubled every change
through git, which is over-machinery for the kind of small focused
edits the production-framework needs (bin scripts, compose flags,
configs/models.yml entries).

The simpler loop is: edit directly on the server via short-lived
`ssh forge "<edit command>"` calls. Each call is independent — no cwd
or env carryover — but each is one round-trip to the prod box.

The hidden cost: each call paid the full TCP + TLS + key-exchange
handshake to `mikhailov.tech:2222`, ~1.5–2.5 s of pure overhead before
any work happened. Measured cold:

| operation                         | cold ssh   |
|-----------------------------------|------------|
| `ssh forge "true"` (no work)      | 1.9–4.4 s  |
| `cat ~/forge/AGENTS.md \| wc -l`  | 2.2 s      |
| `sed -i s/X/Y/ <file>`            | 3.1 s      |
| `git log -1 --oneline`            | 2.6 s      |

A typical "fix one thing, restart container" cycle is ~4–5 ssh calls.
At ~3 s each that is ~15 s of pure handshake per cycle, dwarfing the
work. Across a session of 50–100 such edits — typical for a model
swap + bench + revert — that is 15–25 minutes of architect time spent
re-handshaking. This sits squarely on the **architect-velocity** goal
(Phase A): minutes the architect spends on overhead are minutes not
spent advancing capabilities.

## Decision

Use OpenSSH ControlMaster on the architect workstation to multiplex
all `ssh forge` calls onto one persistent socket, with a
`ControlPersist` window long enough to span a normal editing session.

```
# ~/.ssh/config (architect workstation)
Host forge
  HostName 77.37.246.197
  User vmihaylov
  Port 2222
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  ControlMaster auto
  ControlPath ~/.ssh/cm/%C
  ControlPersist 10m
```

The `~/.ssh/cm/` directory must exist (the socket lives there); the
hashed `%C` path keeps it host- and user-specific so multiple
workstations can share the same `~/.ssh` over the same `Host` block
without colliding.

After this is in place, every additional ssh call within the
ControlPersist window reuses the open TCP+TLS+auth channel and pays
only the small command-execution overhead.

## Measurement (the experiment)

Same operations re-timed after enabling ControlMaster, primed by one
warmup call:

| operation                 | warm ssh    | speedup |
|---------------------------|-------------|---------|
| `ssh forge "true"`        | 0.28–0.85 s | 4–7×    |
| `cat <file> \| wc -l`     | 0.48 s      | 4.6×    |
| `sed -i …`                | 0.35 s      | 8.8×    |
| python multi-step edit    | 0.40 s      | 6.6×    |
| `git log -1 --oneline`    | 0.30 s      | 8.5×    |

Typical edit cycle drops from ~15 s of handshake to ~2 s. On the
G3 Gemma-4-31B startup investigation (this session) the edit-fix-
restart loop completed in ~5 s wall instead of ~12–15 s pre-fix.

## Consequences

- **Positive — directly raises architect-velocity.** Every operation
  that reads or edits production state on the forge box is 4–9× faster.
  The savings compound across multi-step workflows (model swap,
  pilot orchestration, ADR drafting against live state).
- **Positive — no production-side change.** The forge box, sshd
  config, and all keys are unchanged. ControlMaster lives entirely on
  the architect workstation. No new ports, no daemon, no privilege.
- **Positive — falls back gracefully.** If the master socket dies
  (network blip, sshd restart, ControlPersist expiry), the next
  `ssh forge` re-handshakes and re-establishes the master. No manual
  intervention. Worst case is one cold call's latency.
- **Cost — one stale-socket failure mode.** A sshd restart on the
  forge box can leave a stale ControlPath socket that the local ssh
  still tries to use. Symptom: `mux_client_request_session: read
  from master failed: Broken pipe`. Fix is `rm ~/.ssh/cm/*` and retry.
  Rare in practice (mikhailov.tech sshd restarts ≤ once a month).
- **Cost — long-running master keeps an authenticated session open.**
  At 10-minute idle TTL this is bounded; the session ends when the
  workstation goes to sleep or the socket is removed.
- **Architect-velocity dimension this advances.** Capability-advances
  per architect-hour, dimension "overhead per edit". Was: ~3 s per
  edit (cold ssh). Is: ~0.4 s per edit (warm ssh). 7–8× lower
  overhead, applied to every interactive session with the prod box.

## Touched files

- New: `phase-preliminary/adr/0009-ssh-controlmaster-for-architect-edit-loop.md` (this).
- Architect workstation only: `~/.ssh/config` (Host forge stanza adds
  ControlMaster / ControlPath / ControlPersist). Not in repo —
  workstation-local config, mirrored in this ADR for reproducibility.

## Alternatives considered

- **Mirror checkout + push/pull.** Edit on workstation, `git push`,
  ssh in, `git pull`, restart container. Rejected — every micro-edit
  goes through git, which is heavy for one-line config changes; and
  the ssh hop is still needed to restart the container, so we do not
  save a round-trip.
- **Persistent shell session via `ssh -t` + tmux.** Would also avoid
  re-handshakes, but loses per-call isolation (cwd, env, exit codes
  bleed between commands). Less composable from a tooling layer that
  sends one command at a time.
- **Mosh.** Solves the latency problem differently (UDP + state
  reconciliation), but requires a server-side daemon and opens UDP
  ports. Rejected — production-side change is not warranted for a
  workstation latency problem.
- **VS Code Remote-SSH / similar IDE bridges.** Useful for human
  editing but does not help tool-driven (Claude Code / Codex CLI)
  ssh-per-command workflows that this ADR targets.

## Cross-references

- Phase A goal advanced: **architect-velocity** (`AGENTS.md`
  Motivation layer — capability advances per architect-hour).
- Phase G policy this ADR is consistent with: containers-only
  execution. Edits land on host config files (.env, compose,
  load-active-model.sh); production processes still run only inside
  containers.
- Phase F context (the experiment whose tight edit-restart loop
  surfaced the cost): G3 Gemma-4-31B-it bench
  (`phase-f-migration-planning/experiments/G3-gemma-4-31b.md` —
  in flight at time of this ADR).


## Motivation

Per [P7](../architecture-principles.md) — backfit:

- **Driver**: re-establishing SSH per architect command is
  high-latency; ControlMaster amortises the handshake.
- **Goal**: Architect-velocity.
- **Outcome**: DevOps role multiplexes SSH per ADR 0009.
- **Measurement source**: audit-predicate: P3 (architect-edit-loop conformance)
