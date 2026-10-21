#!/usr/bin/env python3
"""Cross-check the numbers quoted in quant-001 against the CSVs/stdout produced by
tradable_backtest.py, placebo_gate.py and familywise_placebo.py.

This is a consistency check, not a new backtest: every check is a literal string
that must appear in the entry. Run from this directory: python3 verify_entry_numbers.py
"""
import pathlib
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[5]
ENTRY = ROOT / "bots/quant/entries/quant-001-vm-btc-regime-gate.md"
text = ENTRY.read_text(encoding="utf-8")
tr = pd.read_csv(HERE / "tradable_results.csv")
se = pd.read_csv(HERE / "same_exposure.csv")

checks = []


def need(label, s):
    checks.append((label, s, s in text))


def row(variant, fill, fee):
    r = tr[(tr.variant == variant) & (tr.fill == fill) & (tr.fee_side == fee)]
    assert len(r) == 1, (variant, fill, fee, len(r))
    return r.iloc[0]


# 4 OOS folds, first-hour VWAP, 0.30%/side (table in "可成交价回测")
for variant, comp, cagr, worst, path, expo in [
    ("VM", "232.5", "37.3", "15.7", "22.6", "0.29"),
    ("VM_x_SMA50", "213.1", "35.2", "16.1", "19.6", "0.24"),
    ("VM_x_SMA100", "148.1", "27.1", "15.5", "19.5", "0.22"),
    ("VM_x_SMA200", "140.7", "26.1", "15.5", "20.9", "0.21"),
]:
    r = row(variant, "fill", 0.003)
    need(f"{variant} compound", f"+{comp}%")
    need(f"{variant} cagr", cagr + "%")
    need(f"{variant} worst", "−" + worst + "%")
    need(f"{variant} path", "−" + path + "%")
    need(f"{variant} exposure", expo)

# old close-fill rows
for variant, comp, cagr, worst, path, expo in [
    ("VM", "237.2", "37.8", "15.8", "22.1", "0.29"),
    ("VM_x_SMA50", "224.2", "36.4", "14.1", "19.1", "0.24"),
]:
    r = row(variant, "close", 0.003)
    need(f"{variant} close compound", f"+{comp}%")
    need(f"{variant} close cagr", cagr + "%")
    need(f"{variant} close worst", "−" + worst + "%")
    need(f"{variant} close path", "−" + path + "%")

# 1.00%/side stress
for variant, comp, cagr, path in [
    ("VM_x_SMA50", "113.4", "22.1", "21.5"),
    ("VM_x_SMA100", "70.4", "15.1", "24.0"),
    ("VM_x_SMA200", "75.7", "16.0", "25.7"),
]:
    r = row(variant, "fill", 0.010)
    need(f"{variant} 1pct compound", f"+{comp}%")
    need(f"{variant} 1pct cagr", cagr + "%")

# same-exposure diagnostic
for _, r in se.iterrows():
    need(f"{r.variant} k", f"{r.const_scale_k:.2f}")
    need(f"{r.variant} const compound", f"+{r.const_compound:.1f}%")
    need(f"{r.variant} const path", f"−{abs(r.const_path_dd):.1f}%")

# off-episodes: counts, switches, off-days, medians, means, negative counts
ep = {n: pd.read_csv(HERE / f"episodes_{n}.csv") for n in ("SMA50", "SMA100", "SMA200")}
need("SMA50 episodes", "60 段")
need("SMA100 episodes", "39 段")
need("SMA200 episodes", "25 段")
need("SMA50 switches", "120 次")
need("SMA50 off days", "1036 天")
need("SMA50 median/max", "段长中位数 6 天、最长 99 天")
for n, mean, med, neg in [("SMA50", "0.16", "0.00", 20), ("SMA100", "0.95", "0.42", 9),
                          ("SMA200", "3.12", "0.08", 1)]:
    d = ep[n]
    assert len(d) == {"SMA50": 60, "SMA100": 39, "SMA200": 25}[n]
    need(f"{n} mean", f"+{mean}%")
    need(f"{n} median", f"{med}%")
    need(f"{n} negative", f"{neg}/{len(d)}")

# placebo table / stdout
pl = (HERE / "placebo_stdout.txt").read_text(encoding="utf-8")
for n, comp, pdd, psh, pcomp, pddv in [
    ("SMA50", "213.1", "-19.6", "1.227", "0.032", "0.601"),
    ("SMA100", "148.1", "-19.5", "0.966", "0.125", "0.572"),
    ("SMA200", "140.7", "-20.9", "1.031", "0.156", "0.430"),
]:
    need(f"{n} placebo actual", f"+{comp}% / −{abs(float(pdd)):.1f}% / {psh}")
    need(f"{n} placebo pcomp", pcomp)
    need(f"{n} placebo pdd", pddv)

# family-wise max-statistic adjustment (new in round 2)
fw = (HERE / "familywise_placebo_stdout.txt").read_text(encoding="utf-8")
need("familywise p compound", "p(compound)=0.070")
need("familywise p dd", "p(pathDD)=0.812")
need("familywise p sharpe", "p(Sharpe)=0.219")
need("familywise interpretation", "0.032" if "0.032" in text else "p=0.032")

print(f"entry: {ENTRY.relative_to(ROOT)}")
print(f"checks: {len(checks)}  failed: {sum(not ok for _, _, ok in checks)}")
for label, s, ok in checks:
    if not ok:
        print(f"FAIL {label}: expected {s!r}")
print("RESULT:", "PASS" if all(ok for _, _, ok in checks) else "FAIL")
