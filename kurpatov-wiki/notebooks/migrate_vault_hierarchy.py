"""
One-shot migration: flat vault/raw/<stem>/raw.json  →  mirrored hierarchy
vault/raw/<course>/<module>/<stem>/raw.json.

The target path is rebuilt from info.source_path written by 02/03 into each
raw.json, so no guessing is required.

Run on the host (typically via ssh):
  python3 migrate_vault_hierarchy.py \
    --vault-raw /mnt/steam/forge/kurpatov-wiki/vault/raw \
    --strip-prefix /workspace/videos

  (add --dry-run to preview without moving)
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault-raw", required=True,
                    help="Root of vault/raw on the host.")
    ap.add_argument("--strip-prefix", default="/workspace/videos",
                    help="Prefix from info.source_path to strip off.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw_root = Path(args.vault_raw)
    prefix = Path(args.strip_prefix)

    if not raw_root.is_dir():
        print(f"[err ] {raw_root} does not exist")
        return 1

    # Only pick flat "candidates": <raw_root>/<dir>/raw.json — this is
    # the legacy layout we want to migrate.
    candidates = sorted(p for p in raw_root.iterdir() if p.is_dir())
    moved = 0
    already_ok = 0
    skipped = 0

    for old_dir in candidates:
        raw = old_dir / "raw.json"
        if not raw.exists():
            # could already be a "top level" of the new hierarchy
            # (e.g. the Psychologist-consultant course) — leave it alone
            continue

        info = json.loads(raw.read_text(encoding="utf-8")).get("info", {})
        src = info.get("source_path")
        if not src:
            print(f"[skip] {old_dir.name}: raw.json has no info.source_path")
            skipped += 1
            continue

        source = Path(src)
        try:
            rel = source.relative_to(prefix).with_suffix("")
        except ValueError:
            print(f"[skip] {old_dir.name}: source_path {src!r} outside {prefix}")
            skipped += 1
            continue

        target = raw_root / rel

        if target == old_dir:
            already_ok += 1
            continue

        if target.exists():
            print(f"[skip] {old_dir.name}: target already exists → {target}")
            skipped += 1
            continue

        print(f"[move] {old_dir.name}\n"
              f"         → {target.relative_to(raw_root)}")

        if args.dry_run:
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_dir), str(target))
        moved += 1

    print()
    print(f"[summary] moved={moved}  already_ok={already_ok}  "
          f"skipped={skipped}  dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
