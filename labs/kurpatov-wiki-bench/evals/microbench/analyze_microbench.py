#!/usr/bin/env python3
"""Read F1 microbench CSV, print per-L pass-rate and L*."""
import csv
import sys
from collections import defaultdict


def main(path):
    by_L = defaultdict(list)
    by_L_actual = defaultdict(list)
    by_L_args = defaultdict(list)
    by_L_lat = defaultdict(list)
    errors = defaultdict(list)

    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            L = int(r["L_target"])
            passed = int(r["passed"])
            by_L[L].append(passed)
            try:
                by_L_actual[L].append(int(r.get("L_bytes") or 0))
            except ValueError:
                pass
            try:
                by_L_args[L].append(int(r.get("args_len") or 0))
            except ValueError:
                pass
            try:
                by_L_lat[L].append(float(r.get("latency_s") or 0))
            except ValueError:
                pass
            if not passed and r.get("error"):
                errors[L].append(r["error"][:80])

    print(f"\n{'L_target':>9} {'pass_rate':>10} {'trials':>7} "
          f"{'L_bytes_avg':>11} {'args_len_avg':>13} {'lat_avg':>8}")
    print("-" * 70)
    for L in sorted(by_L):
        passes = by_L[L]
        rate = sum(passes) / len(passes)
        avg_bytes = sum(by_L_actual[L]) // max(1, len(by_L_actual[L]))
        args_vals = [v for v in by_L_args[L] if v > 0]
        avg_args = (sum(args_vals) // max(1, len(args_vals))) if args_vals else 0
        avg_lat = sum(by_L_lat[L]) / max(1, len(by_L_lat[L]))
        print(f"{L:>9} {rate:>10.2f} {len(passes):>7} "
              f"{avg_bytes:>11} {avg_args:>13} {avg_lat:>8.1f}s")

    L_star = None
    L_star_50 = None
    for L in sorted(by_L):
        rate = sum(by_L[L]) / len(by_L[L])
        if rate >= 0.95:
            L_star = L
        if rate >= 0.5:
            L_star_50 = L

    print(f"\nL*       (pass-rate ≥ 0.95) = {L_star} bytes" if L_star else "\nL*       (pass-rate ≥ 0.95) = NOT FOUND")
    print(f"L*_50    (pass-rate ≥ 0.50) = {L_star_50} bytes" if L_star_50 else "L*_50    (pass-rate ≥ 0.50) = NOT FOUND")

    if errors:
        print("\nFailure modes (sample):")
        for L in sorted(errors):
            print(f"  L={L}:")
            seen = set()
            for e in errors[L][:5]:
                key = e[:40]
                if key in seen:
                    continue
                seen.add(key)
                print(f"    - {e}")


if __name__ == "__main__":
    main(sys.argv[1])
