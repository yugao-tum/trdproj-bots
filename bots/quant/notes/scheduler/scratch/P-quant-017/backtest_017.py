#!/usr/bin/env python3
"""P-quant-017: historical tradable-price backtest for the US Apple App Store
weekly rank boards, net of Polymarket taker fees.

Data: CLOB prices-history (10-minute points) for the 8 closed free-board events
that have any history (4 settlement dates x #1/#2).  Prices are last-trade
prices, NOT quotes: there is no public historical order book, so the half-spread
is an explicit assumption, reported for 0.0c / 0.5c / 1.5c.

The 2026 settlement-day Apple chart snapshot cannot be reconstructed (Wayback
has no 2026 captures), so the chart filter in the proposed rule is replaced by a
price-only proxy: at T_entry buy YES of the arm the market currently prices
highest, hold to resolution.  This is an upper bound on what the rule could have
earned, not a replication of it.

Run: python3 backtest_017.py
"""
import json
import pathlib
import statistics
from datetime import datetime, timezone

BASE = pathlib.Path(__file__).resolve().parent
CACHE = BASE / "_cache"
RATE = 0.05  # feeSchedule rate observed on these boards (culture_fees)


def load_history(tok):
    fp = CACHE / f"hist_{tok}.json"
    if not fp.exists():
        return []
    try:
        h = json.loads(fp.read_text()).get("history", [])
    except Exception:  # noqa: BLE001
        return []
    return sorted((int(p["t"]), float(p["p"])) for p in h if "t" in p and "p" in p)


def price_at(hist, ts, max_age=1800):
    """last trade at or before ts, no older than max_age seconds."""
    cand = [p for t, p in hist if ts - max_age <= t <= ts]
    if not cand:
        return None
    return cand[-1]


def real_arms(ev):
    out = []
    for m in ev["markets"]:
        title = (m.get("groupItemTitle") or "").strip()
        if not title or title.lower() == "other" or title.lower().startswith("reserved"):
            continue
        try:
            outs = json.loads(m.get("outcomes") or "[]")
            prs = json.loads(m.get("outcomePrices") or "[]")
        except Exception:  # noqa: BLE001
            continue
        if outs[:1] != ["Yes"] or len(prs) < 2:
            continue
        try:
            yes = float(prs[0])
        except Exception:  # noqa: BLE001
            continue
        toks = json.loads(m.get("clobTokenIds") or "[]")
        if not toks:
            continue
        fee = (m.get("feeSchedule") or {}).get("rate")
        out.append({"title": title, "win": yes > 0.5, "tok": toks[0],
                    "rate": float(fee) if fee is not None else RATE})
    return out


