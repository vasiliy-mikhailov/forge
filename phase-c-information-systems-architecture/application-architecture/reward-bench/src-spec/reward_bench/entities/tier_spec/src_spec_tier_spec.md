# `src/reward_bench/entities/tier_spec.py`
`TierSpec` is a frozen dataclass that captures one row of the 4-tier
ladder described in [`SPEC.md`](../../../../SPEC.md#tier-specifications).
## Fields
| Field | Type | Meaning |
| ---------------------- | --------------- | ------------------------------------------------------ |
| `tier` | `int` | 1..4. Matches `meta.json: tier`. |
| `image` | `str` | Docker image (with `${VERSION}` placeholder). |
| `network_policy` | `NetworkPolicy` | `none` (tier 1) or `vllm_only` (tier 2-4). |
| `submission_shape` | `str` | One-line description of the submission interface. |
| `reward_n` | `int` | Games scored per attempt (20 for tier 1, 10 for 2-4). |
| `replay_tolerance_pct` | `float` | Allowed drift on replay (0% / 5% / 5% / 10%). |
## `NetworkPolicy`
A `Literal['none', 'vllm_only']` matching SPEC.md's two egress modes.
## Properties
- Frozen, no methods. Pure data.
- No validation in the entity itself.
