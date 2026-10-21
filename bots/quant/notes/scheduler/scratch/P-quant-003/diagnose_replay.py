#!/usr/bin/env python3
"""Extra diagnostics for the quant-003 round-2 replay: fold-win count,
paired daily return difference, correlation, independent-event count."""
import pathlib

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPLAY = HERE
eq = pd.read_csv(REPLAY / "equity_curve.csv", index_col=0, parse_dates=True)
res = pd.read_csv(REPLAY / "results_replay.csv")
per = pd.read_csv(REPLAY / "results_percoin.csv")

k6 = eq["GATE_k6_net"]
b1 = eq["B1_net"]
print("replay window:", eq.index[0].date(), eq.index[-1].date(), len(eq), "days")
print("\nGATE_k6 vs B1_tsmom30_basket")
for r in res[res.variant.isin(["GATE_k6", "B1_tsmom30_basket"])].itertuples(index=False):
    print(f"  {r.variant:20s} net {r.net_pct:+7.2f}%  cagr {r.cagr_pct:+6.2f}%  "
          f"mdd {r.mdd_pct:+7.2f}%  sharpe {r.sharpe:.2f}  expo {r.expo:.2f}")
for i, y in enumerate(["2022", "2023", "2024"], 1):
    a = res[res.variant == "GATE_k6"].iloc[0]
    b = res[res.variant == "B1_tsmom30_basket"].iloc[0]
    print(f"  fold {y}: return k6 {a[f'y{i}_ret']:+7.2f}% vs B1 {b[f'y{i}_ret']:+7.2f}% ; "
          f"sharpe k6 {a[f'y{i}_sh']:+.2f} vs B1 {b[f'y{i}_sh']:+.2f}")

wins = sum(res[res.variant == "GATE_k6"].iloc[0][f"y{i}_sh"] >
           res[res.variant == "B1_tsmom30_basket"].iloc[0][f"y{i}_sh"] for i in (1, 2, 3))
print("\nfold Sharpe wins GATE_k6 vs B1:", wins, "/3")
d = (k6 - b1).dropna()
t = d.mean() / (d.std() / np.sqrt(len(d)))
print(f"daily difference k6-B1: mean {d.mean()*365:+.2%}/yr, ann.vol {d.std()*np.sqrt(365):.2%}, "
      f"t {t:.2f}, n {len(d)}, corr {k6.corr(b1):.3f}")
print(f"compound gap k6-B1: {res[res.variant=='GATE_k6'].iloc[0].net_pct - res[res.variant=='B1_tsmom30_basket'].iloc[0].net_pct:+.2f} pp")

print("\nper-coin plain 30d: k6 beats", int((res[res.variant == 'GATE_k6'].iloc[0].net_pct > per.net_pct).sum()), "/", len(per))
print("k-grid: best net =", res.loc[res.variant.str.startswith("GATE_k"), ["variant", "net_pct"]].sort_values("net_pct").iloc[-1].to_dict())
print("k-grid: best sharpe =", res.loc[res.variant.str.startswith("GATE_k"), ["variant", "sharpe"]].sort_values("sharpe").iloc[-1].to_dict())

k6m = res[res.variant == "GATE_k6"].iloc[0]
print(f"\n5000 USDT contribution: net CAGR {k6m.cagr_pct:.2f}% on total account = "
      f"{5000*k6m.cagr_pct/100:.0f} USDT/yr; average exposure {k6m.expo:.2f} "
      f"~ {5000*k6m.expo:.0f} USDT deployed on average")
