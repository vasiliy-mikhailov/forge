"""DockerCanonicalScorer adapter.

Spawns `reward-bench-tier1:${TAG}` per attempt. Reads
`/reports/result.json`. Returns an AttemptResult.

The imperative `.score()` is thin orchestration over three pure
helpers (`build_docker_cmd`, `parse_result_payload`,
`aggregate_attempt`); side effects (subprocess + filesystem) sit at
the edges.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from src.adapters.multiprocessing_cpu_count import MultiprocessingCpuCount
from src.ports.cpu_count import CpuCountPort
from src.ports.canonical_scorer import CanonicalScorerPort
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.entities.game_result import GameResult


_DEFAULT_IMAGE = "reward-bench-tier1:0.4"


# ---- pure helpers (no I/O) ----

def build_docker_cmd(
    *,
    image: str,
    submission_path: Path,
    env_path: Path | None,
    reports_dir: Path,
    cpus: float,
    memory: str,
    pids_limit: int,
    stagnation_sec: int,
    hard_wall_sec: float,
    seed_base: int,
    n_games: int,
    docker_bin: str = "docker",
) -> tuple[str, ...]:
    """Build the `docker run` arg tuple from pure inputs. No side effects."""
    parts: list[str] = [
        docker_bin, "run", "--rm",
        "--network=none",
        f"--memory={memory}",
        f"--pids-limit={pids_limit}",
        f"--cpus={cpus}",
        "-v", f"{submission_path}:/workspace/submission.py:ro",
    ]
    if env_path is not None:
        parts += ["-v", f"{env_path}:/env/env_2048.py:ro"]
    parts += [
        "-v", f"{reports_dir}:/reports",
        "-e", f"REWARD_BENCH_NUM_GAMES={n_games}",
        "-e", f"REWARD_BENCH_SEED_BASE={seed_base}",
        "-e", f"REWARD_BENCH_STAGNATION_SEC={stagnation_sec}",
        "-e", f"REWARD_BENCH_HARD_WALL_SEC={hard_wall_sec}",
        image,
    ]
    return tuple(parts)


def parse_result_payload(
    payload: dict,
    seeds: tuple[int, ...],
) -> tuple[GameResult, ...]:
    """Map a runner result.json payload + seed list to a tuple of GameResults.

    Seeds missing from the payload get walltime_exceeded sentinels.
    """
    by_seed: dict[int, dict] = {
        int(g["seed"]): g for g in payload.get("games", [])
    }
    return tuple(
        GameResult(
            seed=int(seed),
            score=int(by_seed[int(seed)].get("score", 0)),
            max_tile=int(by_seed[int(seed)].get("max_tile", 2)),
            moves=int(by_seed[int(seed)].get("moves", 0)),
            final_state=str(by_seed[int(seed)].get("final_state", "max_moves")),
            walltime_sec=float(by_seed[int(seed)].get("walltime_sec", 0.0)),
        ) if int(seed) in by_seed else _walltime_exceeded(seed)
        for seed in seeds
    )


def aggregate_attempt(
    games: tuple[GameResult, ...],
    elapsed_sec: float,
    hard_wall_sec: float,
) -> AttemptResult:
    """Aggregate a tuple of GameResults into an AttemptResult. Pure."""
    if not games:
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=0, aggregate_walltime_sec=elapsed_sec,
            games=(), hard_wall_sec=hard_wall_sec,
            stagnated_any=False, walltime_exceeded=False,
        )
    scores = [g.score for g in games]
    tiles = [g.max_tile for g in games]
    return AttemptResult(
        mean_score=sum(scores) / len(scores),
        median_score=statistics.median(scores),
        std_score=statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        max_max_tile=max(tiles),
        n_games=len(scores),
        aggregate_walltime_sec=elapsed_sec,
        games=games,
        hard_wall_sec=hard_wall_sec,
        stagnated_any=any(g.final_state == "stagnated" for g in games),
        walltime_exceeded=any(g.final_state == "walltime_exceeded" for g in games),
    )


# ---- adapter (orchestrates pure helpers + side effects) ----

class DockerCanonicalScorer(CanonicalScorerPort):
    """Per-attempt Docker-sandboxed canonical scorer."""

    def score_body(
        self,
        body: str,
        seeds,
        *,
        hard_wall_sec: float = 0.0,
    ):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            sp = Path(td) / 'submission.py'
            sp.write_text(body)
            return self.score(sp, seeds, hard_wall_sec=hard_wall_sec)

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

        Returns an AttemptResult with per-seed sentinel semantics
        (walltime_exceeded / solver_error / stagnated).
        """
        sub_path = Path(submission_path).resolve()
        seeds_t = tuple(int(s) for s in seeds)
        if not seeds_t:
            return aggregate_attempt((), elapsed_sec=0.0, hard_wall_sec=hard_wall_sec)

        if reports_root is not None:
            reports_dir = Path(reports_root).resolve()
            reports_dir.mkdir(parents=True, exist_ok=True)
        else:
            reports_dir = Path(tempfile.mkdtemp(prefix="reward-bench-docker-"))

        cmd = build_docker_cmd(
            image=self.image,
            submission_path=sub_path,
            env_path=self.env_path.resolve() if self.env_path is not None else None,
            reports_dir=reports_dir,
            cpus=self.cpus,
            memory=self.memory,
            pids_limit=self.pids_limit,
            stagnation_sec=self.stagnation_sec,
            hard_wall_sec=hard_wall_sec,
            seed_base=seeds_t[0],
            n_games=len(seeds_t),
            docker_bin=self.docker_bin,
        )

        start = time.monotonic()
        # +30s grace over hard_wall_sec: in-container runner enforces its own deadline.
        timeout = (hard_wall_sec + 30.0) if hard_wall_sec > 0 else None

        try:
            proc = subprocess.run(
                list(cmd), capture_output=True, text=True, timeout=timeout,
            )
            stdout, stderr, returncode = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired:
            stdout, stderr, returncode = "", "docker run exceeded outer timeout", 124

        elapsed = time.monotonic() - start

        if _is_infra_failure(returncode, stderr):
            raise RuntimeError(
                f"docker run infrastructure failure (returncode={returncode}); "
                f"stderr: {stderr.strip()[:500]}"
            )

        result_path = reports_dir / "result.json"
        if not result_path.exists():
            _log_missing_result_diagnostic(cmd, returncode, stdout, stderr,
                                           reports_dir, elapsed)
            games = tuple(_walltime_exceeded(s) for s in seeds_t)
            return aggregate_attempt(games, elapsed, hard_wall_sec)

        try:
            payload = json.loads(result_path.read_text())
        except Exception as e:
            _log_unparseable_result_diagnostic(cmd, result_path, e)
            games = tuple(_solver_error(s, "result.json unparseable") for s in seeds_t)
            return aggregate_attempt(games, elapsed, hard_wall_sec)

        games = parse_result_payload(payload, seeds_t)
        return aggregate_attempt(games, elapsed, hard_wall_sec)


