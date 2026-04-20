"""
Raw-transcripts auto-push daemon for the Kurpatov-wiki project.

Responsibility (single, by design):
  - Watch /workspace/vault/raw/data recursively for new or changed files
    (the content subtree — see ADR 0005's data/content-split amendment).
  - When the filesystem has been quiet for `--debounce-sec` seconds,
    run `git add -A && git commit && git push` inside
    /workspace/vault/raw (the git working tree — `.git/` is at this
    root, not under `data/`).

Deliberately decoupled from the transcriber:
  - The ingest daemon (03_watch_and_ingest.py) knows nothing about git.
  - This daemon knows nothing about whisper or source media.
  - They share only the vault filesystem via a Docker volume.

Repo naming:
  - This daemon pushes to the `kurpatov-wiki-raw` private GitHub repo.
    The git working tree IS /workspace/vault/raw (`--vault`); under
    that, all transcripts live in a `data/` subtree
    (`--raw`, default `/workspace/vault/raw/data`). The repo's root
    contains `data/<course>/<module>/<stem>/raw.json`, leaving the
    top level free for future meta files (README, CLAUDE.md, CI).
    The on-disk parent dir `vault/` (host:
    ${STORAGE_ROOT}/kurpatov-wiki/vault) and the deploy key file
    `~/.ssh/kurpatov-wiki-vault` retain their legacy names; renaming
    them is cheap and can happen out-of-band. Wiki output (built
    manually for now) will live in a separate `kurpatov-wiki-wiki`
    repo owned by a different workflow (ADR 0007).

Git plumbing assumptions:
  - /workspace/vault/raw is a git working tree, pre-initialized on
    the host.
  - .git/config has core.sshCommand pointing at the deploy key at
    ~/.ssh/kurpatov-wiki-vault (mounted read-only into this container).
  - remote `origin` points at the private kurpatov-wiki-raw repo (SSH URL).

Container UID vs host UID:
  - The container runs as root; .git on the host belongs to vmihaylov.
  - We pass `safe.directory`, `user.name`, `user.email` inline via `-c`
    flags on every git invocation, so no global git config is needed
    and nothing is written to the mounted .git beyond normal git state.

Failure model:
  - Any git failure is logged and swallowed. The daemon keeps running.
  - A failed push leaves the commit in place; the next filesystem event
    will re-trigger and a subsequent push will include everything.
  - If nothing is staged (e.g. event on a .tmp file that got removed),
    the commit+push is skipped — no empty commits.

Atomic-rename awareness:
  - The ingest daemon writes to <slug>.tmp/ and renames to <slug>/ when
    done. We ignore any path containing a '.tmp' component so we never
    commit a partial write — the rename itself generates an event for
    the final directory which we happily pick up.
"""

from __future__ import annotations

import argparse
import logging
import signal
import subprocess
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


log = logging.getLogger("raw-pusher")


# ---------------------------------------------------------------------------
# git helpers
# ---------------------------------------------------------------------------

def git_cmd_base(vault_root: Path) -> list[str]:
    return [
        "git", "-C", str(vault_root),
        "-c", f"safe.directory={vault_root}",
        "-c", "user.name=kurpatov-wiki-raw-pusher",
        "-c", "user.email=raw-pusher@forge.local",
    ]


def git_add_commit_push(vault_root: Path) -> None:
    """Stage, commit, and push any pending changes in the vault tree.

    Idempotent: if nothing is staged, it logs and returns without
    creating an empty commit or attempting a push.
    """
    base = git_cmd_base(vault_root)

    add = subprocess.run(
        base + ["add", "-A"],
        capture_output=True, text=True, timeout=60,
    )
    if add.returncode != 0:
        log.warning("[git  ] add failed: %s", add.stderr.strip())
        return

    # Anything actually staged?
    diff = subprocess.run(
        base + ["diff", "--cached", "--quiet"],
        capture_output=True, timeout=10,
    )
    if diff.returncode == 0:
        log.info("[git  ] nothing to commit")
        return

    # Build a concise commit message from the staged name-status output.
    names = subprocess.run(
        base + ["diff", "--cached", "--name-only"],
        capture_output=True, text=True, timeout=10,
    )
    changed = [
        line for line in names.stdout.splitlines() if line
    ] if names.returncode == 0 else []
    if len(changed) == 1:
        subject = f"vault: {changed[0]}"
    elif len(changed) <= 4:
        subject = "vault: " + ", ".join(changed)
    else:
        subject = f"vault: {len(changed)} files changed"

    commit = subprocess.run(
        base + ["commit", "-q", "-m", subject],
        capture_output=True, text=True, timeout=60,
    )
    if commit.returncode != 0:
        log.warning("[git  ] commit failed: %s", commit.stderr.strip())
        return
    log.info("[git  ] committed: %s (%d files)", subject, len(changed))

    push = subprocess.run(
        base + ["push", "--quiet"],
        capture_output=True, text=True, timeout=300,
    )
    if push.returncode != 0:
        log.warning(
            "[git  ] push failed: %s (local commit persists; next event re-pushes)",
            push.stderr.strip(),
        )
        return
    log.info("[git  ] pushed")


