"""
One-shot migration: rename legacy ``<stem>.html/`` directories under
``vault/raw/data/`` to bare ``<stem>/``.

Motivated by the 2026-04-21 amendment to
[ADR 0008](../docs/adr/0008-ingest-dispatch.md) — HTML-produced raws
now share the media slug rule (strip extension).

Must run inside the pusher container (root-owned files, and we want
the rename to show up as a git rename in the raw repo). Typical
invocation from the server::

    docker compose -f ~/repos/forge/kurpatov-wiki/docker-compose.yml run \\
        --rm --entrypoint bash raw-pusher -lc '
            set -euo pipefail
            cd /workspace/vault/raw
            git config --global --add safe.directory /workspace/vault/raw
            python3 /workspace/notebooks/migrate_html_slug.py \\
                --raw-root /workspace/vault/raw
            if ! git diff --cached --quiet; then
                git commit -m "migrate: rename <stem>.html/ -> <stem>/ (ADR 0008 2026-04-21)"
                git push
            fi
        '

Idempotent — if no ``*.html`` directories remain the script is a no-op.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


HTML_SUFFIXES = {".html", ".htm"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-root", required=True,
                    help="Root of the vault/raw git repo "
                         "(typically /workspace/vault/raw).")
    ap.add_argument("--data-subdir", default="data",
                    help="Content subdir under raw root (default: data).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would move, don't touch disk.")
    args = ap.parse_args()

    raw_root = Path(args.raw_root).resolve()
    data_root = raw_root / args.data_subdir
    if not data_root.is_dir():
        print(f"[err ] {data_root} is not a directory", file=sys.stderr)
        return 1

    # Every directory whose name ends in .html/.htm and contains raw.json
    # is a legacy HTML output slug we want to rename.
    candidates = []
    for p in data_root.rglob("*"):
        if p.is_dir() and p.suffix.lower() in HTML_SUFFIXES:
            if (p / "raw.json").exists():
                candidates.append(p)

    if not candidates:
        print("[ ok ] no legacy .html/ directories found; nothing to do")
        return 0

    renamed, skipped = 0, 0
    for src in sorted(candidates):
        dst = src.with_suffix("")  # drops .html / .htm
        if dst.exists():
            print(f"[skip] {src.relative_to(raw_root)} → "
                  f"{dst.relative_to(raw_root)} (target exists)")
            skipped += 1
            continue
        print(f"[mv  ] {src.relative_to(raw_root)} → "
              f"{dst.relative_to(raw_root)}")
        if args.dry_run:
            continue
        # Prefer `git mv` — keeps history as a rename in the raw repo.
        res = subprocess.run(
            ["git", "-C", str(raw_root), "mv", "--", str(src), str(dst)],
            capture_output=True, text=True,
        )
        if res.returncode != 0:
            print(f"[err ] git mv failed: {res.stderr.strip()}",
                  file=sys.stderr)
            return 2
        renamed += 1

    print(f"[done] renamed={renamed} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
