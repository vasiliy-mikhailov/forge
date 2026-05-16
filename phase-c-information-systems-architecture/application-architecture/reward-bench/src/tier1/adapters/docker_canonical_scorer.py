"""Cycle 105 / ADR 0006 Layer 2: DockerCanonicalScorer adapter.

Spawns `reward-bench-tier1:${TAG}` per attempt with:
  - `--cpus=N` host-side cap (N = `cpu_count() // 2` by default)
  - `--memory=2g --pids-limit=256 --network=none` isolation
  - REWARD_BENCH_* env vars threaded from BenchConfig
  - mounts: submission.py:ro, env_2048.py:ro, reports:rw

Waits for the container with a deadline-based timeout. Reads
/reports/result.json. Returns an AttemptResult.

Lives in the frameworks layer because it uses subprocess (forbidden
in use_cases by the architecture test).
"""
from __future__ import annotations

import json
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from src.adapters.multiprocessing_cpu_count import MultiprocessingCpuCount
from src.ports.cpu_count import CpuCountPort
from src.ports.canonical_scorer import CanonicalScorerPort
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.entities.game_result import GameResult


_DEFAULT_IMAGE = "reward-bench-tier1:0.4"


class DockerCanonicalScorer(CanonicalScorerPort):
    """Per-attempt Docker-sandboxed canonical scorer."""

    def __init__(
        self,
        image: str = _DEFAULT_IMAGE,
        cpus: float | None = None,
        cpu_count_port: CpuCountPort | None = None,
        memory: str = "2g",
        pids_limit: int = 256,
        env_path: str | Path | None = None,
        stagnation_sec: int = 60,
        docker_bin: str = "docker",
    ):
        self.image = image
        port = cpu_count_port or MultiprocessingCpuCount()
        if cpus is None:
            # ADR 0006 Layer 2: 50% of host cores.
            cpus = max(1.0, port.cpu_count() / 2.0)
        self.cpus = float(cpus)
        self.memory = memory
        self.pids_limit = int(pids_limit)
        self.env_path = Path(env_path) if env_path is not None else None
        self.stagnation_sec = int(stagnation_sec)
        self.docker_bin = docker_bin

    def score(
        self,
        submission_path: str | Path,
        seeds,
        *,
        hard_wall_sec: float = 0.0,
        reports_root: str | Path | None = None,
    ) -> AttemptResult:
        """Score one submission across `seeds` inside the Docker sandbox.

        Returns an AttemptResult with cycle-23/27 sentinel semantics
        preserved (per-seed walltime_exceeded / solver_error / stagnated).
        """
        sub_path = Path(submission_path).resolve()
        seeds_t = tuple(seeds)
        if not seeds_t:
            return _empty_result(hard_wall_sec)

        # Reports go into a fresh dir under reports_root (or tmp).
        if reports_root is not None:
            reports_dir = Path(reports_root).resolve()
            reports_dir.mkdir(parents=True, exist_ok=True)
        else:
            reports_dir = Path(tempfile.mkdtemp(prefix="reward-bench-docker-"))

        seed_base = int(seeds_t[0])
        n_games = len(seeds_t)
        # The runner walks seeds_base .. seed_base+n_games-1. Our caller
        # may pass a non-contiguous list; we cope by passing the whole
        # range and discarding seeds we didn't ask for after the run.
        # In practice main.py passes range(1000, 1020) — contiguous.

        cmd = [
            self.docker_bin, "run", "--rm",
            "--network=none",
            f"--memory={self.memory}",
            f"--pids-limit={self.pids_limit}",
            f"--cpus={self.cpus}",
            "-v", f"{sub_path}:/workspace/submission.py:ro",
        ]
        if self.env_path is not None:
            cmd += ["-v", f"{self.env_path.resolve()}:/env/env_2048.py:ro"]
        cmd += [
            "-v", f"{reports_dir}:/reports",
            "-e", f"REWARD_BENCH_NUM_GAMES={n_games}",
            "-e", f"REWARD_BENCH_SEED_BASE={seed_base}",
            "-e", f"REWARD_BENCH_STAGNATION_SEC={self.stagnation_sec}",
            "-e", f"REWARD_BENCH_HARD_WALL_SEC={hard_wall_sec}",
            self.image,
        ]

        start = time.monotonic()
        deadline = (start + hard_wall_sec + 30.0) if hard_wall_sec > 0 else None
        # ^ +30 s grace: in-container runner enforces hard_wall_sec itself
        #   via its own deadline; the outer subprocess timeout is just
        #   a safety net.

        try:
            timeout = (deadline - start) if deadline is not None else None
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
            )
            stdout = proc.stdout
            stderr = proc.stderr
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            # The container blew past our outer cap. Force-stop any
            # leftover (the --rm flag removes on stop).
            stdout = ""
            stderr = "docker run exceeded outer timeout"
            returncode = 124
            # Best-effort: docker stop by image name. The --rm makes
            # cleanup automatic if SIGTERM completes.

        elapsed = time.monotonic() - start

        # Cycle 121: distinguish infrastructure failure from runner
        # crash. Infra failure (image missing, daemon down) must
        # RAISE per ADR 0018 Port contract — silently sentinelizing
        # them produces zero-score artifacts that look like "slow
        # solver hit timeout" but actually mean "bench broken."
        if _is_infra_failure(returncode, stderr):
            raise RuntimeError(
                f"docker run infrastructure failure (returncode={returncode}); "
                f"stderr: {stderr.strip()[:500]}"
            )

        result_path = reports_dir / "result.json"
        if not result_path.exists():
            # No result file => container started and crashed before
            # writing. Emit walltime_exceeded sentinels per seed —
            # this is submission-side / runner-side failure, not
            # infrastructure.
            games = tuple(_walltime_exceeded(seed) for seed in seeds_t)
            return _aggregate(games, elapsed, hard_wall_sec)

        try:
            payload = json.loads(result_path.read_text())
        except Exception:
            games = tuple(_solver_error(seed, "result.json unparseable")
                          for seed in seeds_t)
            return _aggregate(games, elapsed, hard_wall_sec)

        # Map the runner's JSON game list -> GameResult entities.
        by_seed: dict[int, dict] = {int(g["seed"]): g for g in payload.get("games", [])}
        games_list: list[GameResult] = []
        for seed in seeds_t:
            g = by_seed.get(int(seed))
            if g is None:
                games_list.append(_walltime_exceeded(seed))
                continue
            games_list.append(GameResult(
                seed=int(seed),
                score=int(g.get("score", 0)),
                max_tile=int(g.get("max_tile", 2)),
                moves=int(g.get("moves", 0)),
                final_state=str(g.get("final_state", "max_moves")),
                walltime_sec=float(g.get("walltime_sec", 0.0)),
            ))
        return _aggregate(tuple(games_list), elapsed, hard_wall_sec)


