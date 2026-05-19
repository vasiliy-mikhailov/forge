---
name: cats-review
description: |
  Audit a CATS-style lab for drift between its stance and its
  artifacts (SPEC.md, SOLUTION-ARCHITECTURE.md, tests, code).
  Produce a gap report + a step-by-step remediation plan.

  Invoke when the user asks to "review the architecture", "audit
  drift", "do a CATS review", or after a non-trivial refactor.
---

# cats-review

A CATS review is **not** a checklist. It is the agent reading the
stance and the artifacts, finding where they disagree, and writing
the next cycles that close the gaps.

## Step 1 — Stance

The four ground rules every artifact in a CATS lab obeys. Repeat
them out loud (in your reasoning, before reading anything else):

### Twain (master rule)

> Writing is easy. All you have to do is cross out the excessive
> words. — Mark Twain

Every other writing rule derives from it. Cognitive load is the
bottleneck on doing good work; excess words are the largest
controllable source.

- **Code comments**: keep the "what" (intent faster than re-reading
  the code). Strip "why" — it lives in the spec, the ADR, or
  `SOLUTION-ARCHITECTURE.md`. Strip cycle archaeology
  ("Cycle 47: …") — that lives in git.
- **Specs**: one decision per spec. No "out of scope" sections, no
  anticipatory enumeration, no "previously X but cycle N changed
  it" preambles. Specs describe the current decision; git holds
  the chronology.
- **Architecture docs / ADRs**: current state only. When a decision
  changes, edit the doc — don't append an amendment header.
- **Commit messages**: as long as needed to capture the why, no
  longer.

### Senior Erlang AI Engineer

Pure functions over stateful processes. Immutability (binaries,
tuples, records) over mutation. Composition over inheritance.
Small, focused functions with explicit inputs and outputs. Side
effects sit at the edges (`gen_server`s); the core is pure.

### Constraints are tests, not prose

Express invariants and contracts as TDD-style unit tests,
meta-tests (architecture-shape checks), or live integration tests.
Markdown `test_spec` / `src_spec` ceremony is dead. Erlang
`-spec` attributes carry type contracts, EUnit pins behavior,
Common Test pins integration. **The doc explains *why*; the tests
prove *what*.**

### Prefer fitness functions: constraints → search → verification → repair → repeat

Define what success looks like *as a check* before you start;
iterate against the check; verify on each pass; repair when the
check regresses. Live-runtime tests are fitness functions against
the real environment.

## Step 2 — Read the artifacts (in this order)

The order matters: each later artifact is judged against the
earlier ones.

1. **`SPEC.md`** — what the lab promises (the contract).
2. **`SOLUTION-ARCHITECTURE.md`** — how the lab keeps that promise
   (the target architecture, §1-§N invariants, role decomposition).
3. **`test/`** and any sibling fitness-function folder, plus the
   `make eunit` / `make ct` targets — what is actually proven.
4. **`src/`** — what is actually built.

Don't review by name; open every file and read it. The point is
to develop an opinion based on what's there, not on what should
be there.

## Step 3 — Find gaps between the stance and the artifacts

For each pair (stance dimension, artifact), ask: **is the artifact
consistent with the stance?** If not, name the drift.

The dimensions:

| stance dimension | what drift looks like |
|---|---|
| Twain | amendment headers; cycle archaeology in comments / specs / commit subjects; "out of scope" sections; anticipatory enumeration; rule-change preambles; >1 sentence of "why" in a file that has a spec or ADR |
| Senior Erlang AI Engineer | mutation hidden in records or process state when pure functions would do; side effects scattered through the core instead of corralled in a `gen_server` boundary; OO-flavoured composition; functions without explicit `-spec`; functions that take a process and a state instead of just values |
| Constraints are tests | invariants stated in prose with no test pinning them; `test_spec` / `src_spec` markdown files still present; promises in SPEC / SOLUTION-ARCHITECTURE not covered by `make eunit` or `make ct`; tests written as scripts instead of EUnit / Common Test suites; missing `-spec` on exported functions |
| Fitness functions | "we should never X" claims with no automated check; quality floors that exist only in someone's head; live-runtime regressions caught by manual eyeballing rather than a live test |

Cross-product the dimensions × artifacts. Output one row per pair
in the gap table, ✓ or ✗ per cell. Each ✗ gets a drift detail
section below.

## Step 4 — Step-by-step plan to make it consistent

For every ✗, write a remediation cycle. **Order by leverage**:
the gap whose closure most clarifies the others goes first.

Each cycle entry:

```
Cycle N: <imperative action — what you do, not what you achieve>
  Stance dimension: <Twain | Senior Erlang | Constraints are tests | Fitness functions>
  Artifact touched: <file path(s)>
  Verification: <how cats-review knows the gap is gone>
```

The plan ends when re-running cats-review would print all-green.

## Output template

```
## CATS Architecture Review — <project> — <YYYY-MM-DD>

### Step 1 — Stance recited
Twain · Senior Erlang AI Engineer · Constraints are tests · Fitness functions

### Step 2 — Artifacts read
- SPEC.md                  (<N> lines, last touched <date>)
- SOLUTION-ARCHITECTURE.md (<N> lines, last touched <date>)
- test/, fitness-functions/ (<count> files, `make eunit` -> <N> tests)
- src/                      (<count> .erl files, `make compile` -> <ok|warnings|errors>)

### Step 3 — Gaps

| dimension \ artifact | SPEC | SA  | tests | src |
|---                   |---   |---  |---    |--- |
| Twain                | ✓/✗ | ✓/✗ | ✓/✗  | ✓/✗ |
| Senior Erlang        | …    | …   | …    | …   |
| Constraints are tests| …    | …   | …    | …   |
| Fitness functions    | …    | …   | …    | …   |

### Drift details (one per ✗)

#### <dimension> in <artifact>
- <line range / file:lineno>: <evidence>
- Why this violates <dimension>: <one sentence>

### Step 4 — Plan

Cycle N+1: <action>
  Stance dimension: <one>
  Artifact touched: <path>
  Verification: <check>

Cycle N+2: …

```

## Anti-patterns

- **Don't** invent dimensions. The four listed in Step 1 are the
  whole stance — extending it dilutes it.
- **Don't** judge a file by name. Open it.
- **Don't** propose cycles whose verification is "looks good now".
  Every cycle in the plan must end with an automated check or with
  re-running cats-review and seeing the row flip to ✓.
- **Don't** output a verdict-without-evidence. Every ✗ must cite
  the file + line(s) that prove it.
