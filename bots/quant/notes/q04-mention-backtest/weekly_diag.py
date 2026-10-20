#!/usr/bin/env python3
"""
POST-HOC DIAGNOSTIC, NOT PART OF THE PRE-SPECIFIED BACKTEST.

Reads only cache/events_*.json and trades.csv from the pre-specified run.
Classifies an event as a PERIOD/WEEK market by a slug heuristic:
  slug contains "this-week", "episode-of-the-week", or ends with "-week".
For these markets the Gamma endDate is the end of the measurement period, so
an entry at endDate-24h or endDate-6h can be INSIDE the period (look-ahead).
Prints the pre-specified rules split into period vs non-period events.
Run: python3 weekly_diag.py
"""
import collections
import csv
import datetime as dt
import glob
import json
import math
import statistics as st

def parse_dt(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None

def is_period(e):
    s = (e.get("slug") or "").lower()
    return ("this-week" in s) or ("episode-of-the-week" in s) or s.endswith("-week")

events = {}
for f in glob.glob("cache/events_mention-markets_*.json"):
    for e in json.load(open(f)):
        events[str(e["id"])] = e

now = dt.datetime.now(dt.timezone.utc)
dated = sorted(
    [(parse_dt(e["endDate"]), e) for e in events.values()
     if parse_dt(e.get("endDate")) and parse_dt(e["endDate"]) <= now],
    key=lambda x: x[0],
)
sample = [e for _, e in dated[-200:]]
period_ids = {str(e["id"]) for e in sample if is_period(e)}
print(f"sample events={len(sample)}  period/week events={len(period_ids)}")
print(f"period slugs: {sorted(e['slug'] for e in sample if is_period(e))[:5]} ...")

rows = list(csv.DictReader(open("trades.csv")))
for hz in ["H24", "H6"]:
    print(f"\n===== {hz} =====")
    for rule in ["R1", "R2", "R3"]:
        print(f"  {rule}")
        for grp, want in [("period", True), ("nonperiod", False)]:
            rr = [r for r in rows if r["horizon"] == hz and r["rule"] == rule
                  and (r["event_id"] in period_ids) == want]
            if not rr:
                print(f"    {grp:<10} n=0")
                continue
            rets = [float(r["ret"]) for r in rr]
            by_ev = collections.defaultdict(list)
            for r in rr:
                by_ev[r["event_id"]].append(float(r["ret"]))
            ev_means = [sum(v) / len(v) for v in by_ev.values()]
            if len(ev_means) >= 2 and st.stdev(ev_means) > 0:
                t = (sum(ev_means) / len(ev_means)) / (
                    st.stdev(ev_means) / math.sqrt(len(ev_means)))
            else:
                t = float("nan")
            print(f"    {grp:<10} trades={len(rr):4d} events={len(by_ev):3d} "
                  f"win={sum(1 for x in rets if x > 0)/len(rets):.4f} "
                  f"mean={sum(rets)/len(rets):+.5f} "
                  f"event_mean={sum(ev_means)/len(ev_means):+.5f} t={t:+.2f}")

# ---------------------------------------------------------------------------
# Additional post-hoc diagnostic: endDate often looks like an end-of-day
# deadline (03:59Z = 23:59 ET, or 23:59Z) rather than the event start time.
# For such events, endDate-6h can fall after the event has already happened.
def is_eod(e):
    d = parse_dt(e.get("endDate"))
    return d is not None and ((d.hour == 3 and d.minute == 59)
                              or (d.hour == 23 and d.minute == 59))

print("\nendDate end-of-day-marker share (post-hoc):")
for hz in ["H24", "H6"]:
    for rule in ["R1", "R2", "R3"]:
        rr = [r for r in rows if r["horizon"] == hz and r["rule"] == rule]
        n_eod = sum(1 for r in rr if is_eod(events[r["event_id"]]))
        print(f"  {hz} {rule}: {n_eod}/{len(rr)} = {100*n_eod/len(rr):.1f}%")

print("\nH6 R1 split by endDate end-of-day marker (post-hoc):")
for want in [True, False]:
    rr = [r for r in rows if r["horizon"] == "H6" and r["rule"] == "R1"
          and is_eod(events[r["event_id"]]) == want]
    if not rr:
        continue
    rets = [float(r["ret"]) for r in rr]
    by_ev = collections.defaultdict(list)
    for r in rr:
        by_ev[r["event_id"]].append(float(r["ret"]))
    em = [sum(v) / len(v) for v in by_ev.values()]
    t = ((sum(em) / len(em)) / (st.stdev(em) / math.sqrt(len(em)))
         if len(em) >= 2 and st.stdev(em) > 0 else float("nan"))
    print(f"  {'eod' if want else 'non-eod':<8} trades={len(rr):4d} events={len(by_ev):3d} "
          f"mean={sum(rets)/len(rets):+.5f} event_mean={sum(em)/len(em):+.5f} t={t:+.2f}")
