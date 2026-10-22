#!/usr/bin/env python3
"""Recompute the event/leg accounting quoted in entry quant-014 from events.csv.

Run from repo root (or anywhere):
    python3 bots/quant/notes/scheduler/scratch/H-quant-014/verify_counts.py

No network.  Corrects the 2026-10-21 wording that called all ladder legs negative:
16 triggered ladder legs from 5 events, 9 negative / 7 positive, mean negative.
"""
import csv
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[6]
EVENTS = ROOT / "bots/quant/replay/quant-014/events.csv"


def main():
    rows = list(csv.DictReader(EVENTS.open(encoding="utf-8")))
    print("rows/legs=%d  events=%d" % (len(rows), len({r["event_slug"] for r in rows})))

    by_type = {}
    for r in rows:
        t = r["event_type"]
        by_type.setdefault(t, {"legs": 0, "events": set()})
        by_type[t]["legs"] += 1
        by_type[t]["events"].add(r["event_slug"])
    for t, d in sorted(by_type.items()):
        print("%-14s legs=%3d events=%3d" % (t, d["legs"], len(d["events"])))

    trig = [r for r in rows if r["triggered"] == "1"]
    trig_events = {r["event_slug"] for r in trig}
    print("triggered legs=%d events=%d  YES=%d NO=%d" % (
        len(trig), len(trig_events),
        sum(1 for r in trig if r["side"] == "YES"),
        sum(1 for r in trig if r["side"] == "NO")))

    nets = [float(r["net_per_share"]) for r in trig]
    print("all triggered: mean=%.5f median=%.5f total=%.3f" % (
        statistics.fmean(nets), statistics.median(nets), sum(nets)))

    ladder = [r for r in trig if r["event_type"] != "daily_updown"]
    ln = [float(r["net_per_share"]) for r in ladder]
    print("triggered ladder: legs=%d events=%d mean=%.5f median=%.5f total=%.5f neg=%d pos=%d" % (
        len(ladder), len({r["event_slug"] for r in ladder}),
        statistics.fmean(ln), statistics.median(ln), sum(ln),
        sum(1 for x in ln if x < 0), sum(1 for x in ln if x > 0)))
    for t in ("monthly_above", "monthly_close", "weekly_above"):
        ns = [float(r["net_per_share"]) for r in ladder if r["event_type"] == t]
        if ns:
            print("  %-14s legs=%d mean=%.5f neg=%d pos=%d" % (
                t, len(ns), statistics.fmean(ns), sum(1 for x in ns if x < 0), sum(1 for x in ns if x > 0)))
        else:
            print("  %-14s legs=0 (no trigger)" % t)

    dates = sorted({r["resolution_date"] for r in ladder})
    print("ladder resolution dates: %s .. %s (all before 2026-07-01: %s)" % (
        dates[0], dates[-1], dates[-1] < "2026-07-01"))

    expected = {
        "legs": 303, "events": 259, "daily_legs": 252, "daily_events": 252,
        "ladder_legs": 51, "ladder_events": 7,
        "triggered_legs": 240, "triggered_events": 229,
        "triggered_ladder_legs": 16, "triggered_ladder_events": 5,
    }
    got = {
        "legs": len(rows), "events": len({r["event_slug"] for r in rows}),
        "daily_legs": by_type["daily_updown"]["legs"], "daily_events": len(by_type["daily_updown"]["events"]),
        "ladder_legs": len(rows) - by_type["daily_updown"]["legs"],
        "ladder_events": len({r["event_slug"] for r in rows if r["event_type"] != "daily_updown"}),
        "triggered_legs": len(trig), "triggered_events": len(trig_events),
        "triggered_ladder_legs": len(ladder), "triggered_ladder_events": len({r["event_slug"] for r in ladder}),
    }
    bad = 0
    for k, v in expected.items():
        ok = got[k] == v
        bad += 0 if ok else 1
        print("%-4s %-26s expected=%-4s got=%s" % ("OK" if ok else "FAIL", k, v, got[k]))
    print("\nfailures=%d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
