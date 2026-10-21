#!/usr/bin/env python3
"""Verify every local file cited by quant-001's 出处 section exists, is <1 MB,
and is not a forbidden binary. Read-only. Run from repo root:
python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_cited_local.py
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[6]
GROUPS = {
    "bots/quant/replay/quant-001": [
        "run_replay.py", "SUMMARY.md", "replay_stdout.txt", "replay_results.json",
        "replay_equity.csv", "episodes_SMA50.csv", "episodes_SMA100.csv",
        "episodes_SMA200.csv", "placebo_results.json",
    ],
    "bots/quant/notes/scheduler/scratch/H-quant-001": [
        "REPORT.md", "REPORT-hardening-round2.md", "tradable_backtest.py",
        "tradable_stdout.txt", "tradable_results.csv", "same_exposure.csv",
        "placebo_gate.py", "placebo_stdout.txt", "familywise_placebo.py",
        "familywise_placebo_stdout.txt", "familywise_placebo.csv",
        "episodes_SMA50.csv", "episodes_SMA100.csv", "episodes_SMA200.csv",
        "fetch_hourly.py", "verify_sources.py", "verify_sources_stdout.txt",
        "verify_entry_numbers.py", "lint_entry.py",
    ],
    "bots/quant/notes/xqt-migration": ["README.md", "reproduce.py", "results.csv"],
    "bots/quant/notes/xqt-migration/q001-robustness": [
        "REPORT.md", "q001_robustness.py", "run_output.txt", "variants.csv",
    ],
}
BINARY = {".pkl", ".pickle", ".parquet", ".feather", ".npy", ".npz", ".joblib",
          ".zip", ".gz", ".bz2", ".xz", ".7z", ".db", ".sqlite", ".h5", ".hdf5",
          ".xlsx", ".pdf"}
bad = 0
for d, names in GROUPS.items():
    for name in names:
        p = ROOT / d / name
        ok = p.is_file() and p.stat().st_size < 1_000_000 and p.suffix.lower() not in BINARY
        bad += not ok
        print(f"{'OK' if ok else 'FAIL'} {d}/{name} size={p.stat().st_size if p.exists() else '-'}")
print(f"cited local files: {sum(len(v) for v in GROUPS.values())}  failed: {bad}")
raise SystemExit(1 if bad else 0)
