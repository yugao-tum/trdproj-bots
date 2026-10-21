#!/usr/bin/env python3
"""Compatibility wrapper for quant-001 number checks (2026-10-21).

The round-1 version of this script checked old-window numbers from
tradable_backtest.py / first-hour VWAP. Those windows are not allowed in the
round-2 entry and those numbers were removed from it. The old results stay
archived in REPORT.md / REPORT-hardening-round2.md and their CSVs.

The current entry is round-2 only; this wrapper runs the current verifier.
Run: python3 verify_entry_numbers.py
"""
import pathlib
import runpy

HERE = pathlib.Path(__file__).resolve().parent
runpy.run_path(str(HERE / "verify_replay_entry.py"), run_name="__main__")
