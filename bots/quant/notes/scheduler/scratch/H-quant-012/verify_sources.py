#!/usr/bin/env python3
import csv, io, json, math, statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
CACHE.mkdir(exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "quant-research/1.0 (public data; no auth)"
UA = {"User-Agent": "quant-research/1.0"}

def fetch(url, params=None, timeout=90):
    r = S.get(url, params=params, timeout=timeout)
    return r

def show(label, r, needle=None):
    body = r.text
    ok = r.status_code == 200
    extra = ""
    if needle is not None:
        extra = f" needle={'FOUND' if needle in body else 'MISSING'}"
    print(f"{'OK ' if ok else 'BAD'} {r.status_code} {len(r.content):8d}B {label}{extra}")
    return body

def usgs_csv():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    p = {"format": "csv", "starttime": "2000-01-01", "endtime": "2026-10-01",
         "minmagnitude": 6.4, "orderby": "time-asc"}
    path = CACHE / "usgs_6.4.csv"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        r = type("R", (), {"status_code": 200, "text": text, "content": text.encode()})()
    else:
        r = fetch(url, p)
        text = r.text
        if r.status_code == 200:
            path.write_text(text, encoding="utf-8")
    show("USGS CSV 2000-01-01..2026-10-01 minmag6.4", r)
    lines = [x for x in text.splitlines() if x.strip()]
    rows = list(csv.DictReader(io.StringIO(text)))
    mags = []
    times = []
    for row in rows:
        try:
            m = float(row["mag"])
        except (TypeError, ValueError):
            continue
        if m >= 6.5:
            mags.append(m)
            times.append(datetime.fromisoformat(row["time"].replace("Z", "+00:00")))
    times.sort()
    start = datetime(2000, 1, 3, tzinfo=timezone.utc).timestamp()
    end = datetime(2026, 10, 1, tzinfo=timezone.utc).timestamp()
    bins = []
    t = start
    while t + 7 * 86400 <= end:
        a, b = t, t + 7 * 86400
        bins.append(sum(1 for x in times if a <= x.timestamp() < b))
        t = b
    from collections import Counter
    c = Counter(bins)
    print(f"    lines={len(lines)} (header={lines[0][:40]!r}) mag>=6.5={len(mags)} "
          f"7d_bins={len(bins)} sum={sum(bins)} mean={sum(bins)/len(bins):.4f}")
    print(f"    dist={dict(sorted(c.items()))}")
    print(f"    P(>=3)={sum(v for k,v in c.items() if k>=3)/len(bins):.4f} "
          f"P(>=5)={sum(v for k,v in c.items() if k>=5)/len(bins):.4f}")
    print(f"    sections: 2016+={sum(1 for x in times if x.year>=2016)} "
          f"2021+={sum(1 for x in times if x.year>=2021)} "
          f"2025-10+={sum(1 for x in times if x >= datetime(2025,10,1,tzinfo=timezone.utc))}")

def counts():
    for mag in ("6.5", "7.0", "5.5"):
        r = fetch("https://earthquake.usgs.gov/fdsnws/event/1/count",
                  {"format": "geojson", "starttime": "2015-01-01",
                   "endtime": "2026-01-01", "minmagnitude": mag})
        body = show(f"USGS count 2015-2026 minmag {mag}", r)
        try:
            print("    ", json.loads(body))
        except Exception:
            print("    body", body[:120])

def text_window():
    r = fetch("https://earthquake.usgs.gov/fdsnws/event/1/query",
              {"format": "text", "starttime": "2026-10-12",
               "endtime": "2026-10-19", "minmagnitude": "6.5"})
    body = show("USGS text 2026-10-12..2026-10-19 minmag6.5", r)
    lines = [x for x in body.splitlines() if x.strip()]
    print(f"    lines={len(lines)}")
    for line in lines[:6]:
        print("    ", line[:160])

def gamma_event(slug, needles=()):
    r = fetch("https://gamma-api.polymarket.com/events", {"slug": slug})
    body = show(f"Gamma event {slug}", r)
    try:
        d = json.loads(body)
        e = d[0] if isinstance(d, list) else d
    except Exception:
        print("    unparsable")
        return
    print(f"    closed={e.get('closed')} endDate={e.get('endDate')} volume={e.get('volume')} "
          f"liquidity={e.get('liquidity')} negRisk={e.get('negRisk')}")
    print(f"    feeSchedules={[m.get('feeSchedule') for m in e.get('markets', [])]}")
    desc = e.get("description", "")
    for needle in needles:
        print(f"    rule needle {'FOUND' if needle in desc else 'MISSING'}: {needle[:80]!r}")
    print(f"    brackets={[m.get('groupItemTitle') for m in e.get('markets', [])]}")
    print(f"    prices={[m.get('outcomePrices') for m in e.get('markets', [])]}")
    return e

def search():
    r = fetch("https://gamma-api.polymarket.com/public-search",
              {"q": "earthquake", "limit_per_type": 50, "events_status": "all"})
    body = show("Gamma public-search q=earthquake all", r)
    d = json.loads(body)
    slugs = [e.get("slug") for e in d.get("events", [])]
    print(f"    events={len(slugs)} has_oct19={any('october-19-october-25' in s for s in slugs)}")
    r = fetch("https://gamma-api.polymarket.com/public-search",
              {"q": "magnitude", "limit_per_type": 50, "events_status": "all"})
    body = show("Gamma public-search q=magnitude all", r)
    d = json.loads(body)
    for e in d.get("events", []):
        s = e.get("slug", "")
        if s in ("how-many-7pt0-or-above-earthquakes-in-2026",
                 "how-many-7pt0-or-above-earthquakes-by-june-30"):
            print(f"    {s} volume={e.get('volume')}")

def tag_scan():
    r = fetch("https://gamma-api.polymarket.com/events",
              {"tag_slug": "earthquake", "limit": 500, "closed": "true",
               "order": "endDate", "ascending": "false"})
    body = show("Gamma tag=earthquake closed", r)
    d = json.loads(body)
    evs = d if isinstance(d, list) else d.get("events", [])
    vol = sum(float(e.get("volume") or 0) for e in evs)
    titles = {"how-many": 0, "megaquake": 0, "7.0 or above": 0, "other": 0}
    months = {}
    for e in evs:
        s = (e.get("slug") or "").lower()
        if "how-many" in s:
            titles["how-many"] += 1
        elif "megaquake" in s:
            titles["megaquake"] += 1
        elif "7pt0" in s or "7-0" in s or "7.0" in s:
            titles["7.0 or above"] += 1
        else:
            titles["other"] += 1
        m = (e.get("endDate") or "")[:7]
        months[m] = months.get(m, 0) + 1
    print(f"    events={len(evs)} volume_sum={vol:,.2f}")
    print(f"    title_counts={titles}")
    print(f"    months={dict(sorted(months.items()))}")
    print(f"    endDate range={min(e.get('endDate','') for e in evs)} .. {max(e.get('endDate','') for e in evs)}")

def clob_checks():
    urls = [
        ("open token 0", "https://clob.polymarket.com/prices-history",
         {"market": "2500092545816023700094480893694885475686508335314406123382468585117526026802", "interval": "max", "fidelity": 60}),
        ("closed token", "https://clob.polymarket.com/prices-history",
         {"market": "101519993085150541985963030400073395102135944737997204045298260898135285026732", "interval": "max", "fidelity": 60}),
    ]
    for label, url, p in urls:
        r = fetch(url, p)
        body = show(f"CLOB prices-history {label}", r)
        print("    ", body[:180])

def data_api():
    r = fetch("https://data-api.polymarket.com/trades",
              {"market": "0xe88699f06db8629bf5497f00343d0bc4c52497eae0476212b5bff381769d863a",
               "limit": 2, "offset": 0})
    body = show("data-api trades example", r)
    try:
        d = json.loads(body)
        print(f"    n={len(d)} fields={sorted(d[0].keys()) if d else []}")
    except Exception:
        print("    unparsable")

def markets_slug():
    r = fetch("https://gamma-api.polymarket.com/markets",
              {"slug": "how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25"})
    body = show("Gamma markets?slug=event-slug", r)
    print("    ", body[:80])

def page_check():
    r = fetch("https://gamma-api.polymarket.com/public-search",
              {"q": "earthquake", "limit_per_type": 50, "events_status": "closed", "page": 1})
    show("Gamma public-search closed page=1", r)

def main():
    print("quant-012 source verification, accessed 2026-10-21 (UTC)")
    print("\n[USGS]")
    usgs_csv()
    counts()
    text_window()
    r = fetch("https://earthquake.usgs.gov/earthquakes/search/")
    show("USGS search page", r, "<title>Search Earthquake Catalog</title>")
    print("\n[Gamma event snapshots]")
    gamma_event("how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25",
                ("between October 19, 2026", "United States Geological Survey",
                 "48 hours", "lowest bracket", "anywhere on Earth"))
    gamma_event("how-many-6pt5-or-above-earthquakes-worldwide-october-12-october-18")
    print("\n[Gamma search / tag]")
    search()
    tag_scan()
    print("\n[CLOB]")
    clob_checks()
    print("\n[data-api / markets-slug / paging]")
    data_api()
    markets_slug()
    page_check()

if __name__ == "__main__":
    main()
