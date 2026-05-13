"""TIER_REGISTRY: the four bench tiers from SPEC.md.

See src-spec/reward_bench/use_cases/tier_registry/."""
from src.reward_bench.entities.tier_spec import TierSpec


TIER_REGISTRY = (
    TierSpec(
        tier=1,
        image='reward-bench-tier1:${VERSION}',
        network_policy='none',
        submission_shape='class Solver with move(board) -> W|A|S|D (transitions FSM)',
        reward_n=20,
        replay_tolerance_pct=0.0,
    ),
    TierSpec(
        tier=2,
        image='reward-bench-tier2:${VERSION}',
        network_policy='vllm_only',
        submission_shape='def build_graph() -> langgraph.StateGraph (nodes may call llm.invoke)',
        reward_n=10,
        replay_tolerance_pct=5.0,
    ),
    TierSpec(
        tier=3,
        image='reward-bench-tier3:${VERSION}',
        network_policy='vllm_only',
        submission_shape='LangGraph + orchestrator function routing between nodes at runtime',
        reward_n=10,
        replay_tolerance_pct=5.0,
    ),
    TierSpec(
        tier=4,
        image='reward-bench-tier3:${VERSION}',
        network_policy='vllm_only',
        submission_shape='def construct(task_spec) -> Solver (meta-orchestrator builds the FSM)',
        reward_n=10,
        replay_tolerance_pct=10.0,
    ),
)