def fmt(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M")


def main():
    slugs = json.loads((CACHE / "kept_slugs.json").read_text())
    events = []
    for slug in slugs:
        fp = CACHE / ("ev_" + slug[:60] + ".json")
        d = json.loads(fp.read_text())[0]
        arms = real_arms(d)
        for a in arms:
            a["hist"] = load_history(a["tok"])
        events.append({"slug": slug, "end": d["endDate"], "arms": arms})

    print("=== P-quant-017 historical price backtest, CLOB 10-min last-trade series ===")
    print("fee rate: 0.05 (Gamma feeSchedule, culture_fees); fee/share = rate*p*(1-p)")
    print("prices = last trade, not quotes; half-spread is an assumption\n")

    # coverage
    for e in events:
        day = e["end"][:10]
        tres = int(datetime.fromisoformat(day + "T16:00:00+00:00").timestamp())
        pts = sum(len(a["hist"]) for a in e["arms"])
        around = [p for a in e["arms"] for t, p in a["hist"] if tres - 3600 <= t <= tres]
        print(f"{e['slug'][:58]:<58} day={day} arms={len(e['arms']):2d} "
              f"pts={pts:4d} points_in_T-60..T={len(around):3d} "
              f"winner={[a['title'] for a in e['arms'] if a['win']]}")

    print("\n--- A. price-only favorite at each entry time (no price filter) ---")
    print("entry  hs    n  win  mean_net  median_net  total_net  avg_entry  avg_payout")
    rows_a = {}
    for minutes_before in (60, 30, 10):
        for hs in (0.0, 0.005, 0.015):
            trades = []
            for e in events:
                day = e["end"][:10]
                tres = int(datetime.fromisoformat(day + "T16:00:00+00:00").timestamp())
                te = tres - minutes_before * 60
                cand = []
                for a in e["arms"]:
                    p = price_at(a["hist"], te)
                    if p is not None:
                        cand.append((p, a))
                if not cand:
                    continue
                p, a = max(cand, key=lambda x: x[0])
                fee = a["rate"] * p * (1 - p)
                net = (1.0 if a["win"] else 0.0) - p - hs - fee
                trades.append({"day": day, "slug": e["slug"], "arm": a["title"],
                               "p": p, "fee": fee, "net": net, "win": a["win"],
                               "cost": p + hs + fee})
            rows_a[(minutes_before, hs)] = trades
            if trades:
                nets = [t["net"] for t in trades]
                print(f"T-{minutes_before:<3d} {hs:.3f} {len(trades):2d}  "
                      f"{sum(t['win'] for t in trades):2d}  {statistics.mean(nets):+.4f}   "
                      f"{statistics.median(nets):+.4f}    {sum(nets):+.4f}     "
                      f"{statistics.mean([t['p'] for t in trades]):.4f}     "
                      f"{statistics.mean([1.0 if t['win'] else 0.0 for t in trades]):.3f}")

    print("\n--- B. trades that satisfy the proposed edge filter cost<=0.98 ---")
    print("entry  hs    n  win  mean_net  median_net  total_net")
    for minutes_before in (60, 30, 10):
        for hs in (0.0, 0.005, 0.015):
            trades = [t for t in rows_a[(minutes_before, hs)] if t["cost"] <= 0.98]
            if trades:
                nets = [t["net"] for t in trades]
                print(f"T-{minutes_before:<3d} {hs:.3f} {len(trades):2d}  "
                      f"{sum(t['win'] for t in trades):2d}  {statistics.mean(nets):+.4f}   "
                      f"{statistics.median(nets):+.4f}    {sum(nets):+.4f}")
            else:
                print(f"T-{minutes_before:<3d} {hs:.3f}  0   0       -          -         -")

    print("\n--- B2. chart proxy: favourite already >=0.90 AND cost<=0.98 ---")
    print("entry  hs    n  win  mean_net  total_net  trades")
    for minutes_before in (60, 30, 10):
        for hs in (0.0, 0.005, 0.015):
            trades = [t for t in rows_a[(minutes_before, hs)]
                      if t["p"] >= 0.90 and t["cost"] <= 0.98]
            if trades:
                nets = [t["net"] for t in trades]
                detail = "; ".join(f"{t['day']}:{t['arm'][:14]} p={t['p']:.4f} "
                                   f"net={t['net']:+.4f}" for t in trades)
                print(f"T-{minutes_before:<3d} {hs:.3f} {len(trades):2d}  "
                      f"{sum(t['win'] for t in trades):2d}  {statistics.mean(nets):+.4f}   "
                      f"{sum(nets):+.4f}   {detail}")
            else:
                print(f"T-{minutes_before:<3d} {hs:.3f}  0   0       -         -        -")

    print("\n--- C. per-event detail, T-10, hs=0.015, no filter ---")
    print("day        board  arm                          p      fee    cost   win   net")
    for t in rows_a[(10, 0.015)]:
        board = "1-free" if t["slug"].startswith("1-") else "2-free"
        print(f"{t['day']} {board:<7} {t['arm'][:28]:<28} {t['p']:.4f} {t['fee']:.5f} "
              f"{t['cost']:.4f} {str(t['win']):<5} {t['net']:+.4f}")

    print("\n--- D. per-date aggregate, T-10, hs=0.015, no filter ---")
    by_day = {}
    for t in rows_a[(10, 0.015)]:
        by_day.setdefault(t["day"], []).append(t)
    for day in sorted(by_day):
        nets = [t["net"] for t in by_day[day]]
        print(f"{day}  boards={len(nets)}  total_net={sum(nets):+.4f}  "
              f"mean_net={statistics.mean(nets):+.4f}  wins={sum(t['win'] for t in by_day[day])}")

    print("\n--- E. what price did the favourite already trade at? distribution ---")
    ps = [t["p"] for t in rows_a[(10, 0.015)]]
    if ps:
        print("T-10 favourite price min/median/max:",
              f"{min(ps):.4f}/{statistics.median(ps):.4f}/{max(ps):.4f}")
        print("count p>=0.98:", sum(1 for p in ps if p >= 0.98),
              "| 0.95<=p<0.98:", sum(1 for p in ps if 0.95 <= p < 0.98),
              "| p<0.95:", sum(1 for p in ps if p < 0.95))

    print("\n--- F. breakeven arithmetic for a p=0.98 favourite ---")
    for p in (0.95, 0.97, 0.98, 0.99):
        fee = RATE * p * (1 - p)
        print(f"p={p:.2f} fee={fee:.5f} gross_up={1-p:.4f} "
              f"net_after_fee={1-p-fee:+.5f} net_after_fee_and_0.5c={1-p-fee-0.005:+.5f} "
              f"net_after_fee_and_1.5c={1-p-fee-0.015:+.5f}")


if __name__ == "__main__":
    main()
