#!/usr/bin/env python3
"""Re-read the live cross-ladder signal cited in the quant-019 entry.

The entry's 1.73x "two ladders disagree" number is a 2026-10-20 snapshot.
This script only refreshes that snapshot (Gamma, free, keyless); it is NOT a
backtest and does not feed the replay. Run: python3 refresh_crosscheck.py
"""
import json
import urllib.request
from datetime import date

UA = {"User-Agent": "python-requests/2.31", "Accept": "application/json"}
GAMMA = "https://gamma-api.polymarket.com"
CDC_PRINT, CDC_DATE = 4410.0, date(2026, 10, 15)
ANCHOR_A_MID = 50.667


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, json.loads(r.read())


def num(s):
    return int(float(str(s).replace("+", "").replace(",", "")
                     .replace("↑", "").replace("k", "000")
                     .replace("12.5000", "12500")))


def mid(m):
    b, a = m.get("bestBid"), m.get("bestAsk")
    if b is not None and a is not None and float(a) > 0:
        return (float(b) + float(a)) / 2
    op = m.get("outcomePrices") or []
    return float(op[0]) if op else None


def ladder(slug):
    st, d = get(f"{GAMMA}/events?slug={slug}")
    e = d[0] if isinstance(d, list) else d
    rows = []
    for m in e.get("markets") or []:
        try:
            n = num(m["threshold"])
        except (KeyError, ValueError, TypeError):
            continue
        p = mid(m)
        if p is not None:
            rows.append((n, p))
    rows.sort()
    return st, e, rows


print(f"CDC print used: {CDC_PRINT:.0f} as of {CDC_DATE} (entry snapshot)")
for slug, end in [
    ("measles-cases-in-uptspt-by-october-31-20260928t160000000z", date(2026, 10, 31)),
    ("measles-cases-in-us-in-2026", date(2026, 12, 31)),
]:
    st, e, rows = ladder(slug)
    print(f"\n[{st}] {slug} endDate={e.get('endDate')}")
    print("  " + "  ".join(f"{n}@{p:.4f}" for n, p in rows))
    days = (end - CDC_DATE).days
    for (n1, p1), (n2, p2) in zip(rows, rows[1:]):
        if p1 >= 0.5 >= p2 and p1 > p2:
            x50 = n1 + (p1 - 0.5) / (p1 - p2) * (n2 - n1)
            f = (x50 - CDC_PRINT) / days
            print(f"  50% level = {x50:.1f} cases on {end} over {days}d "
                  f"-> f={f:.2f}/day; anchor A mid={ANCHOR_A_MID:.2f} "
                  f"-> ratio={ANCHOR_A_MID / f:.2f}x")
            break
    else:
        print("  no 0.5 crossing found in quoted strikes")
