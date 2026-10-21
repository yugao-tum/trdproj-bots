#!/usr/bin/env python3
"""Chronological 70/30 hold-out split of the quant-010 replay events.

Fixed rule, declared before looking at the split: sort the unique chart weeks,
the first ceil(0.70 * n) weeks are the development slice, the rest the
out-of-sample (OOS) slice. No parameter is fitted on either slice, so this is a
descriptive temporal hold-out test of stability, not an in-sample optimisation.

Reads events.csv / events_movies.csv produced by q010_replay.py. One cluster =
one chart week (global and US averaged), per the entry's independence rule.
"""
import csv
import statistics
import sys


def clusters(rows):
    by = {}
    for r in rows:
        by.setdefault(r["week"], []).append(r)
    out = []
    for week in sorted(by):
        rs = by[week]
        out.append({
            "week": week,
            "net": statistics.mean(float(x["net"]) for x in rs),
            "staked": statistics.mean(float(x["ask"]) for x in rs),
            "won": statistics.mean(float(x["won"]) for x in rs),
            "net_per_dollar": statistics.mean(float(x["net_per_dollar"]) for x in rs),
        })
    return out


def report(label, path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    cl = clusters(rows)
    n = len(cl)
    cut = -(-7 * n // 10)  # ceil(0.7 n)
    print("")
    print("## %s (%s)" % (label, path))
    print("clusters=%d | dev weeks 1..%d | OOS weeks %d..%d" % (n, cut, cut + 1, n))
    for name, part in (("DEV (first 70%)", cl[:cut]), ("OOS (last 30%)", cl[cut:])):
        if not part:
            print("  %-16s n=0" % name)
            continue
        nets = [x["net"] for x in part]
        hits = [x["won"] for x in part]
        dollars = [x["net_per_dollar"] for x in part]
        total_staked = sum(x["staked"] for x in part)
        print("  %-16s n=%2d | hit=%.4f | net/share median=%+.4f mean=%+.4f "
              "| net/$ mean=%+.4f | sum net=%+.4f on %+.4f staked | weeks %s..%s" % (
                  name, len(part), statistics.mean(hits),
                  statistics.median(nets), statistics.mean(nets),
                  statistics.mean(dollars), sum(nets), total_staked,
                  part[0]["week"], part[-1]["week"]))
    print("  sign consistency: dev median %+.4f, OOS median %+.4f" % (
        statistics.median([x["net"] for x in cl[:cut]]),
        statistics.median([x["net"] for x in cl[cut:]]) if cl[cut:] else float("nan")))
    return 0


def main(argv):
    show = argv[1] if len(argv) > 1 else "events.csv"
    movie = argv[2] if len(argv) > 2 else "events_movies.csv"
    print("quant-010 chronological hold-out split (fixed 70/30, no re-tuning)")
    report("Netflix #1 show proxy arm", show)
    report("Netflix #1 movie proxy arm", movie)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
