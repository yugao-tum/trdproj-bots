#!/usr/bin/env python3
"""Fetch all Polymarket measles events/markets (free, keyless) and normalise.

Saves a compact JSON to _cache/events.json (git-ignored) with only the fields
the replay needs. Also prints the settled milestone windows used by the model.
"""
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_cache")
os.makedirs(CACHE, exist_ok=True)

URL = ("https://gamma-api.polymarket.com/public-search"
       "?q=measles&limit_per_type=100&events_status=all")


def get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (research; keyless)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


status, raw = get(URL)
print(f"GET {URL} -> HTTP {status}, {len(raw)} bytes")
data = json.loads(raw)
events = data["events"]
print(f"events: {len(events)}")

out = []
for e in events:
    ms = []
    for m in (e.get("markets") or []):
        ms.append({
            "slug": m.get("slug"),
            "question": m.get("question"),
            "conditionId": m.get("conditionId"),
            "clobTokenIds": json.loads(m.get("clobTokenIds") or "[]"),
            "threshold": m.get("groupItemTitle"),
            "outcomePrices": json.loads(m.get("outcomePrices") or "[]"),
            "startDate": m.get("startDate"),
            "endDate": m.get("endDate"),
            "closedTime": m.get("closedTime"),
            "closed": m.get("closed"),
            "feesEnabled": m.get("feesEnabled"),
            "feeSchedule": m.get("feeSchedule"),
            "acceptingOrders": m.get("acceptingOrders"),
            "volume": m.get("volume"),
        })
    out.append({
        "slug": e.get("slug"),
        "title": e.get("title"),
        "startDate": e.get("startDate"),
        "endDate": e.get("endDate"),
        "closedTime": e.get("closedTime"),
        "closed": e.get("closed"),
        "negRisk": e.get("negRisk"),
        "volume": e.get("volume"),
        "liquidity": e.get("liquidity"),
        "markets": ms,
    })

with open(os.path.join(CACHE, "events.json"), "w") as f:
    json.dump(out, f, indent=1)
print(f"wrote _cache/events.json ({os.path.getsize(os.path.join(CACHE,'events.json'))} bytes)")

print("\nmulti-strike 'by <date>' events (candidate milestones / ladders):")
for e in sorted(out, key=lambda x: x["endDate"] or ""):
    if len(e["markets"]) < 2:
        continue
    wins = sorted({m["threshold"] for m in e["markets"]})
    print(f"  {e['slug']:60s} end={e['endDate']} strikes={wins}")
