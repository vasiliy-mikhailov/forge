---
name: cats-review
description: |
  CATS-style architecture review of a project against the invariants
  declared in its SOLUTION-ARCHITECTURE.md. Invoke when the user
  asks to "review the architecture", "audit drift", "do a CATS
  review", or after a non-trivial refactor.
---

# cats-review

CATS methodology says **constraints are tests, not prose**. Most
constraints (per-module behavior) belong in EUnit / Common Test.
Some — cross-cutting invariants that span the codebase — are best
checked by an agent with judgment: regex catches 90 % but trips on
edge cases (variable dispatch, comments, string content), and the
fix is usually "look at the AST" or "use xref" rather than a
tighter pattern. That's this skill.

## When to invoke

- User asks to "review the architecture" / "do a CATS review" /
  "audit for drift".
- After a refactor that crossed module boundaries.
- Before merging a feature branch that touched the supervision
  tree, behaviours, or §5-style invariants ("no file APIs", "no
  spawn outside the Runner", etc.).

## Process

1. Read `SOLUTION-ARCHITECTURE.md` (or the project's equivalent
   target-architecture doc).
2. For each invariant claim in §1-§N, pick a check method and
   verify it.
3. Produce the review report (format below).

When the project has the seven canonical Erlang invariants below,
run all seven. Otherwise, extract the project-specific invariants
from the doc and verify them with the same machinery.

## The seven canonical Erlang checks

Each check below has: **what § promises**, **what to verify**, and
**how** (preferred method first, fallback in parens). When the
preferred method isn't available, note that in the report.

### 1. Behaviour conformance

- **What §2 promises**: production impls declare the behaviour they
  satisfy (e.g. `beam_canonical_scorer` implements
  `canonical_scorer`).
- **Verify**: every behaviour-declaring module has ≥1 module with
  matching `-behaviour(BehaviourName)` attribute.
- **How**: at the Erlang shell or via an escript,
  `Mod:module_info(attributes)` returns `[{behaviour, [...]}]`.
  Reflection — robust.

### 2. No file APIs above the Runner

- **What §5 promises**: bench-side code communicates only in
  binaries / scalars / records. The only `file:*` calls live
  inside the Runner adapter (or, in the Erlang bench, a one-time
  startup read in the CLI entry).
- **Verify**: no `file:`-namespaced calls in `src/*.erl` outside
  an allow-list.
- **How**:
  - **Preferred**: `xref:start/1` + `xref:add_directory` over
    `_build/default/lib/<app>/ebin`, then
    `xref:q(s, "(XC | (Mod) - <allowlisted_mod>) || \"file\" : Mod")`.
    Semantic — catches variable dispatch (`M = file, M:read_file(P)`).
  - **Fallback**: `re:run` with `\bfile:`. Misses variable dispatch
    and trips on comments/string content. Note the limitation in
    the report.

### 3. No unrestricted spawn

- **What §5 promises**: concurrency is corralled. Solver execution
  spawns one Erlang process per seed inside `beam_canonical_scorer`;
  no other module spawns raw processes. (OTP startup via
  supervisors is fine — that goes through `proc_lib`, not `spawn`.)
- **Verify**: no calls to `erlang:spawn{,_link,_monitor,_opt}/N`
  outside an allow-list.
- **How**:
  - **Preferred**: `xref:q(s, "(XC | (Mod) - <allowlisted_mod>) || \"erlang\" : Mod / (E : Fun where Fun = spawn or Fun = spawn_link ...)")`.
  - **Fallback**: regex `\b(?:erlang:)?spawn(?:_link|_monitor|_opt)?\s*\(`.

### 4. SolutionGenerator uses the fenced-block extractor

- **What §4 promises**: the LLM emits a fenced ` ```erlang ... ``` `
  block; the `extract_fenced_erlang` helper lifts the body. If a
  refactor strips that call, the bench returns garbage.
- **Verify**: `solution_generator` actually CALLS
  `extract_fenced_erlang:extract/1` (not just mentions it).
- **How**:
  - **Preferred**: `xref:q(s, "(XC) || solution_generator")` and
    confirm `extract_fenced_erlang:extract/1` appears in the result.
  - **Fallback**: regex for `extract_fenced_erlang:` (the colon
    enforces a call site, not a bare mention).

### 5. Every record has a user

- **What's promised**: records declared in `records.hrl` are part
  of the architecture; orphans accumulate during refactors.
- **Verify**: every `-record(Name, ...)` declaration in
  `records.hrl` (or wherever shared records live) has ≥ 1 reference
  somewhere in `src/*.erl` (excluding the declaration itself).
- **How**:
  - **Preferred**: parse the .hrl with `epp_dodger:parse_file`,
    extract record names; parse each src/*.erl with
    `erl_syntax:parse_form` + walk for `record_expr` / `record_index`
    / `record_access` nodes whose record name matches.
  - **Fallback**: regex `#RecName[\\{\\.]` (the trailing `{` / `.`
    enforces it's actually a record reference, not a substring of
    another name). Note: `#submission` would NOT match
    `#submission_other` because `_` isn't in the trailing class.

### 6. No Python-era stragglers

- **What's promised**: the Erlang bench replaced the Python one
  wholesale (per the cycle-232 cutover). Stale Python-era strings
  in source or comments are documentation drift, not just cosmetic.
- **Verify**: no occurrences in `src/`, `test/`, `tasks/` of:
  `submission.py`, `class Solver`, `transitions library`,
  `pydantic`, `OpenHands`, `condenser`, `ralph`, `agent_loop`.
- **How**: text scan is the right tool — this is a lint, not a
  semantic check. Case-insensitive regex over each prohibited term.
  Note any matches with file + line + the surrounding context.

### 7. Supervision tree shape — NOTE: this is a unit test, not a fitness function

- **What was claimed**: `reward_bench_sup` boots clean with the
  expected child count.
- **Verify**: spawn the sup, call `supervisor:which_children/1`,
  count.
- **How**: `{ok, Pid} = reward_bench_sup:start_link(), Children =
  supervisor:which_children(Pid), unlink + exit cleanup`.

**Caveat**: this check is per-module behavior of one specific
supervisor — not a cross-cutting invariant. It belongs in
`test/reward_bench_sup_tests.erl`, not in a CATS review. Surface
this in the report as "wrong category — recommend moving to
unit tests".

## Cross-project applicability

The 7 checks above are the Erlang/reward-bench instances of more
general CATS invariants:

| general | reward-bench instance |
|---|---|
| Behaviour conformance / interface impl | Erlang `-behaviour` |
| Side-effect scope (file IO above the Runner) | `file:` |
| Concurrency scope (no rogue spawns) | `spawn` |
| Wiring sanity (boundary helper actually called) | `extract_fenced_erlang` |
| No dead types / records | records.hrl |
| No old-stack stragglers | Python lexicon |
| Supervision tree shape | reward_bench_sup |

When invoked on a different project, derive the project-specific
instance of each general invariant by reading its
`SOLUTION-ARCHITECTURE.md`.

## Output format

```
## CATS Architecture Review — <project> — <date>

Target architecture doc: <path>
Build artifacts inspected: <path-to-ebin>

### Invariants checked

| § | invariant | method | status |
|---|---|---|---|
| §2 | behaviour conformance | reflection | ✓ |
| §5 | no file APIs above Runner | xref | ✓ |
| §5 | no unrestricted spawn | xref | ✗ DRIFT |
| §4 | fenced extractor wired | xref | ✓ |
| —  | every record has a user | AST | ✓ |
| —  | no Python-era stragglers | regex | ✓ |
| —  | sup shape (NOT a fitness function — see report) | runtime | n/a |

### Drift details

#### §5 no unrestricted spawn
   What §5 promises: "Solver execution spawns one Erlang process
   per seed inside beam_canonical_scorer; no other module spawns
   raw processes."
   What I found: src/foo.erl:42 calls erlang:spawn_link/2.
   Suggested fix: route through canonical_scorer or remove.

### Coverage gaps

Architectural claims in §X that I could not mechanically verify:
- "context flows through ... without mutation drift" (semantic claim
  needs a property test or a runtime probe)
- ...

### Methodology notes per check

- §5 file IO: used xref (semantic). xref returns 0 calls to
  `file:*` from src/ modules other than `bench_main`, which
  reads SKILL_tier1.md at startup as the doc allows.

- §5 spawn: used xref. Found 1 call: src/foo.erl:42
  → `erlang:spawn_link/2`. See drift detail above.

- ... (one note per check)
```

## Anti-patterns

- **Don't** shell out to grep when xref / AST is reachable. The
  cost of a semantic check is a few seconds of compile + load;
  the cost of regex false-positive/negative is a missed drift.
- **Don't** pin per-module behavior here. If a check would die
  with one specific module's deletion, it's a unit test — say
  so in the report and recommend the move.
- **Don't** report green without naming the method. "passed via
  regex" and "passed via xref" carry very different epistemic
  weight; the reader needs to know which.
