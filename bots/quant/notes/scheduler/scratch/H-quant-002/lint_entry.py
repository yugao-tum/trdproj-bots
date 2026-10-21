#!/usr/bin/env python3
"""Field + number check for the single hardened entry (quant-002)."""
import pathlib, re
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[6]
HERE = pathlib.Path(__file__).resolve().parent
p = ROOT / "bots/quant/entries/quant-002-tom-monday-oos-counterevidence.md"
t = p.read_text(encoding="utf-8")
f = {}
for line in t.split("---", 2)[1].splitlines():
    if ":" in line:
        k, _, v = line.partition(":")
        f[k.strip()] = v.strip()
req = ["id", "name_zh", "name_en", "bot", "date", "market", "pm_category", "kind",
       "improves", "category", "return_type", "instruments", "venues", "data",
       "test_2w", "status", "confidence"]
problems = []
for k in req:
    if not f.get(k):
        problems.append(f"missing {k}")
if f.get("id") != "quant-002":
    problems.append("id changed")
if f.get("date") != "2026-10-20":
    problems.append("date changed")
if f.get("status") != "待核":
    problems.append("status changed")
if f.get("bot") != "quant":
    problems.append("bot wrong")
if f.get("kind") != "supplement":
    problems.append("kind changed")
if f.get("improves") != "E-E2-turn-of-month":
    problems.append("improves changed")
if not p.name.startswith(f["id"] + "-"):
    problems.append("filename/id mismatch")

# numbers in the two tables must match the CSVs
res = pd.read_csv(HERE / "tradable_results.csv")
tr = res[(res.fee_side == 0.0030) & (res.fill == "first_vwap")].set_index("version")
expected = {
    "BTC_tom_calendar_exact": -39.32, "ETH_tom_calendar_exact": -55.27,
    "BTC_mon_calendar_exact": -35.16, "ETH_mon_calendar_exact": -51.06,
    "BTC_tom_orig_shift": -3.71, "ETH_tom_orig_shift": -44.31,
    "BTC_mon_orig_shift": -69.92, "ETH_mon_orig_shift": -81.03,
}
for k, v in expected.items():
    if abs(tr.loc[k, "compound_pct"] - v) > 0.02:
        problems.append(f"tradable compound mismatch {k}: {tr.loc[k,'compound_pct']} vs {v}")

win = pd.read_csv(HERE / "windows.csv").set_index("version")
for k, v in {"BTC_mon_calendar_exact": 0.018, "BTC_tom_calendar_exact": 0.735}.items():
    if abs(win.loc[k, "p_one_sided_gross"] - v) > 0.002:
        problems.append(f"window p mismatch {k}: {win.loc[k,'p_one_sided_gross']} vs {v}")

print("entry:", p.relative_to(ROOT))
print("fields:", f)
print("PROBLEMS:", problems if problems else "none")
