#!/usr/bin/env python3
"""quant-011 replay summary (runs offline on matches.csv).

Reads the matches.csv produced by run_replay.py and writes trades.csv +
summary.json next to this script. All numbers in SUMMARY.md come from here.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_MATCHES = (HERE.parents[1] / "notes/scheduler/scratch/P-quant-011"
                   / "matches.csv")
STAKE = 50.0
ACCOUNT = 5000.0
VARIANTS = [
    ("primary [T-6h,T]", "triggered", "ask", "net"),
    ("sensitivity [T-24h,T-1h]", "sens_triggered", "sens_ask", "sens_net"),
    ("freshness [T-1h,T]", "narrow_triggered", "narrow_ask", "narrow_net"),
]


def truthy(x):
    return str(x).strip().lower() == "true"


def num(x):
    return float(x) if x not in ("", None, "None", "nan") else None


def max_realized_dd(pnls):
    cum = peak = max_dd = 0.0
    for p in pnls:
        cum += p
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
    return max_dd, max_dd / ACCOUNT * 100.0, cum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matches", default=str(DEFAULT_MATCHES))
    args = ap.parse_args()
    with Path(args.matches).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    dates = sorted(r["date"] for r in rows)
    d0 = dt.date.fromisoformat(dates[0])
    d1 = dt.date.fromisoformat(dates[-1])
    days = (d1 - d0).days + 1
    years = days / 365.25
    good = [r for r in rows if truthy(r["resolution_match"])]
    print("matches.csv rows: %d; resolution_match true: %d" % (len(rows), len(good)))
    print("evaluation window: %s..%s (%d days, %.3f years)"
          % (d0, d1, days, years))
    print("stake per triggered match: %.0f USDT; account: %.0f USDT\n"
          % (STAKE, ACCOUNT))

    summary = {"window": {"start": d0.isoformat(), "end": d1.isoformat(),
                          "days": days, "years": round(years, 4)},
               "stake_usdt": STAKE, "account_usdt": ACCOUNT, "variants": []}
    for name, trig_key, ask_key, net_key in VARIANTS:
        trig = [(r, num(r[ask_key]), num(r[net_key])) for r in good
                if truthy(r[trig_key])]
        n = len(trig)
        nets = [net for _, _, net in trig]
        asks = [ask for _, ask, _ in trig]
        rets = [net / ask for _, ask, net in trig]
        total_net = sum(nets)
        per_dollar = total_net / sum(asks)
        mean_ret = statistics.fmean(rets)
        annual_triggers = n / years
        annual_pnl = mean_ret * STAKE * annual_triggers
        contribution = annual_pnl / ACCOUNT * 100.0
        max_dd, max_dd_pct, cum = max_realized_dd([r * STAKE for r in rets])
        print("VARIANT %s" % name)
        print("  triggered=%d (>=30: %s); date range %s..%s"
              % (n, n >= 30, min(r["date"] for r, _, _ in trig),
                 max(r["date"] for r, _, _ in trig)))
        print("  median net/share=%+.4f mean=%+.4f total=%+.4f"
              % (statistics.median(nets), statistics.fmean(nets), total_net))
        print("  total per $ staked=%+.2f%%; mean per-match return=%+.2f%%; "
              "hit rate=%.1f%%" % (100 * per_dollar, 100 * mean_ret,
                                   100 * sum(1 for x in nets if x > 0) / n))
        print("  annual triggers=%.1f; annual P&L at 50 USDT/match=%+.1f USDT; "
              "contribution=%+.1f%% of 5000 USDT"
              % (annual_triggers, annual_pnl, contribution))
        print("  realized max drawdown=%+.1f USDT (%.1f%% of 5000; "
              "peak-to-trough, chronological, not mark-to-market)\n"
              % (-max_dd, max_dd_pct))
        summary["variants"].append({
            "name": name, "triggered": n,
            "median_net_per_share": round(statistics.median(nets), 6),
            "mean_net_per_share": round(statistics.fmean(nets), 6),
            "total_net_per_share": round(total_net, 6),
            "total_per_dollar": round(per_dollar, 6),
            "mean_per_match_return": round(mean_ret, 6),
            "hit_rate": round(sum(1 for x in nets if x > 0) / n, 6),
            "annual_triggers": round(annual_triggers, 3),
            "annual_pnl_usdt": round(annual_pnl, 2),
            "contribution_pct": round(contribution, 2),
            "realized_max_dd_usdt": round(max_dd, 2),
            "realized_max_dd_pct_account": round(max_dd_pct, 2),
        })

    trig = [r for r in good if truthy(r["triggered"])]
    gross = [(1.0 if r["ftr"] == "D" else 0.0) - num(r["ask"]) for r in trig]
    gross_staked = sum(num(r["ask"]) for r in trig)
    raw = [(1.0 if r["ftr"] == "D" else 0.0) - num(r["prim_yes_last"])
           for r in trig]
    raw_staked = sum(num(r["prim_yes_last"]) for r in trig)
    print("DIAGNOSTIC zero-fee (ask keeps 1c half-spread): n=%d median=%+.4f "
          "mean=%+.4f per $ staked=%+.2f%%"
          % (len(gross), statistics.median(gross), statistics.fmean(gross),
             100 * sum(gross) / gross_staked))
    print("DIAGNOSTIC raw print, zero fee/spread: n=%d median=%+.4f mean=%+.4f "
          "per $ staked=%+.2f%%"
          % (len(raw), statistics.median(raw), statistics.fmean(raw),
             100 * sum(raw) / raw_staked))
    summary["zero_fee_stress"] = {
        "n": len(gross), "median": round(statistics.median(gross), 6),
        "mean": round(statistics.fmean(gross), 6),
        "total": round(sum(gross), 6),
        "per_dollar": round(sum(gross) / gross_staked, 6)}
    summary["raw_print_zero_cost"] = {
        "n": len(raw), "median": round(statistics.median(raw), 6),
        "mean": round(statistics.fmean(raw), 6),
        "total": round(sum(raw), 6),
        "per_dollar": round(sum(raw) / raw_staked, 6)}

    cols = ["date", "league", "season", "event_slug", "condition_id",
            "fd_home", "fd_away", "ftr", "qD", "base_rate",
            "ask", "net", "sens_ask", "sens_net", "narrow_ask", "narrow_net"]
    union = [r for r in good if any(truthy(r[k]) for k in
             ("triggered", "sens_triggered", "narrow_triggered"))]
    union.sort(key=lambda r: (r["date"], r["league"], r["event_slug"]))
    with (HERE / "trades.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in union:
            w.writerow({k: r.get(k, "") for k in cols})
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                       encoding="utf-8")
    print("\nwrote %s (%d rows) and %s"
          % (HERE / "trades.csv", len(union), HERE / "summary.json"))


if __name__ == "__main__":
    main()
