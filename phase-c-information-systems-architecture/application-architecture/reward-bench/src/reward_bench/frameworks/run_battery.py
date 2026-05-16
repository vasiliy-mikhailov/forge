"""Cycle 94: implement `make reward-battery` for real.

Reads wiki-compiler/configs/models.yml, filters out entries with
bench_skip=True (and optionally narrows by a regex on `id`), then
invokes `make reward-bench MODEL=<id> TIER=<n> TASK=<task>` for each.

Per SPEC.md §Make targets:
  > make reward-battery TIER=<N> [--filter <regex>]
  >     Iterate over every model in wiki-compiler/configs/models.yml with
  >     bench_tier ≠ skip; run one attempt at the given TIER for each.

The schema has `bench_skip: bool` (separate from `bench_tier: A|B|C|D`).
We honor `bench_skip != True` as the inclusion rule (SPEC text predates
the schema split; behavior is unchanged).

Cycle 78 ran the same sweep manually via 22 per-model CATS tasks; this
script is the codified version of that.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable


# Default registry path. Resolved relative to the forge root so this
# script keeps working if the repo is checked out under a different
# layout. Override via --models for tests.
_DEFAULT_REGISTRY = Path(
    "/home/vmihaylov/forge/phase-c-information-systems-architecture/"
    "application-architecture/wiki-compiler/configs/models.yml"
)


def load_models(path: Path | str) -> list[dict]:
    """Return the `models:` list from a YAML registry."""
    import yaml  # lazy: only Makefile path requires PyYAML
    with open(path) as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict) or "models" not in doc:
        raise ValueError(f"models.yml at {path} missing top-level `models:` key")
    return list(doc["models"])


def select_battery(
    models: Iterable[dict],
    filter_regex: str | None = None,
) -> list[dict]:
    """Filter models per the SPEC.md §Make targets rule.

    - Drop entries with `bench_skip: true`.
    - If `filter_regex` is given, keep only entries whose `id` matches.

    Preserves registry order — the operator decides priority via
    models.yml layout (cycle 78 used the registry order verbatim).
    """
    out: list[dict] = []
    pat = re.compile(filter_regex) if filter_regex else None
    for m in models:
        if m.get("bench_skip", False):
            continue
        mid = str(m.get("id", ""))
        if pat is not None and not pat.search(mid):
            continue
        out.append(m)
    return out


def run_battery(
    tier: int,
    task: str = "2048",
    filter_regex: str | None = None,
    registry_path: Path | str = _DEFAULT_REGISTRY,
    runner: callable = None,
) -> list[tuple[str, int]]:
    """Execute the battery. Returns list of (model_id, returncode) tuples.

    `runner` is an injection point for tests — defaults to spawning
    `make reward-bench MODEL=<id> TIER=<tier> TASK=<task>` via subprocess.
    """
    models = load_models(registry_path)
    picks = select_battery(models, filter_regex=filter_regex)
    print(f"[reward-battery] tier={tier} task={task} "
          f"filter={filter_regex!r} -> {len(picks)} model(s) of {len(models)}",
          flush=True)
    for i, m in enumerate(picks, 1):
        print(f"  [{i}/{len(picks)}] {m['id']}", flush=True)

    if runner is None:
        def runner(model_id: str) -> int:
            cmd = [
                "make", "reward-bench",
                f"MODEL={model_id}",
                f"TIER={tier}",
                f"TASK={task}",
            ]
            print(f"[reward-battery] $ {' '.join(cmd)}", flush=True)
            return subprocess.run(cmd).returncode

    results: list[tuple[str, int]] = []
    for m in picks:
        rc = runner(str(m["id"]))
        results.append((str(m["id"]), rc))
        if rc != 0:
            print(f"[reward-battery] {m['id']} exited rc={rc} (continuing)",
                  flush=True)

    n_ok = sum(1 for _, rc in results if rc == 0)
    n_fail = len(results) - n_ok
    print(f"\n[reward-battery] done: {n_ok} ok / {n_fail} failed "
          f"of {len(picks)} attempted.", flush=True)
    return results


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="reward-battery",
        description="Iterate `make reward-bench` across the model registry.",
    )
    p.add_argument("--tier", type=int, required=True,
                   help="Reward-bench tier (1-4).")
    p.add_argument("--task", default="2048",
                   help="Task id (default: 2048).")
    p.add_argument("--filter", default=None,
                   help="Optional regex on model id.")
    p.add_argument("--models", default=str(_DEFAULT_REGISTRY),
                   help="Path to models.yml (default: wiki-compiler registry).")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    results = run_battery(
        tier=args.tier,
        task=args.task,
        filter_regex=args.filter,
        registry_path=args.models,
    )
    # Return non-zero if any model failed — useful for CI gating.
    return 0 if all(rc == 0 for _, rc in results) else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())



# ============================================================
# Cycle 102: resumable canonical bench
# ============================================================

_CANONICAL_DATE_STAMP = None  # set lazily; YYYY-MM-DD at startup time.


def _today_stamp() -> str:
    """YYYY-MM-DD for the artifact filename. Module-scoped so a
    single sweep keeps the same date even if it crosses midnight."""
    global _CANONICAL_DATE_STAMP
    if _CANONICAL_DATE_STAMP is None:
        from datetime import date
        _CANONICAL_DATE_STAMP = date.today().isoformat()
    return _CANONICAL_DATE_STAMP


def canonical_artifact_path(model_id: str, trial: int,
                            experiments_root: Path | str | None = None) -> Path:
    """Per-(model, trial) artifact path. Existence = (model, trial) done."""
    root = Path(experiments_root) if experiments_root is not None else (
        Path("/home/vmihaylov/forge/phase-c-information-systems-architecture/"
             "application-architecture/reward-bench/experiments")
    )
    return root / f"{_today_stamp()}-bench-{model_id}-trial{trial}.json"


def run_canonical_battery(
    n_trials: int = 10,
    max_iters: int = 500,
    temperature: float = 0.7,
    canonical_hard_wall_sec: float = 300.0,
    seeds: list[int] | None = None,
    registry_path: Path | str | None = None,
    filter_regex: str | None = None,
    experiments_root: Path | str | None = None,
    runner: callable = None,
) -> list[dict]:
    """ADR 0003 canonical campaign: 500 iters × 10 trials × T=0.7
    across every model in MODEL_REGISTRY (filtered by `bench_skip`).

    Resumable: on each (model, trial) the driver checks for an existing
    artifact; if present, skips. Ctrl-C halts in-flight without losing
    completed (model, trial) artifacts.

    Returns the list of artifact dicts (one per completed trial,
    including ones skipped because they already existed).
    """
    import json
    from datetime import date
    from dataclasses import asdict

    if registry_path is None:
        registry_path = _DEFAULT_REGISTRY
    if seeds is None:
        seeds = list(range(1000, 1020))

    models = load_models(registry_path)
    picks = select_battery(models, filter_regex=filter_regex)

    if not picks:
        print("[canonical-battery] no models matched; nothing to do.", flush=True)
        return []

    # Default runner: run main() with the canonical config.
    if runner is None:
        from src.reward_bench.entities.bench_config import BenchConfig
        from src.reward_bench.frameworks.main import main as _bench_main

        def runner(model_id: str, trial: int) -> dict:
            config = BenchConfig(
                max_iters=max_iters,
                n_trials=1,
                temperature=temperature,
                hard_wall_sec=canonical_hard_wall_sec,  # cycle 104 / ADR 0015
            )
            result = _bench_main(model_id=model_id, seeds=seeds,
                                 config=config)
            # AttemptResult -> json-friendly dict.
            return {
                "model_id": model_id,
                "trial": trial,
                "config": {
                    "max_iters": max_iters, "n_trials_total": n_trials,
                    "temperature": temperature, "seeds": list(seeds),
                },
                "mean_score": float(result.mean_score),
                "median_score": float(result.median_score),
                "std_score": float(result.std_score),
                "max_max_tile": int(result.max_max_tile),
                "n_games": int(result.n_games),
                "aggregate_walltime_sec": float(result.aggregate_walltime_sec),
                "best_dev_mean": (None if result.best_dev_mean is None
                                  else float(result.best_dev_mean)),
                "games": [
                    {"seed": int(g.seed), "score": int(g.score),
                     "max_tile": int(g.max_tile), "moves": int(g.moves),
                     "final_state": str(g.final_state),
                     "walltime_sec": float(g.walltime_sec)}
                    for g in result.games
                ],
            }

    out: list[dict] = []
    total = len(picks) * n_trials
    done = 0
    started = date.today().isoformat()
    print(f"[canonical-battery] start {started} | "
          f"{len(picks)} model(s) × {n_trials} trial(s) = {total} runs",
          flush=True)

    for mi, model in enumerate(picks, 1):
        mid = str(model["id"])
        for trial in range(n_trials):
            artifact = canonical_artifact_path(mid, trial,
                                               experiments_root=experiments_root)
            if artifact.exists():
                done += 1
                print(f"  [{done}/{total}] {mid} trial {trial}  SKIP (already done)",
                      flush=True)
                try:
                    out.append(json.loads(artifact.read_text()))
                except Exception:
                    pass
                continue

            print(f"  [{done + 1}/{total}] {mid} trial {trial}  RUN ...",
                  flush=True)
            try:
                payload = runner(mid, trial)
            except KeyboardInterrupt:
                print(f"  [{done + 1}/{total}] {mid} trial {trial}  "
                      f"INTERRUPTED — artifact NOT written; re-run to resume",
                      flush=True)
                raise

            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(json.dumps(payload, indent=2))
            done += 1
            print(f"  [{done}/{total}] {mid} trial {trial}  "
                  f"DONE mean={payload.get('mean_score', '?'):.1f} "
                  f"n_games={payload.get('n_games', '?')}",
                  flush=True)
            out.append(payload)

    print(f"[canonical-battery] complete {date.today().isoformat()} | "
          f"{done}/{total} runs accounted for",
          flush=True)
    return out
