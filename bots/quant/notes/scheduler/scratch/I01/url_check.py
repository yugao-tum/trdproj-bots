#!/usr/bin/env python3
"""HTTP status for the concrete URLs cited in quant-012 (placeholders mapped to examples)."""
import json
import requests
from pathlib import Path

UA = {"User-Agent": "quant-research/1.0 (public data check)"}
urls = [
    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2000-01-01&endtime=2026-10-01&minmagnitude=6.4&orderby=time-asc",
    "https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2015-01-01&endtime=2026-01-01&minmagnitude=6.5",
    "https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2015-01-01&endtime=2026-01-01&minmagnitude=7.0",
    "https://earthquake.usgs.gov/fdsnws/event/1/count?format=geojson&starttime=2015-01-01&endtime=2026-01-01&minmagnitude=5.5",
    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=text&starttime=2026-10-12&endtime=2026-10-19&minmagnitude=6.5",
    "https://earthquake.usgs.gov/earthquakes/search/",
    "https://gamma-api.polymarket.com/events?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25",
    "https://gamma-api.polymarket.com/events?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-12-october-18",
    "https://gamma-api.polymarket.com/public-search?q=earthquake&limit_per_type=50&events_status=all",
    "https://gamma-api.polymarket.com/public-search?q=magnitude&limit_per_type=50&events_status=all",
    "https://gamma-api.polymarket.com/events?tag_slug=earthquake&limit=500&closed=true&order=endDate&ascending=false",
    "https://clob.polymarket.com/prices-history?market=2500092545816023700094480893694885475686508335314406123382468585117526026802&interval=max&fidelity=60",
    "https://clob.polymarket.com/prices-history?market=101519993085150541985963030400073395102135944737997204045298260898135285026732&interval=max&fidelity=60",
    "https://gamma-api.polymarket.com/markets?slug=how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25",
    "https://gamma-api.polymarket.com/public-search?q=earthquake&limit_per_type=50&events_status=closed&page=1",
]
# map placeholder data-api URL to a real closed-market conditionId from the cache
cid = None
for f in sorted(Path("bots/quant/notes/scheduler/scratch/I01/_cache/gamma_events").glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    ev = d[0] if isinstance(d, list) and d else d
    for m in ev.get("markets", []):
        if m.get("conditionId"):
            cid = m["conditionId"]
            break
    if cid:
        break
if cid:
    urls.append(f"https://data-api.polymarket.com/trades?market={cid}&limit=2&offset=0")

for u in urls:
    try:
        r = requests.get(u, headers=UA, timeout=60)
        print(f"{r.status_code} {len(r.content):>8} {u}")
    except Exception as exc:
        print(f"ERR {exc} {u}")
