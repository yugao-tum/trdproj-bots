#!/usr/bin/env python3
"""quant-018 paired: re-run with post-decision executable fills.

Original fill (q018_paired.py attach_prices): last data-api print in
[T-24h, T], where T = Monday 00:00 UTC of the market week.  Decision time is
T, so the original main fill is a PRE-decision print (dot's criticism).

Strict fills:
  STRICT   : first print at/after T (buckets.csv after24h_p_yes; for buckets
             with no print in [T,T+24h] fetch the first print in [T,T+10d])
  STRICT60 : first print in [T,T+60min], else unfillable
Same rule/costs as q018_paired.py: buy NO when 1-p_model >= fill + 0.01,
fill = 1-p_yes + 0.01, fee rate 0 (geopolitics), 1 share/bucket.
"""
import csv
import datetime as dt
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import fetch_trades, first_yes_price  # noqa: E402

ROOT = HERE.parents[3]
BUCKETS = ROOT / "bots/quant/notes/q018-paired/buckets.csv"
EVENTS = ROOT / "bots/quant/notes/q018-paired/events.csv"
HALF_SPREAD = 0.01
SAFETY = 0.01
FEE_RATE = 0.0


def ts(week_start):
    d = dt.date.fromisoformat(week_start)
    return int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())


def make_trade(p_model, p_yes, resolved_yes):
    if p_yes is None:
        return None
    fill = 1.0 - p_yes + HALF_SPREAD
    if not (0.0 < fill < 1.0):
        return None
    if (1.0 - p_model) + 1e-12 < fill + SAFETY:
        return None
    no_wins = 1.0 if int(resolved_yes) == 0 else 0.0
    fee = FEE_RATE * fill * (1.0 - fill)
    gross = no_wins - fill
    return {"fill": fill, "gross": gross, "net": gross - fee,
            "no_wins": int(no_wins), "ref_p_yes": p_yes}


def summarize(trades, label):
    if not trades:
        return "%s: n=0" % label
    nets = [t["net"] for t in trades]
    return ("%s: n=%d wins=%d medianGross=%+.4f medianNet=%+.4f meanNet=%+.4f "
            "totalNet=%+.4f hit=%.4f" % (
                label, len(trades), sum(t["no_wins"] for t in trades),
                statistics.median([t["gross"] for t in trades]),
                statistics.median(nets), sum(nets) / len(nets), sum(nets),
                sum(1 for x in nets if x > 0) / len(nets)))


def main():
    with open(BUCKETS, newline="", encoding="utf-8") as fh:
        buckets = list(csv.DictReader(fh))
    with open(EVENTS, newline="", encoding="utf-8") as fh:
        events = {r["slug"]: r for r in csv.DictReader(fh)}
    for b in buckets:
        b["T"] = ts(b["week_start"])
        b["p_model"] = float(b["p_model"])
        b["resolved_yes"] = int(b["resolved_yes"])

    # fill missing [T, T+24h] first prints by fetching the first print after T.
    missing = [b for b in buckets if not b["after24h_p_yes"]]
    print("buckets=%d, missing after24h first print=%d" % (len(buckets), len(missing)))

    def work(b):
        lo = b["T"]
        hi = lo + 10 * 86400
        trades = fetch_trades(b["conditionId"], lo, hi)
        p, t = first_yes_price(trades, lo)
        b["strict_p_yes"] = float(b["after24h_p_yes"]) if b["after24h_p_yes"] else p
        b["strict_ts"] = int(b["after24h_ts"]) if b["after24h_ts"] else t
        return b

    with ThreadPoolExecutor(max_workers=8) as ex:
        buckets = list(ex.map(work, buckets))

    for b in buckets:
        b["t_main"] = make_trade(b["p_model"], float(b["main_p_yes"]) if b["main_p_yes"] else None,
                                 b["resolved_yes"])
        b["t_strict"] = make_trade(b["p_model"], b.get("strict_p_yes"), b["resolved_yes"])
        p60 = None
        if b.get("strict_ts") is not None and b["strict_ts"] <= b["T"] + 3600:
            p60 = b["strict_p_yes"]
        b["t_60"] = make_trade(b["p_model"], p60, b["resolved_yes"])

    print("\n[original] last print in [T-24h,T]")
    for name in ("Bab", "Strait of Hormuz", "ALL"):
        key = "Bab el-Mandeb Strait" if name == "Bab" else name
        if name == "ALL":
            ts_ = [b["t_main"] for b in buckets if b["t_main"]]
        else:
            ts_ = [b["t_main"] for b in buckets if b["strait"] == key and b["t_main"]]
        print(summarize(ts_, name))

    print("\n[strict] first print at/after T")
    for name in ("Bab", "Strait of Hormuz", "ALL"):
        key = "Bab el-Mandeb Strait" if name == "Bab" else name
        if name == "ALL":
            ts_ = [b["t_strict"] for b in buckets if b["t_strict"]]
        else:
            ts_ = [b["t_strict"] for b in buckets if b["strait"] == key and b["t_strict"]]
        print(summarize(ts_, name))

    print("\n[strict60] first print within 60 min after T, else unfillable")
    for name in ("Bab", "Strait of Hormuz", "ALL"):
        key = "Bab el-Mandeb Strait" if name == "Bab" else name
        if name == "ALL":
            ts_ = [b["t_60"] for b in buckets if b["t_60"]]
        else:
            ts_ = [b["t_60"] for b in buckets if b["strait"] == key and b["t_60"]]
        print(summarize(ts_, name))

    bab = [b for b in buckets if b["strait"] == "Bab el-Mandeb Strait"]
    print("\nBab buckets=%d, original fills=%d, strict fills=%d, strict60 fills=%d"
          % (len(bab), sum(1 for b in bab if b["t_main"]),
             sum(1 for b in bab if b["t_strict"]), sum(1 for b in bab if b["t_60"])))
    unf = [b for b in bab if b["t_strict"] is None]
    if unf:
        print("Bab strict-unfillable buckets: " + ", ".join(
            "%s %s" % (b["slug"], b["label"]) for b in unf))
    print("Bab events with >=1 strict fill: %d/%d"
          % (len({b["slug"] for b in bab if b["t_strict"]}), len({b["slug"] for b in bab})))
    print("Bab events with >=1 strict60 fill: %d/%d"
          % (len({b["slug"] for b in bab if b["t_60"]}), len({b["slug"] for b in bab})))

    out = HERE / "q018_strict_buckets.csv"
    fields = ["slug", "strait", "week_start", "label", "p_model", "resolved_yes",
              "main_p_yes", "strict_p_yes", "strict_ts"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for b in buckets:
            w.writerow(b)
    print("\nwrote %s rows=%d" % (out.name, len(buckets)))


if __name__ == "__main__":
    main()
