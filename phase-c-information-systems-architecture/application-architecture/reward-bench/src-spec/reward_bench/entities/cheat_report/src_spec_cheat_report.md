# `src/reward_bench/entities/cheat_report.py`
`CheatReport` is a frozen dataclass — the per-attempt anti-cheat
verdict envelope. Mirrors the pydantic schema in
[`SPEC.md`](../../../../SPEC.md#schemas-pydantic-v2).
## Fields
| Field | Type | Meaning |
| ---------------------- | -------------------- | ----------------------------------------------------------- |
| `findings` | `tuple[CheatFinding,...]` | All AST + bandit findings. |
| `network_policy` | `NetworkPolicy` | `'none'` (tier 1) or `'vllm_only'` (tier 2-4). |
| `replay_score_match` | `bool | None` | Stage-2 vs Stage-3 score equality within tolerance. |
| `replay_tolerance_pct` | `float` | Replay tolerance for this attempt's tier (0/5/5/10 from TIER_REGISTRY). |
| `verdict` | `Verdict` | `'clean'`, `'warning'`, or `'rejected'`. |
| `rejected_reason` | `str | None` | One-line cause when `verdict='rejected'`. |
## Type aliases
 NetworkPolicy = Literal['none', 'vllm_only']
 Verdict = Literal['clean', 'warning', 'rejected']
## Properties
Frozen, no methods. Pure data.
