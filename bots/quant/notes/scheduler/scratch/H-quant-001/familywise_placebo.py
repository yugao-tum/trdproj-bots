#!/usr/bin/env python3
"""Family-wise (max-statistic) placebo check for the three pre-specified BTC SMA
gates in quant-001.

The single-gate placebo in placebo_gate.py draws a *different* random shift for
each gate, so the three p-values cannot be combined. This script replays the
SAME cyclic shift for all three gates, which lets us ask: across the 3-gate
family, how often does *any* gate beat the best actual gate by chance?

Fill = first-hour VWAP, 0.30%/side, 4 OOS folds, same rules as tradable_backtest.py.
Run: python3 familywise_placebo.py  (about 60 s)
"""
import importlib.util, pathlib
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("tb", HERE / "tradable_backtest.py")
tb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tb)

panels = {s: tb.load_daily(s) for s in tb.SYMS}
px = pd.DataFrame({s: panels[s]["close"] for s in tb.SYMS}).dropna()
fill = pd.DataFrame({s: panels[s]["fill_vwap"] for s in tb.SYMS}).reindex(px.index)
w = tb.vm_weights(px)
btc = panels["BTC"].reindex(px.index)
FEE, N = 0.003, 2000
GATES = [("SMA50", 50), ("SMA100", 100), ("SMA200", 200)]
rng = np.random.default_rng(20261021)


def run_gate(keep):
    wg = w.mul(keep.shift(1).fillna(1.0), axis=0)
    return tb.metrics(tb.net_fill(wg, fill, FEE), wg, tb.FOLDS)


actual = {}
for name, n in GATES:
    actual[name] = run_gate(tb.sma_gate(btc["close"], n).astype(float))

# same shift for every gate in a given draw
rows = []
for _ in range(N):
    s = int(rng.integers(1, len(btc)))
    row = {"shift": s}
    for name, n in GATES:
        keep = tb.sma_gate(btc["close"], n).astype(float)
        k = pd.Series(np.roll(keep.values, s), index=keep.index)
        r = run_gate(k)
        row[f"{name}_compound"] = r["compound_pct"]
        row[f"{name}_dd"] = r["path_dd_pct"]
        row[f"{name}_sharpe"] = r["mean_sharpe"]
    rows.append(row)
df = pd.DataFrame(rows)
df.to_csv(HERE / "familywise_placebo.csv", index=False, float_format="%.4f")

comp_cols = [f"{n}_compound" for n, _ in GATES]
dd_cols = [f"{n}_dd" for n, _ in GATES]
sh_cols = [f"{n}_sharpe" for n, _ in GATES]
max_comp = df[comp_cols].max(axis=1).values
min_dd = df[dd_cols].min(axis=1).values
max_sh = df[sh_cols].max(axis=1).values

best_name = max(actual, key=lambda n: actual[n]["compound_pct"])
best_comp = actual[best_name]["compound_pct"]
best_dd = actual[best_name]["path_dd_pct"]
best_sh = actual[best_name]["mean_sharpe"]

p_fw_comp = float((max_comp >= best_comp).mean())
p_fw_dd = float((min_dd <= best_dd).mean())
p_fw_sh = float((max_sh >= best_sh).mean())

lines = []
lines.append("common-shift placebo, N=%d, fill=first-hour VWAP, fee=0.30%%/side, 4 OOS folds" % N)
lines.append("actual (single gate, family best = %s): compound=%.2f%% pathDD=%.2f%% meanSharpe=%.3f"
             % (best_name, best_comp, best_dd, best_sh))
for name, _ in GATES:
    a = actual[name]
    adj_comp = float((max_comp >= a["compound_pct"]).mean())
    adj_dd = float((min_dd <= a["path_dd_pct"]).mean())
    adj_sh = float((max_sh >= a["mean_sharpe"]).mean())
    lines.append("%s: actual compound=%.2f%% pathDD=%.2f%% Sharpe=%.3f | max-stat adjusted p "
                 "(compound/DD/Sharpe)=%.3f/%.3f/%.3f"
                 % (name, a["compound_pct"], a["path_dd_pct"], a["mean_sharpe"],
                    adj_comp, adj_dd, adj_sh))
lines.append("family-wise (any of 3 gates vs family-best actual): "
             "p(compound)=%.3f p(pathDD)=%.3f p(Sharpe)=%.3f"
             % (p_fw_comp, p_fw_dd, p_fw_sh))
lines.append("interpretation: the single-gate SMA50 compound p=0.032 in placebo_gate.py is "
             "unadjusted; after accounting for picking the best of 3 pre-specified gates, "
             "the compound p rises to %.3f." % p_fw_comp)
text = "\n".join(lines)
print(text)
(HERE / "familywise_placebo_stdout.txt").write_text(text + "\n")
