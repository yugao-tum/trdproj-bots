#!/usr/bin/env python3
"""Independent re-computation of quant-012 gate-6 numbers from saved CSVs.

Reads buckets.csv / events.csv only (no network); recomputes the aggregates
quoted in the entry so every number has a script+stdout under I01.
"""
import csv
import statistics
from collections import Counter

BASE = "bots/quant/notes/scheduler/scratch/I01"
buckets = list(csv.DictReader(open(f"{BASE}/buckets.csv", encoding="utf-8")))
events = list(csv.DictReader(open(f"{BASE}/events.csv", encoding="utf-8")))

print("events", len(events), "buckets", len(buckets))
print("series events", dict(sorted(Counter(e["series"] for e in events).items())))
print("strict groups", len({e["strict_group"] for e in events}))
print("strict groups with >=1 pre-window fill", len({e["strict_group"] for e in events if int(e["n_priced_pre"]) > 0}))
print("strict groups with >=1 traded bucket", len({b["strict_group"] for b in buckets if b["traded"] == "1"}))
print("events with >=1 pre-window fill", sum(1 for e in events if int(e["n_priced_pre"]) > 0))
print("events with every bucket priced", sum(1 for e in events if int(e["n_priced_pre"]) == int(e["n_buckets"])))
print("partial bracket events", sum(1 for e in events if e["bracket_coverage"] != "full"))
print("USGS match", sum(1 for e in events if e["usgs_match"] == "MATCH"), "/", len(events))

traded = [b for b in buckets if b["traded"] == "1"]
gross = [float(b["gross_per_share"]) for b in traded]
net = [float(b["net_per_share"]) for b in traded]
stake = [float(b["no_exec_price"]) for b in traded]
wins = sum(1 for b in traded if b["resolved_yes"] == "0")
print("\ntraded buckets", len(traded), "winning NO", wins, f"({wins/len(traded):.1%})")
print(f"median gross {statistics.median(gross):+.6f}")
print(f"median net   {statistics.median(net):+.6f}")
print(f"mean gross   {statistics.mean(gross):+.6f}")
print(f"mean net     {statistics.mean(net):+.6f}")
print(f"total net    {sum(net):+.6f} / staked {sum(stake):.6f} = {sum(net)/sum(stake):+.4%}")
for ser in ("M5.5+", "M6.5+"):
    rows = [b for b in traded if b["series"] == ser]
    n = [float(b["net_per_share"]) for b in rows]
    s = [float(b["no_exec_price"]) for b in rows]
    print(f"  {ser}: traded {len(rows)}, win {sum(1 for b in rows if b['resolved_yes']=='0')}, "
          f"mean net {statistics.mean(n):+.6f}, total {sum(n):+.6f} / {sum(s):.6f} = {sum(n)/sum(s):+.4%}")

ll = [e for e in events if e["model_logloss"] and e["market_logloss"]]
model = [float(e["model_logloss"]) for e in ll]
market = [float(e["market_logloss"]) for e in ll]
better = sum(1 for e in ll if float(e["model_logloss"]) < float(e["market_logloss"]))
worse = sum(1 for e in ll if float(e["model_logloss"]) > float(e["market_logloss"]))
print("\nlog loss paired events", len(ll))
print(f"mean model  {statistics.mean(model):.6f}")
print(f"mean market {statistics.mean(market):.6f}")
print(f"model better {better}, market better {worse}")

print("\nmismatches (all M5.5):")
for e in events:
    if e["usgs_match"] != "MATCH":
        print(f"  {e['event_slug']}: USGS={e['usgs_count']} resolved={e['resolved_bucket']}")

print("\nnegative-side check (NOT hidden):")
print(f"  losing NO buckets: {sum(1 for b in traded if b['resolved_yes']=='1')} / {len(traded)}")
print(f"  worst net/share: {min(net):+.6f}; best net/share: {max(net):+.6f}")
print(f"  net return per dollar staked over 2026-01..2026-10: {sum(net)/sum(stake):+.4%}")
