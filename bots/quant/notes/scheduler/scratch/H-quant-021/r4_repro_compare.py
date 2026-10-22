#!/usr/bin/env python3
"""Compare the committed replay products with a fresh cold-cache rerun.

Usage: python3 r4_repro_compare.py <committed_dir> <fresh_dir>
No network, no writes outside stdout.
"""
import hashlib
import json
import pathlib
import sys

committed = pathlib.Path(sys.argv[1])
fresh = pathlib.Path(sys.argv[2])

a = json.loads((committed / "results.json").read_text())
b = json.loads((fresh / "results.json").read_text())

keys = ["primary", "bootstrap", "per_season", "fit", "p0", "events", "pole_wins",
        "mean_p_hist", "mean_modelA", "break_even_gap", "months", "annual_usdt",
        "contribution_pct", "cross_section", "variants"]
bad = 0
for key in keys:
    ok = a.get(key) == b.get(key)
    bad += 0 if ok else 1
    print(f"{key:20s} equal={ok}")
if "generated_utc" in a or "generated_utc" in b:
    print(f"generated_utc committed={a.get('generated_utc')} fresh={b.get('generated_utc')} (expected to differ)")

for name in ["trades.csv", "all_events.csv", "cross_section.csv"]:
    ha = hashlib.sha256((committed / name).read_bytes()).hexdigest()
    hb = hashlib.sha256((fresh / name).read_bytes()).hexdigest()
    ok = ha == hb
    bad += 0 if ok else 1
    print(f"{name:20s} byte_identical={ok} sha256={ha[:16]} bytes={(committed/name).stat().st_size}")
print("ALL_EQUAL" if bad == 0 else f"MISMATCHES={bad}")
sys.exit(0 if bad == 0 else 1)
