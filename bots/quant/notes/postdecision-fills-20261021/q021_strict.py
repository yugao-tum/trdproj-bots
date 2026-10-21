#!/usr/bin/env python3
"""quant-021 replay: strict post-decision fill sensitivity.

Original replay already fills from taker BUY prints strictly after the cutoff
(race-day 00:00 UTC), accumulating a VWAP to 100 shares.  This script reuses
the original cached data and computes:
  ORIGINAL : exec100 VWAP after cutoff (the published primary fill)
  STRICT   : first taker BUY print after cutoff (1 share)
  STRICT60 : first taker BUY print within 60 min after cutoff, else unfillable
Same fee (0.05*p*(1-p)) and 1 cent half-spread.
"""
import importlib.util
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MOD_PATH = ROOT / "bots/quant/replay/quant-021/run_replay.py"
CACHE = Path("/tmp/quant-021-cache")

spec = importlib.util.spec_from_file_location("q021_replay", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def summarize(rows, fill_key, label):
    vals = [mod.net(r["y"], r[fill_key]) for r in rows if r.get(fill_key) is not None]
    if not vals:
        return "%s: n=0" % label
    return ("%s: n=%d wins=%d unfillable=%d meanNet=%+.4f medianNet=%+.4f "
            "totalNet=%+.4f hit=%.4f" % (
                label, len(vals), sum(1 for r in rows if r.get(fill_key) is not None and r["y"] == 1),
                len(rows) - len(vals), sum(vals) / len(vals), statistics.median(vals),
                sum(vals), sum(1 for x in vals if x > 0) / len(vals)))


def main():
    print("cache", CACHE)
    events = mod.fetch_gamma(CACHE)
    races = mod.fetch_ergast(CACHE)
    schedule = mod.fetch_schedule(CACHE)
    matched = mod.match_events(events, races)
    fit, table, p0 = mod.fit_rates(races)
    print("gamma events=%d matched=%d fit races=%d" % (len(events), len(matched), len(fit)))

    rows = []
    for key, item in sorted(matched.items()):
        race = item["race"]
        event = item["event"]
        cut, start, qual_end = mod.event_times(race, schedule)
        market = mod.pole_market(event, race["pole"])
        if market is None:
            continue
        token = mod.yes_token(market)
        outcomes = __import__("json").loads(market["outcomes"])
        prices = __import__("json").loads(market["outcomePrices"])
        y = float(prices[outcomes.index("Yes")])
        trades = mod.fetch_trades(market, cut, start, CACHE)
        tr = [t for t in trades if t["asset"] == token]
        buys = sorted([t for t in tr if t["side"] == "BUY" and cut < t["timestamp"] < start],
                      key=lambda z: z["timestamp"])
        first, qfirst = mod.vwap(buys, 1)
        e100, q100 = mod.vwap(buys, 100)
        buys60 = [t for t in buys if t["timestamp"] <= cut + 3600]
        first60, q60 = mod.vwap(buys60, 1)
        rows.append({
            "key": key, "race": race["name"], "date": race["date"], "y": y,
            "margin": race.get("margin"), "p_hist": mod.last_price(token, cut, CACHE)[0],
            "exec100": e100, "first": first, "first60": first60,
            "first_ts": buys[0]["timestamp"] if buys else None,
            "first60_ts": buys60[0]["timestamp"] if buys60 else None,
        })

    def trigger(rows_in, model="A", cushion=0.05):
        out = []
        for r in rows_in:
            target = (mod.model_a(r["margin"], table) if model == "A" else p0) - cushion
            if r["p_hist"] is None or r["exec100"] is None:
                continue
            if r["p_hist"] <= target:
                out.append(r)
        return out

    primary = trigger(rows)
    print("primary selected n=%d" % len(primary))
    print(summarize(primary, "exec100", "[original] VWAP to 100 shares after cutoff"))
    print(summarize(primary, "first", "[strict] first taker BUY after cutoff"))
    print(summarize(primary, "first60", "[strict60] first taker BUY within 60 min"))

    delays = sorted((r["first_ts"] - mod.event_times(
        next(item["race"] for k, item in matched.items() if k == r["key"]),
        schedule)[0]) / 3600.0 for r in primary if r["first_ts"] is not None)
    if delays:
        print("first-buy delay hours: min=%.3f median=%.3f max=%.3f; >1h n=%d/%d"
              % (delays[0], statistics.median(delays), delays[-1],
                 sum(1 for x in delays if x > 1.0), len(delays)))


if __name__ == "__main__":
    main()
