#!/usr/bin/env python3
"""Cross-check quant-001's round-2 front-matter and quoted replay numbers.

Reads bots/quant/replay/quant-001/replay_results.json (produced by run_replay.py)
and the entry, then checks every headline number.  Also checks file sizes and
forbidden binary extensions in the replay directory.

Run: python3 verify_replay_entry.py
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[5]
ENTRY = ROOT / "bots/quant/entries/quant-001-vm-btc-regime-gate.md"
REPLAY = ROOT / "bots/quant/replay/quant-001"
RES = json.loads((REPLAY / "replay_results.json").read_text())
text = ENTRY.read_text(encoding="utf-8")
summary = (REPLAY / "SUMMARY.md").read_text(encoding="utf-8")
norm = text.replace("−", "-")

fm = {}
for line in text.split("---", 2)[1].splitlines():
    if ":" in line:
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()

checks = []


def ck(name, ok, detail=""):
    checks.append((name, bool(ok), detail))


# --- round-2 front matter ---
expect = {
    "evidence": "回放", "result": "不显著", "slot": "-",
    "variants": "8", "variants_ext": "不清楚",
    "window": "2022-01-01..2024-12-31",
    "max_dd": "-24.6%（日线）", "contribution": "0.4%",
}
for k, v in expect.items():
    ck(f"front-matter {k}={v}", fm.get(k) == v, f"got {fm.get(k)!r}")
ck("id/date/status unchanged",
   (fm.get("id"), fm.get("date"), fm.get("status")) == ("quant-001", "2026-10-20", "待核"),
   str((fm.get("id"), fm.get("date"), fm.get("status"))))

# --- headline numbers vs replay_results.json ---
r = RES["results"]
rows = {
    "VM": ("+23.31", "8.90", "-35.69"),
    "VM_x_SMA50": ("+59.73", "20.99", "-24.58"),
    "VM_x_SMA100": ("+83.41", "27.99", "-23.28"),
    "VM_x_SMA200": ("+48.97", "17.61", "-33.54"),
    "const_scale_SMA50": ("+20.07", "7.73", "-28.54"),
    "const_scale_SMA100": ("+19.05", "7.35", "-26.67"),
    "const_scale_SMA200": ("+19.09", "7.37", "-26.75"),
}
for key, (comp, cagr, dd) in rows.items():
    m = r[key]
    ck(f"{key} compound {comp}", f"{m['compound_pct']:+.2f}" == comp,
       f"{m['compound_pct']:+.2f}")
    ck(f"{key} cagr {cagr}", f"{m['cagr_pct']:.2f}" == cagr, f"{m['cagr_pct']:.2f}")
    ck(f"{key} dd {dd}", f"{m['max_dd_pct']:.2f}" == dd, f"{m['max_dd_pct']:.2f}")
    ck(f"entry quotes {key} row",
       all(x in norm for x in (comp + "%", cagr + "%", dd + "%")),
       "strings found in entry")

ck("entry quotes +23.31%", "+23.31%" in norm)
ck("entry quotes +59.73%", "+59.73%" in norm)
ck("entry quotes +83.41%", "+83.41%" in norm)
ck("entry quotes +48.97%", "+48.97%" in norm)
ck("entry quotes 20.99%", "20.99%" in norm)
ck("entry quotes 21.0% only as caveated full-sample", "21.0%" in norm and "不把 21.0% 当字段值或预期" in norm)
ck("entry quotes contribution 0.4%", "0.4%" in norm)
ck("entry keeps status note", "status/date" in norm)
ck("entry quotes -24.58%", "-24.58%" in norm)
ck("entry quotes -35.69%", "-35.69%" in norm)
ck("entry quotes 7.75%", "7.75%" in norm)
ck("entry quotes p 0.066", "0.066" in norm)
ck("entry quotes p 0.084", "0.084" in norm)
ck("entry quotes p 0.278", "0.278" in norm)
ck("entry quotes episodes 24/18/8", "24/18/8" in norm)
ck("entry quotes off-episode mean -1.18", "-1.18%" in norm)
ck("entry quotes negative 12/24", "12/24" in norm)
ck("entry quotes 52 switches", "46 次切换" in norm)
ck("entry quotes 45.56", "45.56" in norm)
ck("entry quotes k 0.773", "0.773" in norm)

# --- holdout / walk-forward numbers ---
HO = json.loads((REPLAY / "holdout_results.json").read_text())
h = HO["splits"]["holdout_2024"]
ck("2024 VM compound -8.64", f"{h['VM']['compound_pct']:+.2f}" == "-8.64")
ck("2024 SMA50 compound +0.39", f"{h['VM_x_SMA50']['compound_pct']:+.2f}" == "+0.39")
ck("2024 SMA100 compound +2.10", f"{h['VM_x_SMA100']['compound_pct']:+.2f}" == "+2.10")
ck("2024 SMA200 compound -16.29", f"{h['VM_x_SMA200']['compound_pct']:+.2f}" == "-16.29")
wf = HO["walk_forward"]["metrics"]
ck("walk-forward compound +96.04", f"{wf['compound_pct']:+.2f}" == "+96.04")
ck("walk-forward cagr 39.95", f"{wf['cagr_pct']:.2f}" == "39.95")
ck("walk-forward dd -23.28", f"{wf['max_dd_pct']:.2f}" == "-23.28")
ck("entry quotes 2024 +0.39%", "+0.39%" in norm)
ck("entry quotes 2024 -8.64%", "-8.64%" in norm)
ck("entry quotes walk-forward +96.04%", "+96.04%" in norm)
ck("entry quotes walk-forward 39.95%", "39.95%" in norm)
ck("entry quotes always-SMA100", "always-SMA100" in norm)

# --- SUMMARY completeness ---
for i in range(1, 10):
    ck(f"SUMMARY variant row {i}", re.search(rf"^\| {i} \|", summary, re.M) is not None)
ck("SUMMARY states 不显著", "不显著" in summary)
ck("SUMMARY states 8 variants", "**8**" in summary)
ck("SUMMARY states window", "2022-01-01..2024-12-31" in summary)
ck("SUMMARY has reproduce command", "run_replay.py" in summary)
ck("SUMMARY has holdout command", "run_holdout.py" in summary)
ck("SUMMARY lists data URL", "data-api.binance.vision/api/v3/klines" in summary)

# --- files: size and binary extensions ---
bad_ext = {".pkl", ".pickle", ".parquet", ".npy", ".zip", ".gz", ".bz2", ".xz",
           ".db", ".sqlite", ".xlsx", ".pdf", ".feather", ".h5", ".arrow",
           ".pyc", ".so", ".bin"}
for p in REPLAY.rglob("*"):
    if p.is_file():
        ck(f"<1MB {p.name}", p.stat().st_size < 1_000_000, f"{p.stat().st_size} bytes")
        ck(f"not binary {p.name}", p.suffix.lower() not in bad_ext, p.suffix)

fails = [c for c in checks if not c[1]]
for name, ok, detail in checks:
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))
print(f"\n{len(checks)} checks, {len(fails)} failed")
raise SystemExit(1 if fails else 0)
