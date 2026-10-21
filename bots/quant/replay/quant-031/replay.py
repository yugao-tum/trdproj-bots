#!/usr/bin/env python3
"""Historical tradable-print replay for quant-031 (AAA daily gas bracket).

Run from the repo root:
    python3 bots/quant/replay/quant-031/replay.py
    python3 bots/quant/replay/quant-031/replay.py --write-trades

Data (free, keyless):
  - Gamma events: https://gamma-api.polymarket.com/events?series_id=12954&limit=100
  - data-api trades: https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=0
  - Wayback decision snapshots: listed in decision_points.csv (one URL per event)

Parameters:
  - decision = earliest archived AAA snapshot on the event day with
    Price as of == event day and Yesterday Avg. == prior day Current Avg.
    (the archived timestamps are in decision_points.csv; the replay does not
    re-download Wayback, which is intermittently unavailable)
  - fill = first actual YES BUY print at/after decision and before endDate
  - fee = 0.04 * p * (1 - p), taker, as in the closed markets' feeSchedule
  - extra half-spread = 0.005 per share
  - hold to settlement (YES pays 1)
  - budget = 250 USDC per event, capped by the print's size
  - variants: limit <= 0.95 (the entry's rule), <= 0.99, any price
"""

import argparse
import csv
import datetime as dt
import json
import os
import time
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
GAMMA = "https://gamma-api.polymarket.com/events?series_id=12954&limit=100"
TRADES = "https://data-api.polymarket.com/trades?market={cid}&limit=1000&offset={off}"
UA = {"User-Agent": "Mozilla/5.0 (research; quant-bot replay)"}
FEE_RATE = 0.04
HALF_SPREAD = 0.005
BUDGET = 250.0
LIMITS = [(0.95, "limit<=0.95"), (0.99, "limit<=0.99"), (1.0001, "market (any price)")]


def get_json(url, tries=5):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as exc:  # noqa: BLE001
            last = exc
            print("retry", i, url, exc)
            time.sleep(2 + 2 * i)
    raise RuntimeError("failed %s :: %s" % (url, last))


def bracket_win(group, value):
    s = group.replace("<", "").replace("+", "").replace("$", "").replace(",", "")
    if group.startswith("<"):
        return value < float(s)
    if group.endswith("+"):
        return value >= float(s)
    a, b = s.split("-")
    return float(a) - 1e-9 <= value <= float(b) + 1e-9


def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def load_decisions():
    with open(os.path.join(BASE, "decision_points.csv"), encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["decision_epoch"] = dt.datetime.fromisoformat(
            r["decision_utc"].replace("Z", "+00:00")).timestamp()
        r["aaa_value"] = float(r["aaa_value"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-trades", action="store_true",
                    help="write trades.csv next to this script")
    args = ap.parse_args()

    events = get_json(GAMMA)
    by_slug = {e["slug"]: e for e in events}
    decisions = load_decisions()

    rows = []
    for d in decisions:
        e = by_slug[d["slug"]]
        if not e.get("closed"):
            raise RuntimeError("event not closed: " + d["slug"])
        win = [m for m in e["markets"] if bracket_win(m["groupItemTitle"], d["aaa_value"])]
        if len(win) != 1:
            raise RuntimeError("bracket mismatch %s %s" % (d["slug"], d["aaa_value"]))
        winning = win[0]
        outcome = [m for m in e["markets"]
                   if float(json.loads(m["outcomePrices"])[0]) > 0.5]
        if len(outcome) != 1 or outcome[0]["groupItemTitle"] != winning["groupItemTitle"]:
            raise RuntimeError("settled outcome does not match page bracket: " + d["slug"])
        end = dt.datetime.fromisoformat(
            e["endDate"].replace("Z", "+00:00")).timestamp()
        cid = winning["conditionId"]
        trades, off = [], 0
        while True:
            batch = get_json(TRADES.format(cid=cid, off=off))
            if not isinstance(batch, list) or not batch:
                break
            trades += batch
            if len(batch) < 1000 or off >= 20000:
                break
            off += 1000
            time.sleep(0.2)
        print("%s Price as of=%s AAA=%s Yesterday=%s bracket=%s decision=%s snapshot=%s"
              % (d["event_date"], d["price_as_of"], d["aaa_value"],
                 d["yesterday_avg"], winning["groupItemTitle"],
                 d["decision_utc"], d["snapshot_url"]))
        rows.append((d, winning, trades, end))

    all_fills = []
    for th, label in LIMITS:
        fills = []
        for d, winning, trades, end in rows:
            cand = [t for t in trades
                    if t.get("outcome") == "Yes" and t.get("side") == "BUY"
                    and d["decision_epoch"] <= t["timestamp"] < end
                    and t["price"] <= th]
            cand.sort(key=lambda t: t["timestamp"])
            if not cand:
                continue
            t = cand[0]
            p = float(t["price"])
            cost = p + HALF_SPREAD
            fee = FEE_RATE * p * (1 - p)
            net = 1.0 - cost - fee
            shares = min(BUDGET / cost, float(t["size"]))
            usd = net * shares
            fills.append(dict(variant=label, event=d["slug"], event_date=d["event_date"],
                              entry_utc=iso(t["timestamp"]), price=p,
                              print_size=float(t["size"]), fee_per_share=fee,
                              net_per_share=net, shares=shares, net_usdc=usd,
                              cost_usdc=cost * shares))
        print("\n%s: fills %d of %d" % (label, len(fills), len(rows)))
        for f in fills:
            print("  %s %s entry=%s p=%.6f size=%.2f fee/sh=%.6f net/sh=%.6f "
                  "shares=%.2f net$=%.4f"
                  % (f["event_date"], f["event"], f["entry_utc"], f["price"],
                     f["print_size"], f["fee_per_share"], f["net_per_share"],
                     f["shares"], f["net_usdc"]))
        if fills:
            total = sum(f["net_usdc"] for f in fills)
            cost = sum(f["cost_usdc"] for f in fills)
            med = sorted(f["net_per_share"] for f in fills)
            n = len(med)
            median = med[n // 2] if n % 2 else (med[n // 2 - 1] + med[n // 2]) / 2
            print("  median_net/sh=%.6f total_net$=%.4f cost$=%.2f ROI%%=%.4f"
                  % (median, total, cost, 100 * total / cost))
        all_fills += fills

    if args.write_trades:
        path = os.path.join(BASE, "trades.csv")
        cols = ["variant", "event", "event_date", "entry_utc", "price", "print_size",
                "fee_per_share", "net_per_share", "shares", "net_usdc", "cost_usdc"]
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for f in all_fills:
                w.writerow({k: f[k] for k in cols})
        print("\nwrote", path)


if __name__ == "__main__":
    main()
