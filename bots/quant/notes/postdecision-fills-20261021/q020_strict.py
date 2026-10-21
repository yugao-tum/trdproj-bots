#!/usr/bin/env python3
"""quant-020 OOS: re-run with post-decision executable fills.

Original fill (q020_oos.py): p24 = last YES-equivalent data-api print in
[endDate-72h, endDate-24h]; entry ask = p24 + 1 cent.  Decision time is
endDate-24h, so the original fill is a PRE-decision print (dot's criticism).

Strict fills computed here:
  STRICT   : first data-api print at/after endDate-24h (through endDate+1d)
  STRICT60 : first print in [endDate-24h, endDate-24h+60min], else unfillable
Both keep the original +1 cent half-spread and 0.05 taker fee.
"""
import csv
import datetime as dt
import os
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import fetch_trades, first_yes_price  # noqa: E402

ROOT = HERE.parents[3]
EVENTS = ROOT / "bots/quant/notes/q020-oos/events.csv"
FEE_RATE = 0.05
HALF_SPREAD = 0.01
BAND_LO, BAND_HI = 0.40, 0.55


def parse_iso(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def epoch(value):
    return int(value.timestamp())


def fee(p):
    return FEE_RATE * p * (1.0 - p)


def summarize(rows, net_key="net"):
    vals = [r[net_key] for r in rows if r.get(net_key) is not None]
    if not vals:
        return None
    asks = [r["ask_strict" if net_key == "net_strict" else
            ("ask60" if net_key == "net60" else "ask")] for r in rows
            if r.get(net_key) is not None]
    ys = sum(r["y"] for r in rows if r.get(net_key) is not None)
    total = sum(vals)
    stake = sum(asks)
    return {
        "n": len(vals),
        "unfillable": len(rows) - len(vals),
        "mean": total / len(vals),
        "median": statistics.median(vals),
        "total": total,
        "per_dollar": total / stake if stake else float("nan"),
        "hit": sum(1 for v in vals if v > 0) / len(vals),
        "yes_rate": ys / len(vals),
        "mean_ask": stake / len(vals),
    }


def fmt(label, s):
    if s is None:
        return "%s: n=0" % label
    return ("%s: n=%d unfillable=%d meanNet=%+.4f medianNet=%+.4f totalNet=%+.4f "
            "perDollar=%+.4f hit=%.4f YESrate=%.4f meanAsk=%.4f" % (
                label, s["n"], s["unfillable"], s["mean"], s["median"], s["total"],
                s["per_dollar"], s["hit"], s["yes_rate"], s["mean_ask"]))


def main():
    with open(EVENTS, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    band = [r for r in rows if r.get("in_band") == "True" and r.get("p24")]
    print("in-band events in q020-oos/events.csv: %d (priced by original: %d)"
          % (sum(1 for r in rows if r.get("in_band") == "True"), len(band)))

    for r in band:
        end_dt = parse_iso(r["endDate"])
        decision = end_dt - dt.timedelta(hours=24)
        r["_end"] = end_dt
        r["_decision"] = decision
        r["p24"] = float(r["p24"])
        r["y"] = int(r["y"])
        r["ask"] = min(1.0, r["p24"] + HALF_SPREAD)
        r["net"] = r["y"] - r["ask"] - fee(r["ask"])
        r["split"] = r["split"]

    def work(r):
        lo = epoch(r["_decision"])
        hi = epoch(r["_end"] + dt.timedelta(days=1))
        trades = fetch_trades(r["conditionId"], lo, hi)
        p, ts = first_yes_price(trades, lo)
        r["strict_price"] = p
        r["strict_ts"] = ts
        if p is None:
            r["ask_strict"] = r["net_strict"] = None
        else:
            a = min(1.0, p + HALF_SPREAD)
            r["ask_strict"] = a
            r["net_strict"] = r["y"] - a - fee(a)
        p60, ts60 = first_yes_price(trades, lo, lo + 3600)
        r["p60"] = p60
        r["ts60"] = ts60
        if p60 is None:
            r["ask60"] = r["net60"] = None
        else:
            a6 = min(1.0, p60 + HALF_SPREAD)
            r["ask60"] = a6
            r["net60"] = r["y"] - a6 - fee(a6)
        return r

    with ThreadPoolExecutor(max_workers=8) as ex:
        band = list(ex.map(work, band))

    print("\n[original] last pre-decision print +1c")
    for label, subset in (
        ("DISCOVERY", [r for r in band if r["split"] == "discovery"]),
        ("HOLDOUT", [r for r in band if r["split"] == "holdout"]),
        ("POOLED", band),
    ):
        print(fmt(label, summarize(subset, "net")))

    print("\n[strict] first print at/after decision +1c")
    for label, subset in (
        ("DISCOVERY", [r for r in band if r["split"] == "discovery"]),
        ("HOLDOUT", [r for r in band if r["split"] == "holdout"]),
        ("POOLED", band),
    ):
        print(fmt(label, summarize(subset, "net_strict")))

    print("\n[strict60] first print within 60 min after decision, else unfillable")
    for label, subset in (
        ("DISCOVERY", [r for r in band if r["split"] == "discovery"]),
        ("HOLDOUT", [r for r in band if r["split"] == "holdout"]),
        ("POOLED", band),
    ):
        print(fmt(label, summarize(subset, "net60")))

    delay = [(r["strict_ts"] - epoch(r["_decision"])) / 3600.0
             for r in band if r.get("strict_ts") is not None]
    if delay:
        delay.sort()
        print("\nfirst post-decision print delay hours: n=%d min=%.3f median=%.3f max=%.3f"
              % (len(delay), delay[0], statistics.median(delay), delay[-1]))
        print("post-decision prints later than 60 min: %d/%d"
              % (sum(1 for x in delay if x > 1.0), len(delay)))

    def verdict(subset, key):
        s = summarize(subset, key)
        if s is None:
            return "INSUFFICIENT"
        if s["n"] < 30:
            return "INSUFFICIENT(n=%d)" % s["n"]
        if s["median"] <= 0 or s["yes_rate"] <= s["mean_ask"]:
            return "FAIL"
        return "PASS"

    hold = [r for r in band if r["split"] == "holdout"]
    print("\nHOLDOUT verdict: original=%s strict=%s strict60=%s"
          % (verdict(hold, "net"), verdict(hold, "net_strict"), verdict(hold, "net60")))

    out = HERE / "q020_strict_events.csv"
    fields = ["slug", "endDate", "split", "y", "p24", "ask", "net",
              "strict_price", "strict_ts", "ask_strict", "net_strict",
              "p60", "ts60", "ask60", "net60"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in sorted(band, key=lambda x: x["endDate"]):
            w.writerow(r)
    print("\nwrote %s rows=%d" % (out.name, len(band)))


if __name__ == "__main__":
    main()
