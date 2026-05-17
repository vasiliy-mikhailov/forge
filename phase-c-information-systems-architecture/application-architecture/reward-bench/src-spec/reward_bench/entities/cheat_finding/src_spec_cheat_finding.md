# `src/reward_bench/entities/cheat_finding.py`
`CheatFinding` is a frozen dataclass — one row of the anti-cheat
report. Mirrors the pydantic schema in
[`SPEC.md`](../../../../SPEC.md#schemas-pydantic-v2).
## Fields
| Field | Type | Meaning |
| ---------- | ------------ | -------------------------------------------------------- |
| `layer` | `Layer` | `'ast'` or `'bandit'`; which scanner produced the finding.|
| `severity` | `Severity` | `'info'`, `'warning'`, or `'rejected'`. |
| `rule` | `str` | The rule that fired, e.g. `'no_subprocess'`. |
| `line` | `int` | Line number in submission.py where the finding occurred. |
| `code` | `str` | The offending source line text. |
## Type aliases
 Layer = Literal['ast', 'bandit']
 Severity = Literal['info', 'warning', 'rejected']
## Properties
Frozen, no methods. Pure data.
