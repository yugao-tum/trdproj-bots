#!/usr/bin/env python3
"""Run the quant-025 replay from scratch (keyless public endpoints).

Stages (all paths relative to this directory, raw data in gitignored _cache/):
  1. fetch_outlooks.py  Gamma events + archived SPC Day-1 tornado GeoJSON
  2. filter_62.py       freeze the 62-event sample 2026-08-19..2026-10-19
  3. fetch_headers.py   HTTP Last-Modified of each archived GeoJSON
  4. classify.py        point-in-polygon settlement check
  5. fetch_trades.py    Polymarket data-api per-trade fills (1550 markets)
  6. reproduce.py       pre-registered strict/broad replay + replay_results.json
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
STAGES = ["fetch_outlooks.py", "filter_62.py", "fetch_headers.py",
          "classify.py", "fetch_trades.py"]


def main():
    for stage in STAGES:
        print(f"\n=== {stage} ===", flush=True)
        subprocess.run([sys.executable, stage], cwd=HERE, check=True)
    print("\n=== reproduce.py ===", flush=True)
    out = subprocess.run([sys.executable, "reproduce.py"], cwd=HERE,
                         check=True, text=True, capture_output=True).stdout
    print(out, end="")
    (HERE / "reproduce.out").write_text(out)
    print("\noutputs: reproduce.out, replay_results.json (raw cache in _cache/, gitignored)")


if __name__ == "__main__":
    main()
