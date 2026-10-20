#!/usr/bin/env python3
"""Independent re-computation of quant-006 gate-6 numbers from saved matches.csv.

Reads bots/quant/notes/q006-hist/matches.csv only (no network). No downloads,
no re-run of the original backtest. Produces the aggregates quoted in the entry
plus a zero-cost sensitivity, so every number has a script + stdout under I02.
"""
from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[6]
CSV = ROOT / "bots/quant/notes/q006-hist/matches.csv"
df = pd.read_csv(CSV)


def pct(x):
    return f"{x:+.4%}"


def boot_median(x, seed=20261020, draws=20000):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(draws, len(x)))
    med = np.median(x[idx], axis=1)
    return np.percentile(med, [2.5, 50, 97.5])


def binom_two_sided(k, n, p=0.5):
    if k <= n / 2:
        tail = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n
    else:
        tail = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


print("== quant-006 I02 independent recompute ==")
print("csv:", CSV.relative_to(ROOT))
print("rows:", len(df))

priced = df[df["price_a"].notna()].copy()
trig = priced[priced["triggered"].eq(True)].copy()
print("priced (main-window both outcome prices):", len(priced))
print("triggered main:", len(trig), f"({len(trig)/len(priced):.1%} of priced)")

net = trig["net_pnl"].to_numpy(dtype=float)
ask = trig["entry_ask"].to_numpy(dtype=float)
fee = trig["fee"].to_numpy(dtype=float)
payout = trig["payout"].to_numpy(dtype=float)

print("\n[main window start-6h .. start-15m]")
print(f"  n={len(net)} median={np.median(net):+.6f} mean={net.mean():+.6f}")
print(f"  hit payout>=0.999: {int((payout >= 0.999).sum())}/{len(net)} = {(payout >= 0.999).mean():.3f}")
print(f"  total net={net.sum():+.6f} per_$staked={net.sum()/ask.sum():+.6f}")
print(f"  net>0: {(net > 0).sum()}/{len(net)} = {(net > 0).mean():.3f}; "
      f"two-sided binomial p vs 0.5 = {binom_two_sided(int((net > 0).sum()), len(net)):.4f}")
print(f"  resolved: {dict(sorted(trig['resolved_prices'].value_counts().items()))}")
print(f"  entry_ask min/median/max = {ask.min():.4f}/{np.median(ask):.4f}/{ask.max():.4f}")

print("\n[sensitivity window start-24h .. start-1h, main-priced rows only]")
sens = priced[priced["triggered_sens"].eq(True)].copy()
sens_net = sens["net_pnl_sens"].to_numpy(dtype=float)
print(f"  n={len(sens_net)} median={np.median(sens_net):+.6f} mean={sens_net.mean():+.6f} "
      f"total={sens_net.sum():+.6f}")
print(f"  hit payout>=0.999: {int((sens['payout'] >= 0.999).sum())}/{len(sens_net)} = "
      f"{(sens['payout'] >= 0.999).mean():.3f}")
print("  per_$staked: not recomputable from matches.csv (entry_ask_sens column omitted); "
      "REPORT.md quotes -0.057802")

print("\n[price bands, same main triggers]")
for label, mask in (
    ("ask<0.3", ask < 0.3),
    ("0.3<=ask<=0.7", (ask >= 0.3) & (ask <= 0.7)),
    ("ask>0.7", ask > 0.7),
):
    b = net[mask]
    print(f"  {label}: n={len(b)} median={np.median(b):+.6f} mean={b.mean():+.6f}")
print("  NOTE: CSV prices are rounded to 6dp; ~11 rows sit exactly on 0.3 and move bands")
print("        versus run_output.txt (246/901/219). Medians match run_output.txt.")

print("\n[date_lag_days <= 2 subset]")
sub = df[df["date_lag_days"] <= 2]
sub_priced = sub[sub["price_a"].notna()]
sub_trig = sub_priced[sub_priced["triggered"].eq(True)]
sub_net = sub_trig["net_pnl"].to_numpy(dtype=float)
print(f"  priced={len(sub_priced)} triggered={len(sub_net)} "
      f"median={np.median(sub_net):+.6f} mean={sub_net.mean():+.6f}")

print("\n[Elo vs market forecast comparison]")
bic = priced[priced["resolved_prices"].isin(["1|0", "0|1"])].copy()
b_elo, b_mkt, l_elo, l_mkt, abs_gap = [], [], [], [], []
elo_worse = elo_better = 0
eps = 1e-15
for _, r in bic.iterrows():
    y = 1.0 if r["resolved_prices"] == "1|0" else 0.0
    pa = float(r["p_model_a"])
    den = float(r["price_a"]) + float(r["price_b"])
    pm = float(r["price_a"]) / den
    be, bm = (pa - y) ** 2, (pm - y) ** 2
    le = -(y * np.log(max(pa, eps)) + (1 - y) * np.log(max(1 - pa, eps)))
    lm = -(y * np.log(max(pm, eps)) + (1 - y) * np.log(max(1 - pm, eps)))
    b_elo.append(be); b_mkt.append(bm); l_elo.append(le); l_mkt.append(lm)
    abs_gap.append(abs(pa - pm))
    if be > bm:
        elo_worse += 1
    elif be < bm:
        elo_better += 1
print(f"  n={len(b_elo)}")
print(f"  Brier Elo={np.mean(b_elo):.6f} market={np.mean(b_mkt):.6f} "
      f"diff={np.mean(b_elo)-np.mean(b_mkt):+.6f}")
print(f"  logloss Elo={np.mean(l_elo):.6f} market={np.mean(l_mkt):.6f} "
      f"diff={np.mean(l_elo)-np.mean(l_mkt):+.6f}")
print(f"  Elo worse={elo_worse} better={elo_better} "
      f"two-sided binomial p={binom_two_sided(elo_worse, len(b_elo)):.4f}")
print(f"  mean |p_model - p_market|={np.mean(abs_gap):.6f}")

print("\n[zero-cost sensitivity: remove both half-spread and fee]")
zero_half = net + 0.01
zero_fee = net + fee
zero_both = net + fee + 0.01
stake_both = ask - 0.01
for label, x, stake in (
    ("half-spread=0", zero_half, ask - 0.01),
    ("fee=0", zero_fee, ask),
    ("half-spread=0 & fee=0", zero_both, stake_both),
):
    lo, med, hi = boot_median(x)
    print(f"  {label}: n={len(x)} median={med:+.6f} (bootstrap 95% {lo:+.6f}..{hi:+.6f}) "
          f"mean={x.mean():+.6f} total={x.sum():+.6f} per_$staked={x.sum()/stake.sum():+.6f}")

print("\n[verdict against the entry's frozen criterion]")
med = float(np.median(net))
verdict = "FAIL" if (len(net) >= 30 and med <= 0) else "NOT FAIL"
print(f"  triggered={len(net)} (>=30) and median={med:+.6f} <= 0 -> {verdict}")
print("  zero-cost median:", f"{np.median(zero_both):+.6f}",
      "-> still <=0" if np.median(zero_both) <= 0 else "-> positive")
