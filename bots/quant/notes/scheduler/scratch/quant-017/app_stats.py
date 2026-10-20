#!/usr/bin/env python3
"""Independently recompute the quant-017 event counts, Other base rate and
weekly-board frequency from Gamma public-search. Free, keyless."""
import gzip
import json
import pathlib
import re
import time
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent
CACHE = BASE / "_cache"
CACHE.mkdir(exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return r.status, raw
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                print("ERR", url, e)
            time.sleep(2 + i * 2)
    return None, None


events = {}
pagination = None
for page in range(1, 6):
    url = f"https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all&page={page}"
    st, raw = get(url)
    print(f"page {page}: HTTP {st}, {len(raw) if raw else 0} bytes")
    if st != 200:
        continue
    d = json.loads(raw)
    (CACHE / f"search_p{page}.json").write_bytes(raw)
    pagination = d.get("pagination", pagination)
    for e in d.get("events", []):
        events[e["slug"]] = e

print("pagination:", pagination)
print("events deduped:", len(events))
closed = [e for e in events.values() if e.get("closed")]
print("closed:", len(closed), "open:", len(events) - len(closed))

free = [e for e in events.values() if "free app" in (e.get("title") or "").lower()]
free_closed = [e for e in free if e.get("closed")]
print("free title:", len(free), "closed:", len(free_closed))

weekly = [e for e in closed if re.match(r"^[12]-free-app-in-the-us-apple-app-store-on-", e["slug"])]
print("weekly closed:", len(weekly))

other = 0
sub = {"#1": [0, 0], "#2": [0, 0]}
reserved = 0
dates = set()
vol = 0.0
months = {}
for e in weekly:
    win = None
    for m in e.get("markets", []):
        try:
            prices = json.loads(m.get("outcomePrices") or "[]")
            outs = json.loads(m.get("outcomes") or "[]")
        except Exception:  # noqa: BLE001
            continue
        for name, p in zip(outs, prices):
            if name == "Yes" and float(p) > 0.5:
                win = m.get("groupItemTitle")
    if win == "Other":
        other += 1
        tag = "#1" if e["slug"].startswith("1-") else "#2"
        sub[tag][0] += 1
    tag = "#1" if e["slug"].startswith("1-") else "#2"
    sub[tag][1] += 1
    if any((m.get("groupItemTitle") or "").startswith("Reserved") for m in e.get("markets", [])):
        reserved += 1
    if e.get("endDate"):
        dates.add(e["endDate"][:10])
        months[e["endDate"][:7]] = months.get(e["endDate"][:7], 0) + 1
    vol += float(e.get("volume") or 0)

print("other winners:", other, "rate:", other / len(weekly) if weekly else None)
print("by sub:", sub)
print("reserved present:", reserved, "/", len(weekly))
print("market min/max:", min(len(e.get("markets", [])) for e in weekly), max(len(e.get("markets", [])) for e in weekly))
print("unique endDate dates:", len(dates))
print("volume sum:", round(vol, 6))
print("endDate months:", sorted(months.items()))