# ---- side-effect helpers (used by adapter) ----

# Docker stderr patterns that indicate infrastructure failure.
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
    # 125: daemon error / image not found; 126: not executable; 127: not found.
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


def _log_missing_result_diagnostic(
    cmd: tuple[str, ...],
    returncode: int,
    stdout: str,
    stderr: str,
    reports_dir: Path,
    elapsed: float,
) -> None:
    """Surface the silent-zero-score pattern: container ran but wrote no result.json."""
    try:
        ls = sorted(p.name for p in reports_dir.iterdir())
    except Exception:
        ls = ['<unreadable>']
    print(
        f"[DockerCanonicalScorer] result.json missing after {elapsed:.2f}s "
        f"(returncode={returncode}). "
        f"cmd={list(cmd)} "
        f"reports_dir={reports_dir} contents={ls} "
        f"stdout_tail={stdout[-500:]!r} "
        f"stderr_tail={stderr[-500:]!r}",
        file=sys.stderr, flush=True,
    )


def _log_unparseable_result_diagnostic(
    cmd: tuple[str, ...], result_path: Path, exc: Exception,
) -> None:
    try:
        head = result_path.read_text()[:500]
    except Exception:
        head = '<unreadable>'
    print(
        f"[DockerCanonicalScorer] result.json unparseable at {result_path}: "
        f"{type(exc).__name__}: {exc}. "
        f"cmd={list(cmd)} "
        f"file_head={head!r}",
        file=sys.stderr, flush=True,
    )
