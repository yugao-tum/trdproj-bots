#!/usr/bin/env python3
"""quant-030 replay: quarterly-KPI brackets, entry at data-api taker prints.

Run from the repository root:
    python3 bots/quant/replay/quant-030/replay.py

Data (free, keyless, accessed 2026-10-22):
  Gamma events: https://gamma-api.polymarket.com/events?slug=<slug>
  data-api:     https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=N

Raw JSON is cached under notes/scheduler/scratch/P-quant-030/_cache/ (gitignored),
so the repository only keeps this script and the printed table.

Parameters
  fee rate             0.04 of notional, fee/share = 0.04 * p * (1-p)  (GUIDE section 8)
  half-spread          0.01 USDC/share base; 0.03 and 0.05 stress
  entry                first taker print AFTER the information release, side/outcome as listed
  size                 the print's own size (capped at 29 shares for Boeing, 50 for DAL)
  settlement           1 if the bought outcome resolved YES, else 0
  strict rule          >=2% distance from a threshold, >=0.5pp from a bracket edge,
                       event volume >=20k, market volume >=2k, two >=50-share prints/24h
  relaxed variant      distance lowered from 2.0% to 1.9%; all other filters unchanged
"""
import csv
import datetime
import json
import os
import time

import requests

CACHE = "bots/quant/notes/scheduler/scratch/P-quant-030/_cache"
RATE = 0.04
HALF_SPREADS = (0.0, 0.01, 0.03, 0.05)
CSV_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trades.csv")

CASES = [
    dict(label="TSM Q2 above-41 -> NO", slug="will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419",
         bracket="$41B", release="2026-07-13 05:30:28", side="BUY", outcome="No", settle=1.0,
         size_cap=None, status="relaxed-only: distance 1.95% < 2%"),
    dict(label="TSM Q2 above-40 -> YES", slug="will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419",
         bracket="$40B", release="2026-07-13 05:30:28", side="BUY", outcome="Yes", settle=1.0,
         size_cap=None, status="excluded: distance 0.5%"),
    dict(label="Boeing Q1 above-140 -> YES", slug="boeing-airplane-deliveries-above-in-q1",
         bracket="140", release="2026-04-14 00:00:00", side="BUY", outcome="Yes", settle=1.0,
         size_cap=29, status="excluded: quarterly data, release time unpublished"),
    dict(label="Costco 6.5-7.5 -> YES", slug="costco-q3-us-adjusted-comparable-sales-growth",
         bracket="6.5%–7.5%", release="2026-05-06 00:00:00", side="BUY", outcome="Yes", settle=1.0,
         size_cap=None, status="excluded: first YES print is after the earnings release (upper bound only)"),
    dict(label="DAL Q2 83-85 -> YES", slug="delta-dal-q2-passenger-load-factor",
         bracket="83%–85%", release="2026-07-02 10:07:00", side="BUY", outcome="Yes", settle=1.0,
         size_cap=50, status="excluded: 37.55 shares < 50-share gate, BTS release time unpublished"),
    dict(label="UAL Q2 <83 (naive) -> YES", slug="united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130",
         bracket="<83%", release="2026-06-20 00:00:00", side="BUY", outcome="Yes", settle=0.0,
         size_cap=None, status="counterexample: naive partial-month nowcast picks the wrong bracket"),
]


def _get(url, params, path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    r = requests.get(url, params=params, timeout=40)
    r.raise_for_status()
    data = r.json()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return data


def event(slug):
    data = _get("https://gamma-api.polymarket.com/events", {"slug": slug},
                os.path.join(CACHE, f"event_{slug}.json"))
    return data[0] if isinstance(data, list) else data


def trades(condition_id):
    path = os.path.join(CACHE, f"trades_{condition_id}.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    out, offset = [], 0
    while offset < 40000:
        r = requests.get("https://data-api.polymarket.com/trades",
                         params={"market": condition_id, "limit": 1000, "offset": offset}, timeout=40)
        if r.status_code != 200:
            break
        chunk = r.json()
        if not chunk:
            break
        out += chunk
        offset += len(chunk)
        if len(chunk) < 1000:
            break
        time.sleep(0.05)
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    return out


def stamp(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def first_print(case):
    ev = event(case["slug"])
    market = next(m for m in ev["markets"] if m.get("groupItemTitle") == case["bracket"])
    rows = [t for t in trades(market["conditionId"])
            if stamp(t["timestamp"]) >= case["release"]
            and t["side"] == case["side"] and t.get("outcome") == case["outcome"]]
    rows.sort(key=lambda t: t["timestamp"])
    return ev, market, (rows[0] if rows else None)


def net(price, size, settle, half_spread):
    fee = RATE * price * (1 - price)
    per_share = settle - price - fee - half_spread
    return fee, per_share, per_share * size, per_share / price


def main():
    print("quant-030 replay | fee=0.04*p*(1-p) | half-spread 0/1/3/5 cents | data-api taker prints")
    print("strict pre-registered rule: 0 eligible trades in the five same-caliber events")
    print("relaxed variant (2.0% -> 1.9% distance): 1 trade, TSM above-41\n")
    rows = []
    for case in CASES:
        ev, market, trade = first_print(case)
        print(f"[{case['label']}] {case['status']}")
        print(f"  event volume={ev.get('volume')} market volume={market.get('volume')} "
              f"settled={market.get('outcomePrices')} n_trades={len(trades(market['conditionId']))}")
        if not trade:
            print("  no taker print after release\n")
            continue
        size = min(trade["size"], case["size_cap"]) if case["size_cap"] else trade["size"]
        print(f"  print {stamp(trade['timestamp'])} taker {trade['side']} {trade.get('outcome')} "
              f"@{trade['price']:.6f} size={trade['size']:.2f} used={size:.2f}")
        for hs in HALF_SPREADS:
            fee, per_share, total, ret = net(trade["price"], size, case["settle"], hs)
            print(f"    half-spread {hs * 100:.0f}c: fee/share={fee:.6f} net/share={per_share:+.6f} "
                  f"total={total:+.2f} USDC return-on-cost={ret * 100:+.1f}%")
            if hs == 0.01:
                rows.append({
                    "case": case["label"], "event_slug": case["slug"], "bracket": case["bracket"],
                    "release_utc": case["release"], "print_utc": stamp(trade["timestamp"]),
                    "side": trade["side"], "outcome": trade.get("outcome"),
                    "price": f"{trade['price']:.6f}", "size_used": f"{size:.2f}",
                    "settle": f"{case['settle']:.0f}", "fee_per_share": f"{fee:.6f}",
                    "half_spread": "0.01", "net_per_share": f"{per_share:.6f}",
                    "net_total_usdc": f"{total:.2f}", "status": case["status"],
                })
        print()
    with open(CSV_OUT, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {CSV_OUT} ({len(rows)} rows, half-spread 1c)")


if __name__ == "__main__":
    main()
