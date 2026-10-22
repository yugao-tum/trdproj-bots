#!/usr/bin/env python3
"""Secondary calculations for the quant-009 replay (reads markets.csv only).

Run: python3 analysis.py | tee analysis_output.txt

Two weighting schemes are reported because they answer different questions:
  * equal 1 share per triggered market  -> per-share edge (used by q009-hist)
  * fixed 300 USDT per market (the entry's stated size) -> capital-weighted return
The capital-weighted number is the one that matters for a 5,000 USDT account.
"""
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROWS = list(csv.DictReader((HERE / "markets.csv").open(encoding="utf-8")))
MODES = ["primary_7d", "sensitivity_3d", "diagnostic_14d"]
SIZE = 300.0
ACCOUNT = 5000.0

cols = ["entry_mode", "event_slug", "market_slug", "condition_id", "question", "token", "venue",
        "cluster", "end_date", "entry_time", "trade_ts", "trade_outcome", "trade_price",
        "trade_price_yes", "p_model", "side", "entry_price", "fee", "payoff", "net", "edge"]
trades = [r for r in ROWS if r["side"]]
with (HERE / "trades.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in sorted(trades, key=lambda x: (x["entry_mode"], int(x["trade_ts"]))):
        w.writerow(r)
print(f"[1] trades.csv: {len(trades)} triggered rows across {len(MODES)} variants\n")

uniq = {r["condition_id"]: r for r in ROWS if r["entry_mode"] == "primary_7d"}
yes_markets = [r for r in uniq.values() if float(r["yes_payoff"] or 0) > 0.5]
clusters = defaultdict(list)
for r in uniq.values():
    clusters[r["cluster"]].append(r)
yes_clusters = [c for c, rs in clusters.items() if any(float(r["yes_payoff"] or 0) > 0.5 for r in rs)]
print("[2] Full enumerated closed universe (no sampling)")
print(f"    markets={len(uniq)}  Yes markets={len(yes_markets)}  ({len(yes_markets)/len(uniq):.3%})")
print(f"    independent clusters={len(clusters)}  Yes clusters={len(yes_clusters)}  ({len(yes_clusters)/len(clusters):.3%})")
print("    CAUTION: 62/95 markets were already resolved before endDate-7d, so the")
print("    unconditional base rate is NOT the conditional probability at entry.")
print("    Among the 17 markets still priced at endDate-7d, market YES at entry was 0/17.\n")

for mode in MODES:
    rs = sorted([r for r in trades if r["entry_mode"] == mode], key=lambda x: int(x["trade_ts"]))
    if not rs:
        print(f"[{mode}] no trades\n")
        continue
    net = np.array([float(r["net"]) for r in rs])
    entry = np.array([float(r["entry_price"]) for r in rs])
    ret = net / entry                         # return on a fixed-USDT position
    cum = np.cumsum(net)
    print(f"[{mode}] trades={len(rs)}  equal-1-share: total net={net.sum():+.6f} on "
          f"{entry.sum():.6f} staked -> {net.sum()/entry.sum():+.2%} per $ of share cost")
    print(f"         fixed {SIZE:.0f} USDT/market: total PnL={ret.sum()*SIZE:+.2f} USDT on "
          f"{SIZE*len(rs):.0f} deployed -> {ret.mean():+.2%} per trade")
    cum_usd = np.cumsum(ret * SIZE)
    peak = np.maximum.accumulate(np.concatenate([[0.0], cum_usd]))
    dd = np.concatenate([[0.0], cum_usd]) - peak
    span = (max(int(r["trade_ts"]) for r in rs) - min(int(r["trade_ts"]) for r in rs)) / 86400.0
    print(f"         fixed-size running max drawdown={dd.min():+.2f} USDT "
          f"({dd.min()/ACCOUNT:+.2%} of 5,000); fill span {span:.0f} days")
    by = defaultdict(list)
    for r in rs:
        by[r["cluster"]].append(r)
    pnl_cluster = []
    for c, v in by.items():
        per = SIZE / len(v)
        pnl_cluster.append(sum(float(r["net"]) / float(r["entry_price"]) * per for r in v))
    pnl_cluster = np.array(pnl_cluster)
    cum_c = np.cumsum(pnl_cluster)
    peak_c = np.maximum.accumulate(np.concatenate([[0.0], cum_c]))
    dd_c = np.concatenate([[0.0], cum_c]) - peak_c
    print(f"         fixed {SIZE:.0f} USDT/cluster: clusters={len(by)} PnL={pnl_cluster.sum():+.2f} "
          f"on {SIZE*len(by):.0f} deployed -> {pnl_cluster.sum()/(SIZE*len(by)):+.2%}; "
          f"maxDD={dd_c.min():+.2f} USDT")
    if span > 0:
        print(f"         illustrative annualisation on 5,000 (fixed-size, non-continuous): "
              f"{ret.sum()*SIZE*365.0/span/ACCOUNT:+.2%}/yr -- NOT used in the entry (n<30)")
    print()

print("[3] Read with run_output.txt")
print("    canonical 7d: cluster median net<0, per-$ staked<0, CI crosses 0, priced clusters 10<30")
print("    fixed-size capital-weighted returns are negative in all three variants;")
print("    3d and 14d are diagnostics, not the frozen entry rule; none reaches 30 priced clusters.")
