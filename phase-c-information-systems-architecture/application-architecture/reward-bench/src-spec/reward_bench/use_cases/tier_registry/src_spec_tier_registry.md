# `src/reward_bench/use_cases/tier_registry.py`

`TIER_REGISTRY` is a tuple of four `TierSpec` value objects — the
ladder from [`SPEC.md`](../../../../SPEC.md#tier-specifications).

## Contents

| Tier | Image                          | Network    | Reward N | Replay Tol |
| ---- | ------------------------------ | ---------- | -------- | ---------- |
| 1    | reward-bench-tier1:${VERSION}  | none       | 20       | 0%         |
| 2    | reward-bench-tier2:${VERSION}  | vllm_only  | 10       | 5%         |
| 3    | reward-bench-tier3:${VERSION}  | vllm_only  | 10       | 5%         |
| 4    | reward-bench-tier3:${VERSION}  | vllm_only  | 10       | 10%        |

(Tier 4 reuses the tier-3 image — no new deps.)

## Invariants

- Exactly 4 entries, with `tier` values `1, 2, 3, 4` in order.
- Tier 1 has `network_policy='none'`; tiers 2-4 have `'vllm_only'`.
- Tier 1 has `reward_n=20`; tiers 2-4 have `reward_n=10`.
- Replay tolerance strictly increases (or holds) with tier:
  0, 5, 5, 10.
