#!/usr/bin/env python3
"""Placebo test for the BTC SMA gate: circularly shift the gate series by a random
number of days (preserving its on/off run lengths and off-fraction) and compare the
actual gate's OOS return / drawdown with the placebo distribution.

Fill = first-hour VWAP, cost = 0.30%/side, 4 OOS folds as in tradable_backtest.py.
Run: python3 placebo_gate.py
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
FEE = 0.003
N = 2000
rng = np.random.default_rng(20261021)
lines = []


def run_gate(keep):
    wg = w.mul(keep.shift(1).fillna(1.0), axis=0)
    return tb.metrics(tb.net_fill(wg, fill, FEE), wg, tb.FOLDS)


for name, n in [("SMA50", 50), ("SMA100", 100), ("SMA200", 200)]:
    keep = tb.sma_gate(btc["close"], n).astype(float)
    actual = run_gate(keep)
    arr = keep.values
    comps, dds, shs = [], [], []
    for _ in range(N):
        s = int(rng.integers(1, len(arr)))
        k = pd.Series(np.roll(arr, s), index=keep.index)
        r = run_gate(k)
        comps.append(r["compound_pct"]); dds.append(r["path_dd_pct"]); shs.append(r["mean_sharpe"])
    comps, dds, shs = map(np.array, (comps, dds, shs))
    p_comp = float((comps >= actual["compound_pct"]).mean())
    p_dd = float((dds <= actual["path_dd_pct"]).mean())
    p_sh = float((shs >= actual["mean_sharpe"]).mean())
    line = (f"{name}: actual compound={actual['compound_pct']:.2f}% pathDD={actual['path_dd_pct']:.2f}% "
            f"meanSharpe={actual['mean_sharpe']:.3f} | placebo N={N} "
            f"compound p50/p95={np.percentile(comps,50):.1f}/{np.percentile(comps,95):.1f}% "
            f"pathDD p5/p50={np.percentile(dds,5):.1f}/{np.percentile(dds,50):.1f}% "
            f"meanSharpe p50/p95={np.percentile(shs,50):.3f}/{np.percentile(shs,95):.3f} | "
            f"p(placebo compound>=actual)={p_comp:.3f}, "
            f"p(placebo DD<=actual)={p_dd:.3f}, p(placebo Sharpe>=actual)={p_sh:.3f}")
    lines.append(line)
    pd.DataFrame({"compound_pct": comps, "path_dd_pct": dds, "mean_sharpe": shs}).to_csv(
        HERE / f"placebo_{name}.csv", index=False, float_format="%.4f")

text = "\n".join(lines)
print(text)
(HERE / "placebo_stdout.txt").write_text(text + "\n")
