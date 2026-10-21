#!/usr/bin/env python3
"""Offline summary of the quant-014 executable-price replay.

Reads the frozen per-leg file `events.csv` (produced by replay.py / q014_hist.py
from data-api per-trade fills) and reproduces every number quoted in
replay/quant-014/SUMMARY.md.  No network, no cache, no binaries.

Run:  python3 summarize.py
"""
import csv
import math
import random
import statistics
from collections import Counter, defaultdict

CSV = "events.csv"
FEE_RATE = 0.04
HALF_SPREAD = 0.01
BOOT_N = 10000
BOOT_SEED = 20261020
DEV_END = "2026-06-30"          # 70% time split; OOS starts 2026-07-01
CAPITAL = 5000.0
SHARES = 100                    # entry's per-leg cap


def rows():
    with open(CSV, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def median(xs):
    return statistics.median(xs) if xs else float("nan")


def pct(xs, q):
    s = sorted(xs)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def brier(ps, ys):
    return mean([(p - y) ** 2 for p, y in zip(ps, ys)])


def leg_stats(label, rs, fee_zero=False):
    nets = [float(r["net_per_share"]) + (float(r["fee"]) if fee_zero else 0.0) for r in rs]
    costs = [float(r["exec_price"]) for r in rs]
    print("%-38s legs=%3d  mean=%+.5f  median=%+.5f  hit=%.3f  total=%+.3f  per_$1=%+.4f"
          % (label, len(nets), mean(nets), median(nets),
             sum(1 for n in nets if n > 0) / len(nets) if nets else float("nan"),
             sum(nets), sum(nets) / sum(costs) if sum(costs) else float("nan")))
    return nets


def daily_subset(rs, lo_date=None, hi_date=None):
    out = []
    for r in rs:
        if r["event_type"] != "daily_updown" or not r["p_market_yes"]:
            continue
        if lo_date and r["resolution_date"] < lo_date:
            continue
        if hi_date and r["resolution_date"] > hi_date:
            continue
        if abs(float(r["p_market_yes"]) - 0.5) >= 0.10:
            out.append(r)
    return out


def daily_direction(rs, mode, fee_zero=False):
    nets, gross, fees = [], [], []
    for r in rs:
        p, y = float(r["p_market_yes"]), float(r["outcome_yes"])
        side_yes = (p < 0.5) if mode == "FADE" else (p > 0.5)
        exec_p = (p + HALF_SPREAD) if side_yes else (1 - p + HALF_SPREAD)
        fee = FEE_RATE * exec_p * (1 - exec_p)
        payoff = y if side_yes else 1 - y
        mid_cost = p if side_yes else 1 - p
        nets.append(payoff - exec_p - (0.0 if fee_zero else fee))
        gross.append(payoff - mid_cost)
        fees.append(fee)
    return nets, gross


def boot_ci(vals_by_week):
    weeks = sorted(vals_by_week)
    rng = random.Random(BOOT_SEED)
    k = len(weeks)
    means = []
    for _ in range(BOOT_N):
        pool = []
        for j in rng.choices(range(k), k=k):
            pool.extend(vals_by_week[weeks[j]])
        means.append(sum(pool) / len(pool))
    return pct(means, 2.5), pct(means, 97.5), k


def main():
    rs = rows()
    trig = [r for r in rs if r["triggered"] == "1"]
    print("=" * 96)
    print("quant-014 replay summary (offline from events.csv; fee=0.04/side unless stated)")
    print("=" * 96)
    print("legs=%d  events=%d  triggered_legs=%d  triggered_events=%d"
          % (len(rs), len({r["event_slug"] for r in rs}), len(trig),
             len({r["event_slug"] for r in trig})))
    print("event types: %s" % dict(Counter(r["event_type"] for r in rs)))
    print("triggered by type: %s" % dict(Counter(r["event_type"] for r in trig)))
    print("YES/NO: %s" % dict(Counter(r["side"] for r in trig)))
    print("date span: %s..%s" % (min(r["resolution_date"] for r in rs),
                                 max(r["resolution_date"] for r in rs)))

    print("\n--- PRIMARY: entry rule (model vs tradable, 2x(fee+half-spread)), decision close-6h ---")
    leg_stats("all triggered legs (fee 0.04)", trig)
    leg_stats("all triggered legs (fee 0)", trig, fee_zero=True)
    for t in ("daily_updown", "monthly_above", "monthly_close"):
        leg_stats("  %s (fee 0.04)" % t, [r for r in trig if r["event_type"] == t])
        leg_stats("  %s (fee 0)" % t, [r for r in trig if r["event_type"] == t], fee_zero=True)

    print("\n--- DAILY |p6-0.5|>=0.10 subset: FADE (model 0.5) vs FOLLOW (entry's original test) ---")
    sub = daily_subset(rs)
    for mode in ("FADE", "FOLLOW"):
        nets, gross = daily_direction(sub, mode)
        nets0, _ = daily_direction(sub, mode, fee_zero=True)
        print("%-8s legs=%3d  gross=%+.5f  net(fee .04)=%+.5f  net(fee 0)=%+.5f  "
              "median=%+.5f  hit=%.3f  total=%+.3f"
              % (mode, len(nets), mean(gross), mean(nets), mean(nets0),
                 median(nets), sum(1 for n in nets if n > 0) / len(nets), sum(nets)))

    by_week = defaultdict(list)
    for r in sub:
        p, y = float(r["p_market_yes"]), float(r["outcome_yes"])
        side_yes = p < 0.5
        exec_p = (p + HALF_SPREAD) if side_yes else (1 - p + HALF_SPREAD)
        fee = FEE_RATE * exec_p * (1 - exec_p)
        by_week[r["iso_week"]].append((y if side_yes else 1 - y) - exec_p - fee)
    lo, hi, nw = boot_ci(by_week)
    print("FADE weekly-cluster bootstrap 95%% CI [%+.5f,%+.5f] over %d ISO weeks (seed %d)"
          % (lo, hi, nw, BOOT_SEED))

    print("\n--- OUT-OF-SAMPLE TIME SPLIT (dev <= %s, OOS >= 2026-07-01) ---" % DEV_END)
    for label, cond in (("dev", lambda d: d <= DEV_END), ("OOS", lambda d: d > DEV_END)):
        part = [r for r in trig if cond(r["resolution_date"])]
        leg_stats("%s all triggered (fee .04)" % label, part)
        sub2 = daily_subset(rs, hi_date=DEV_END) if label == "dev" else daily_subset(rs, lo_date="2026-07-01")
        for mode in ("FADE", "FOLLOW"):
            nets, _ = daily_direction(sub2, mode)
            print("  %s daily %-6s n=%3d  net=%+.5f  median=%+.5f  total=%+.3f"
                  % (label, mode, len(nets), mean(nets), median(nets), sum(nets)))

    print("\n--- CALIBRATION / BRIER (daily Up/Down, p_model = 0.5) ---")
    daily = [r for r in rs if r["event_type"] == "daily_updown" and r["p_market_yes"]]
    for label, cond in (("all", lambda d: True), ("dev", lambda d: d <= DEV_END),
                        ("OOS", lambda d: d > DEV_END)):
        part = [r for r in daily if cond(r["resolution_date"])]
        ys = [float(r["outcome_yes"]) for r in part]
        pm = [float(r["p_model"]) for r in part]
        mk = [float(r["p_market_yes"]) for r in part]
        print("%-4s n=%3d  Brier model=%.5f  const 0.50=%.5f  const 0.53=%.5f  market=%.5f"
              % (label, len(part), brier(pm, ys), brier([0.5] * len(ys), ys),
                 brier([0.53] * len(ys), ys), brier(mk, ys)))

    print("\n--- CONTRIBUTION TO 5,000 USDT (100 shares/triggered leg, one sample year) ---")
    for label, fee_zero in (("fee 0.04", False), ("fee 0", True)):
        total = sum(float(r["net_per_share"]) + (float(r["fee"]) if fee_zero else 0) for r in trig)
        print("%-8s total net/share=%+.3f -> 100 shares=%+.1f USDT -> %.2f%% of 5,000"
              % (label, total, total * SHARES, total * SHARES / CAPITAL * 100.0))

    print("\n--- FROZEN FAILURE CRITERION ---")
    nets, _ = daily_direction(sub, "FADE")
    b_model = brier([float(r["p_model"]) for r in daily], [float(r["outcome_yes"]) for r in daily])
    b53 = brier([0.53] * len(daily), [float(r["outcome_yes"]) for r in daily])
    print("criterion #1 daily taker subset net mean <= 0: mean=%+.5f -> %s"
          % (mean(nets), "TRIGGERED" if mean(nets) <= 0 else "not triggered"))
    print("criterion #3 model Brier worse than 0.53 on >=30 events: %.5f vs %.5f -> %s"
          % (b_model, b53, "TRIGGERED" if b_model > b53 and len(daily) >= 30 else "not triggered"))
    print("VERDICT: FAIL (criterion #3 full sample; OOS net and every ladder leg negative)")


if __name__ == "__main__":
    main()