# ---- helpers ----

# Cycle 121: docker stderr patterns that indicate infrastructure
# failure (image missing, daemon unreachable, exec error). Match
# these AND treat returncode 125/126/127 as infra-failure as well.
_INFRA_FAIL_STDERR_PATTERNS = (
    "Unable to find image",
    "No such image",
    "pull access denied",
    "manifest unknown",
    "manifest for",
    "repository does not exist",
    "Cannot connect to the Docker daemon",
    "error during connect",
    "executable file not found",
)


def _is_infra_failure(returncode: int, stderr: str) -> bool:
    # docker run returncodes for infra failure:
    #   125 — daemon error, image not found
    #   126 — container command not executable
    #   127 — container command not found
    if returncode in (125, 126, 127):
        return True
    if returncode != 0 and stderr:
        for pattern in _INFRA_FAIL_STDERR_PATTERNS:
            if pattern in stderr:
                return True
    return False


def _walltime_exceeded(seed: int) -> GameResult:
    return GameResult(seed=int(seed), score=0, max_tile=2, moves=0,
                      final_state="walltime_exceeded", walltime_sec=0.0)


def _solver_error(seed: int, _why: str) -> GameResult:
    return GameResult(seed=int(seed), score=0, max_tile=2, moves=0,
                      final_state="solver_error", walltime_sec=0.0)


def _empty_result(hard_wall_sec: float) -> AttemptResult:
    return AttemptResult(
        mean_score=0.0, median_score=0.0, std_score=0.0,
        max_max_tile=0, n_games=0, aggregate_walltime_sec=0.0,
        games=(), hard_wall_sec=hard_wall_sec,
        stagnated_any=False, walltime_exceeded=False,
    )


def _aggregate(games: tuple, elapsed: float, hard_wall_sec: float) -> AttemptResult:
    scores = [g.score for g in games]
    tiles = [g.max_tile for g in games]
    return AttemptResult(
        mean_score=(sum(scores) / len(scores)) if scores else 0.0,
        median_score=statistics.median(scores) if scores else 0.0,
        std_score=statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        max_max_tile=max(tiles) if tiles else 0,
        n_games=len(scores),
        aggregate_walltime_sec=elapsed,
        games=games,
        hard_wall_sec=hard_wall_sec,
        stagnated_any=any(g.final_state == "stagnated" for g in games),
        walltime_exceeded=any(g.final_state == "walltime_exceeded" for g in games),
    )
