#!/usr/bin/env python3
"""quant-012 replay: check post-decision fill timing.

Original replay (quant-012/replay.py) already uses the FIRST data-api print at
or after t0, so the STRICT unbounded rule is identical to the original.  The
only stricter variant here is STRICT60: if that first print arrives more than
60 minutes after t0, drop the bracket; an event with no remaining fill is
unfillable.  Fees/costs are unchanged (0.05 fee already inside net_per_share).
"""
import csv
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TRADES = ROOT / "bots/quant/replay/quant-012/trades.csv"


def summarize(trades, label):
    if not trades:
        return "%s: n=0" % label
    nets = [float(t["net_per_share"]) for t in trades]
    return ("%s: fills=%d events=%d medianNet=%+.4f meanNet=%+.4f totalNet=%+.4f hit=%.4f"
            % (label, len(trades), len({t["event_slug"] for t in trades}),
               statistics.median(nets), sum(nets) / len(nets), sum(nets),
               sum(1 for x in nets if x > 0) / len(nets)))


def main():
    with open(TRADES, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["_delay"] = float(r["delay_h"])

    all_events = {r["event_slug"] for r in rows}
    print("original rows=%d events=%d, delay>1h fills=%d"
          % (len(rows), len(all_events), sum(1 for r in rows if r["_delay"] > 1.0)))
    print(summarize(rows, "[original = strict] first print at/after t0"))

    kept = [r for r in rows if r["_delay"] <= 1.0]
    kept_events = {r["event_slug"] for r in kept}
    unfillable_events = all_events - kept_events
    print(summarize(kept, "[strict60] first print within 60 min after t0"))
    print("strict60: events kept=%d, unfillable events=%d (all their fills >60 min)"
          % (len(kept_events), len(unfillable_events)))

    # event-level net: sum the per-share net of all filled brackets in the event
    def event_nets(rs):
        by = {}
        for r in rs:
            by.setdefault(r["event_slug"], 0.0)
            by[r["event_slug"]] += float(r["net_per_share"])
        return sorted(by.values())

    for label, rs in (("original/strict", rows), ("strict60", kept)):
        vals = event_nets(rs)
        if vals:
            print("%s event-level: events=%d medianSumNet=%+.4f meanSumNet=%+.4f hit=%.4f"
                  % (label, len(vals), statistics.median(vals),
                     sum(vals) / len(vals), sum(1 for x in vals if x > 0) / len(vals)))

    delays = sorted(r["_delay"] for r in rows)
    print("fill delay hours: min=%.3f p25=%.3f median=%.3f p75=%.3f max=%.3f"
          % (delays[0], delays[len(delays) // 4], statistics.median(delays),
             delays[3 * len(delays) // 4], delays[-1]))


if __name__ == "__main__":
    main()
