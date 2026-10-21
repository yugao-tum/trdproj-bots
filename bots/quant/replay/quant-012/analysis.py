#!/usr/bin/env python3
"""quant-012 replay: extra statistics on the canonical replay output.

Reads trades.csv / events.csv produced by replay.py (no network) and adds:
  * event-clustered bootstrap CI of the mean net PnL per share
  * per-event distribution and hit rate
  * delay buckets (fill age after decision time)
  * pre/post price log-loss comparison on the SAME events that q012-hist could
    price fully before the window (join by event_slug, read-only)

Run: python3 analysis.py | tee analysis_output.txt
"""

import csv
import random
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
MERGED = HERE.parents[1] / "notes" / "q012-hist"
random.seed(20261021)


def load(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def boot_event_ci(rows, key, n=10000):
    by_ev = {}
    for r in rows:
        by_ev.setdefault(r["event_slug"], []).append(float(r[key]))
    evs = list(by_ev.values())
    means = []
    for _ in range(n):
        sample = [evs[random.randrange(len(evs))] for _ in evs]
        vals = [x for ev in sample for x in ev]
        means.append(sum(vals) / len(vals))
    means.sort()
    return sum(x for ev in evs for x in ev) / sum(len(ev) for ev in evs), means[int(0.025 * n)], means[int(0.975 * n)]


def main():
    trades = load(HERE / "trades.csv")
    events = load(HERE / "events.csv")
    print("=" * 78)
    print("quant-012 replay extra statistics")
    print("=" * 78)
    print(f"rows: {len(trades)} fills over {len({r['event_slug'] for r in trades})} events")

    mean, lo, hi = boot_event_ci(trades, "net_per_share")
    print("\n[1] net PnL per NO share (fee 0.05, 1 cent concession)")
    print(f"    mean = {mean:+.4f}; event-clustered bootstrap 95% CI = [{lo:+.4f}, {hi:+.4f}]")
    print(f"    95% CI includes zero: {'YES' if lo <= 0 <= hi else 'NO'}")

    by_ev = {}
    for r in trades:
        by_ev.setdefault(r["event_slug"], []).append(r)
    ev_pnl = []
    for slug, rows in by_ev.items():
        ev_pnl.append(sum(float(r["net_per_share"]) for r in rows))
    pos = sum(1 for x in ev_pnl if x > 0)
    print(f"\n[2] event totals (1 share per bracket): {len(ev_pnl)} events, "
          f"positive {pos}, negative {len(ev_pnl) - pos}")
    print(f"    median event total = {statistics.median(ev_pnl):+.4f} USDT/share-lot")
    print(f"    mean event total   = {statistics.mean(ev_pnl):+.4f}")
    print(f"    worst event        = {min(ev_pnl):+.4f}; best = {max(ev_pnl):+.4f}")

    print("\n[3] fill delay after decision time t0")
    for name, cond in (
        ("<= 6h", lambda d: d <= 6),
        ("6h..24h", lambda d: 6 < d <= 24),
        ("24h..72h", lambda d: 24 < d <= 72),
        ("> 72h", lambda d: d > 72),
    ):
        rows = [r for r in trades if cond(float(r["delay_h"]))]
        if rows:
            tot = sum(float(r["net_per_share"]) for r in rows)
            st = sum(float(r["no_entry"]) for r in rows)
            print(f"    {name:10s} n={len(rows):3d} mean={tot / len(rows):+.4f} "
                  f"total={tot:+.4f} = {tot / st * 100:+.2f}% of notional")

    print("\n[4] month split (1 share each)")
    by_month = {}
    for r in trades:
        by_month.setdefault(r["fill_utc"][:7], []).append(r)
    for m in sorted(by_month):
        rows = by_month[m]
        tot = sum(float(r["net_per_share"]) for r in rows)
        st = sum(float(r["no_entry"]) for r in rows)
        print(f"    {m} n={len(rows):3d} total={tot:+.4f} = {tot / st * 100:+.2f}%")

    print("\n[5] log loss on the SAME 29 events q012-hist priced fully before t0")
    if (MERGED / "events.csv").exists():
        merged = {r["event_slug"]: r for r in load(MERGED / "events.csv")}
        matched = []
        for r in events:
            m = merged.get(r["event_slug"])
            if not m or not m["model_logloss"] or not r["model_logloss"]:
                continue
            matched.append((r, m))
        if matched:
            post_model = statistics.mean(float(r["model_logloss"]) for r, _ in matched)
            post_market = statistics.mean(float(r["market_logloss"]) for r, _ in matched)
            pre_model = statistics.mean(float(m["model_logloss"]) for _, m in matched)
            pre_market = statistics.mean(float(m["market_logloss"]) for _, m in matched)
            print(f"    events = {len(matched)}")
            print(f"    pre-window price : model {pre_model:.4f} vs market {pre_market:.4f}")
            print(f"    post-t0 price    : model {post_model:.4f} vs market {post_market:.4f}")
        else:
            print("    no overlap")
    else:
        print("    notes/q012-hist/events.csv not found")

    print("\n[6] fee sensitivity and notional")
    st = sum(float(r["no_entry"]) for r in trades)
    print(f"    notional (1 share each) = {st:.4f} USDT")
    print(f"    net fee 0.05 = {sum(float(r['net_per_share']) for r in trades):+.4f} "
          f"({sum(float(r['net_per_share']) for r in trades) / st * 100:+.2f}%)")
    print(f"    net fee 0    = {sum(float(r['net_per_share_fee0']) for r in trades):+.4f} "
          f"({sum(float(r['net_per_share_fee0']) for r in trades) / st * 100:+.2f}%)")


if __name__ == "__main__":
    main()