# ---------------------------------------------------------------------------
# debouncer
# ---------------------------------------------------------------------------

class Debouncer:
    """Coalesces bursts of filesystem events into one trigger.

    Each call to `bump()` resets the deadline to now + debounce_sec.
    A background loop fires `callback()` once the deadline is reached
    and nothing has bumped since.
    """

    def __init__(self, debounce_sec: float, callback):
        self.debounce_sec = debounce_sec
        self.callback = callback
        self._deadline: float | None = None
        self._lock = threading.Lock()
        self._shutdown = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def shutdown(self) -> None:
        self._shutdown.set()
        self._thread.join(timeout=5)

    def bump(self) -> None:
        with self._lock:
            self._deadline = time.time() + self.debounce_sec

    def _loop(self) -> None:
        while not self._shutdown.is_set():
            time.sleep(0.5)
            with self._lock:
                deadline = self._deadline
            if deadline is None:
                continue
            if time.time() < deadline:
                continue
            # Clear before firing so events during the callback re-arm us.
            with self._lock:
                self._deadline = None
            try:
                self.callback()
            except Exception:
                log.exception("[raw-pusher] callback failed")


# ---------------------------------------------------------------------------
# watchdog handler
# ---------------------------------------------------------------------------

class RawHandler(FileSystemEventHandler):
    def __init__(self, debouncer: Debouncer, raw_root: Path):
        self.debouncer = debouncer
        self.raw_root = raw_root

    def _is_tmp(self, path: str) -> bool:
        # Ignore any path that passes through a '.tmp' sibling — the
        # ingest daemon's atomic-write staging area.
        try:
            rel = Path(path).resolve().relative_to(self.raw_root)
        except ValueError:
            return False
        return any(part.endswith(".tmp") for part in rel.parts)

    def on_any_event(self, event) -> None:
        if event.is_directory:
            # Directory creations matter (new <stem>/ after rename), but
            # we'll also get a file event for raw.json inside, so it's
            # fine either way. Still trigger on dir events — cheap.
            if self._is_tmp(event.src_path):
                return
            self.debouncer.bump()
            return

        if self._is_tmp(event.src_path):
            return
        self.debouncer.bump()


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--vault", default="/workspace/vault/raw",
        help=(
            "Git working tree to commit from (the repo root — .git/ "
            "lives here). Distinct from --raw since content was moved "
            "into a data/ subtree without moving .git/; see ADR 0005 "
            "data/content-split amendment."
        ),
    )
    ap.add_argument(
        "--raw", default="/workspace/vault/raw/data",
        help=(
            "Subtree to watch for content changes. Defaults to the "
            "`data/` subtree under --vault. Staging-dir filters "
            "interpret paths relative to this root."
        ),
    )
    ap.add_argument("--debounce-sec", type=float, default=10.0,
                    help="Quiet-period seconds before committing a burst.")
    ap.add_argument("--initial-push", action="store_true", default=True,
                    help="On startup, attempt one add/commit/push in case "
                         "something landed while we were down.")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    vault_root = Path(args.vault).resolve()
    raw_root = Path(args.raw).resolve()

    if not (vault_root / ".git").exists():
        log.error("no .git at %s — refusing to start", vault_root)
        raise SystemExit(2)
    if not raw_root.exists():
        raw_root.mkdir(parents=True, exist_ok=True)
        log.warning("[raw-pusher] created empty raw root at %s", raw_root)

    log.info("[raw-pusher] vault=%s raw=%s debounce=%.1fs",
             vault_root, raw_root, args.debounce_sec)

    shutdown = threading.Event()

    def _fire() -> None:
        log.info("[raw-pusher] quiet period reached; running git add/commit/push")
        git_add_commit_push(vault_root)

    debouncer = Debouncer(args.debounce_sec, _fire)
    debouncer.start()

    observer = Observer()
    observer.schedule(RawHandler(debouncer, raw_root), str(raw_root), recursive=True)
    observer.start()
    log.info("[raw-pusher] inotify on %s (recursive)", raw_root)

    if args.initial_push:
        # Belt-and-braces: flush anything that landed while we were offline.
        log.info("[raw-pusher] initial sync")
        git_add_commit_push(vault_root)

    def _sig(signum, _frame):
        log.info("[raw-pusher] got signal %d, shutting down", signum)
        shutdown.set()

    for s in (signal.SIGINT, signal.SIGTERM):
        signal.signal(s, _sig)

    try:
        while not shutdown.is_set():
            time.sleep(1.0)
    finally:
        log.info("[raw-pusher] stopping observer")
        observer.stop()
        observer.join(timeout=5)
        debouncer.shutdown()
        # Final flush on the way out.
        try:
            git_add_commit_push(vault_root)
        except Exception:
            log.exception("[raw-pusher] final flush failed")
        log.info("[raw-pusher] bye")


if __name__ == "__main__":
    main()
