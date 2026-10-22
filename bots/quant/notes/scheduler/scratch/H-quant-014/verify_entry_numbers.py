#!/usr/bin/env python3
"""Cross-check the round-2 numbers in the quant-014 entry against summarize stdout.

Run from repo root:
    python3 bots/quant/notes/scheduler/scratch/H-quant-014/verify_entry_numbers.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[6]
ENTRY = ROOT / "bots/quant/entries/quant-014-pm-spx-lognormal-calibration.md"
STDOUT = ROOT / "bots/quant/replay/quant-014/summarize_stdout.txt"

CHECKS = [
    ("all triggered mean", "-0.00743"),
    ("all triggered total", "-1.783"),
    ("all triggered per $1", "-0.0287"),
    ("all triggered median", "-0.14482"),
    ("fee=0 mean", "-0.00090"),
    ("fee=0 total", "-0.216"),
    ("daily FADE mean", "+0.00650"),
    ("daily FADE total", "+1.261"),
    ("daily FADE CI low", "-0.04872"),
    ("daily FADE CI high", "+0.06235"),
    ("daily FOLLOW mean", "-0.03835"),
    ("monthly above", "-0.06948"),
    ("monthly close", "-0.13662"),
    ("OOS all triggered", "-0.03452"),
    ("OOS daily FADE", "-0.02703"),
    ("Brier model", "0.25000"),
    ("Brier constant 0.53", "0.24923"),
    ("Brier market", "0.17783"),
    ("contribution fee .04", "-3.57%"),
    ("contribution fee 0", "-0.43%"),
]


def main():
    text = ENTRY.read_text(encoding="utf-8").replace("\u2212", "-")
    out = STDOUT.read_text(encoding="utf-8").replace("\u2212", "-")
    bad = 0
    for name, token in CHECKS:
        in_entry = token in text
        in_out = token in out
        ok = in_entry and in_out
        bad += 0 if ok else 1
        print("%-4s %-26s entry=%s stdout=%s  %s"
              % ("OK" if ok else "FAIL", name, in_entry, in_out, token))
    counts = (pathlib.Path(__file__).resolve().parent / "verify_counts_stdout.txt").read_text(encoding="utf-8")
    for name, entry_token, count_token in (
            ("ladder triggered legs", "16 条触发阶梯腿", "triggered ladder: legs=16"),
            ("ladder triggered mean", "-0.09885", "mean=-0.09885")):
        in_entry = entry_token in text
        in_counts = count_token in counts
        ok = in_entry and in_counts
        bad += 0 if ok else 1
        print("%-4s %-26s entry=%s counts=%s  %s"
              % ("OK" if ok else "FAIL", name, in_entry, in_counts, count_token))
    fields = dict(re.findall(r"^(evidence|result|slot|variants|variants_ext|window|max_dd|contribution): (.+)$",
                             text, re.M))
    print("\nround-2 fields: %s" % fields)
    expect = {"evidence": "回放", "result": "负", "slot": "-", "variants": "5", "variants_ext": "-",
              "window": "2025-10-15..2026-10-19", "max_dd": "-", "contribution": "-3.6%"}
    for k, v in expect.items():
        ok = fields.get(k) == v
        bad += 0 if ok else 1
        print("%-4s field %-14s %r" % ("OK" if ok else "FAIL", k, fields.get(k)))
    stale = "7 条阶梯腿全部为负"
    ok = stale not in text
    bad += 0 if ok else 1
    print("%-4s stale ladder-count phrase absent" % ("OK" if ok else "FAIL"))
    print("\nfailures=%d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
