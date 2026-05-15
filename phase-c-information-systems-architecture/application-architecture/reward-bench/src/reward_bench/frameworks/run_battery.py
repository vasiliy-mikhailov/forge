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
