"""Multi-model smoke bench per ADR 0009. Cycle 72.

Each parameter is one ModelTarget from MODEL_REGISTRY. The test
swaps the vLLM container to that model, runs main() with the
SMOKE_CONFIG, writes an artifact, and asserts canonical mean > 0.

Opt-in via `pytest -m smoke`. Sequential by design — only one
vLLM container at a time on the lab GPU.
"""
import json
import os
from dataclasses import asdict
from pathlib import Path

import pytest

from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.frameworks.main import main
from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY
from src.tier1.inference import ensure_serving_model


REPO = Path(__file__).resolve().parents[4]

SMOKE_CONFIG = BenchConfig(
    max_iters=10,
    n_trials=1,
    temperature=0.7,
    finish_floor=0.0,
    hard_wall_sec=60.0,
    supervisor_every_k=0,
)


def _artifact_path(model_id: str) -> Path:
    return REPO / "experiments" / f"2026-05-14-smoke-{model_id}.json"


@pytest.mark.smoke
@pytest.mark.parametrize("target", MODEL_REGISTRY, ids=lambda t: t.id)
def test_when_smoke_bench_runs_on_model_then_canonical_mean_above_zero(target):
    """ADR 0009 smoke screen for one model in MODEL_REGISTRY."""
    artifact = _artifact_path(target.id)
    artifact.parent.mkdir(parents=True, exist_ok=True)

    # Container swap. This is a slow operation (model download +
    # vLLM compile) the first time. Subsequent runs against the
    # same model are fast.
    ensure_serving_model(target)

    # Run smoke campaign — 1 trial, max_iters=10.
    try:
        result = main(model_id=target.id, config=SMOKE_CONFIG)
    except Exception as e:
        # ADR 0002 sentinel pattern: container-level failures
        # become structured artifact entries, not pytest errors,
        # so the sweep can continue.
        payload = {
            "model_id": target.id,
            "config": asdict(SMOKE_CONFIG),
            "error": f"{type(e).__name__}: {e}",
            "mean_score": None,
            "smoke_passed": False,
        }
        artifact.write_text(json.dumps(payload, indent=2))
        pytest.fail(f"smoke main() raised: {type(e).__name__}: {e}")

    payload = {
        "model_id": target.id,
        "config": asdict(SMOKE_CONFIG),
        "mean_score": result.mean_score,
        "median_score": result.median_score,
        "max_max_tile": result.max_max_tile,
        "n_games": result.n_games,
        "aggregate_walltime_sec": result.aggregate_walltime_sec,
        "solver_protocol_valid": result.solver_protocol_valid,
        "smoke_passed": result.mean_score > 0,
    }
    artifact.write_text(json.dumps(payload, indent=2))

    # ADR 0009 contract: smoke-pass = mean_score > 0.
    assert result.mean_score > 0, (
        f"{target.id} smoke FAIL: mean_score={result.mean_score} "
        f"max_tile={result.max_max_tile} "
        f"protocol_valid={result.solver_protocol_valid} "
        f"walltime={result.aggregate_walltime_sec:.1f}s"
    )
