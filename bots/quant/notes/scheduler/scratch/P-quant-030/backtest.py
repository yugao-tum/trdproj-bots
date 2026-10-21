"""Historical tradable-price backtest, net of the GUIDE section 8 taker fee.

Rules being tested are the pre-registered rules in
bots/quant/entries/quant-030-kpi-bracket-monthly-nowcast.md (section "规则 2").

Entry price = an actual taker print from data-api (side = taker direction),
not a mid, not a daily close, not the opposite side's resting quote.
Net/share = settlement(1) - entry - fee - assumed half-spread, where
fee = rate * p * (1-p) per share (GUIDE section 8), rate = 0.04.
"""
import json, os, datetime

CACHE = "bots/quant/notes/scheduler/scratch/P-quant-030/_cache"
RATE = 0.04


def trades(slug, bracket):
    e = json.load(open(os.path.join(CACHE, f"event_{slug}.json")))
    for m in e["markets"]:
        if m.get("groupItemTitle") == bracket:
            return m, json.load(open(os.path.join(CACHE, f"trades_{m['conditionId']}.json")))
    raise KeyError(bracket)


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def first_after(slug, bracket, after, side=None, outcome=None):
    m, tr = trades(slug, bracket)
    sel = []
    for t in tr:
        if fmt(t["timestamp"]) < after:
            continue
        if side and t["side"] != side:
            continue
        if outcome and t.get("outcome") != outcome:
            continue
        sel.append(t)
    sel.sort(key=lambda x: x["timestamp"])
    return sel[0] if sel else None


def calc(price, size, settle, hs):
    fee = RATE * price * (1 - price)
    net = settle - price - fee - hs
    return fee, net, net * size, net / price


def row(label, t, settle, size_cap=None, hs_list=(0.0, 0.01, 0.03, 0.05)):
    if t is None:
        print(f"{label}: no taker print")
        return
    size = min(t["size"], size_cap) if size_cap else t["size"]
    print(f"{label}: {fmt(t['timestamp'])} taker {t['side']} {t.get('outcome')} "
          f"@{t['price']:.6f} size={t['size']:.2f} (used {size:.2f})")
    for hs in hs_list:
        fee, net, tot, ret = calc(t["price"], size, settle, hs)
        print(f"   half-spread {hs*100:.0f}c: fee/share={fee:.6f} net/share={net:+.6f} "
              f"total={tot:+.2f} USDC return-on-cost={ret*100:+.1f}%")


print("=== 5 same-caliber cases, pre-registered rule ===")
print("\n[1] TSM Q2 revenue above-41 -> NO; release 2026-07-13 05:30:28Z (TSMC dateModified)")
t = first_after("will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419",
                "$41B", "2026-07-13 05:30:28", side="BUY", outcome="No")
row("  first taker BUY NO after release", t, 1.0)

print("\n[2] TSM above-40 -> YES (nowcast 40.2 is only 0.5% from 40; fails 2% distance)")
t = first_after("will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419",
                "$40B", "2026-07-13 05:30:28", side="BUY", outcome="Yes")
row("  first taker BUY YES after release", t, 1.0)

print("\n[3] Boeing Q1 deliveries above-140 -> YES (release time not published; 18:26 is date-consistent only)")
t = first_after("boeing-airplane-deliveries-above-in-q1", "140", "2026-04-14 00:00:00",
                side="BUY", outcome="Yes")
row("  first taker BUY YES on release date", t, 1.0, size_cap=29)

print("\n[4] Costco 6.5-7.5 -> YES; first print after April sales is taker BUY NO (basket), not a YES ask")
t = first_after("costco-q3-us-adjusted-comparable-sales-growth", "6.5%–7.5%",
                "2026-05-06 00:00:00", side="BUY", outcome="No")
row("  first bracket print (BUY NO, 2026-05-22)", t, 0.0)
t = first_after("costco-q3-us-adjusted-comparable-sales-growth", "6.5%–7.5%",
                "2026-05-06 00:00:00", side="BUY", outcome="Yes")
row("  first taker BUY YES (2026-05-28, after earnings release)", t, 1.0)

print("\n[5] Delta Q2 83-85 -> YES (fails 50-share liquidity gate)")
t = first_after("delta-dal-q2-passenger-load-factor", "83%–85%",
                "2026-07-02 10:07:00", side="BUY", outcome="Yes")
row("  first taker BUY YES", t, 1.0, size_cap=50)

print("\n[6] UAL Q2: naive Apr+May nowcast 82.3 -> '<83' (actual 83.4, loses)")
t = first_after("united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130",
                "<83%", "2026-06-20 00:00:00", side="BUY", outcome="Yes")
row("  first taker BUY YES in <83", t, 0.0)
