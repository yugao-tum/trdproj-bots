#!/usr/bin/env python3
"""B22 fix2 verification (2026-10-20 UTC).

Checks the two remaining review items:
  1. final (0100Z) archived GeoJSON ISSUE range and HTTP Last-Modified range;
  2. live Gamma rule text for the Aug-19 vs Sep-30 markets (no-data fallback,
     revisions cutoff, settlement source), so the entry can label the version.
Also re-prints the settlement source / payer distinction fields used in gate 4.
"""
import json, os, re, csv, datetime, requests

UA = {"User-Agent": "Mozilla/5.0 (research)"}
SPC = "https://www.spc.noaa.gov/products/outlook/archive/2026/"
s = requests.Session(); s.headers.update(UA)

ev = json.load(open("_cache/events_meta.json"))


def issue_of(path):
    d = json.load(open(path))
    for f in d.get("features", []):
        p = f.get("properties", {})
        v = p.get("ISSUE_ISO") or p.get("ISSUE")
        if v:
            return v
    return None


print("== final 0100Z GeoJSON ISSUE range ==")
issues = []
for r in ev:
    fn = f"_cache/geojson/{r['next']}_0100_torn.nolyr.geojson"
    v = issue_of(fn)
    if v:
        issues.append((v, r["date"], fn))
print(f"files_with_issue={len(issues)}/{len(ev)}")
iso = sorted(x[0] for x in issues)
print(f"ISSUE_ISO min={iso[0]} max={iso[-1]}")
print("earliest:", [x for x in issues if x[0] == iso[0]])
print("latest:", [x for x in issues if x[0] == iso[-1]])
times = sorted(datetime.datetime.fromisoformat(x[0].replace("Z", "+00:00")).strftime("%H:%M") for x in issues)
print(f"ISSUE time-of-day min={times[0]} max={times[-1]} n={len(times)}")

print("\n== final 0100Z HTTP Last-Modified range ==")
lm = []
for r in ev:
    u = f"{SPC}day1otlk_{r['next']}_0100_torn.nolyr.geojson"
    resp = s.head(u, timeout=30, allow_redirects=True)
    h = resp.headers.get("Last-Modified")
    if resp.status_code == 200 and h:
        dt = datetime.datetime.strptime(h, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=datetime.timezone.utc)
        lm.append((dt, r["date"], h))
lm.sort()
print(f"rows_with_lm={len(lm)}/{len(ev)}")
by_time = sorted((dt.strftime("%H:%M:%S"), d) for dt, d, h in lm)
print(f"LM earliest-date={lm[0][2]} ({lm[0][1]}) latest-date={lm[-1][2]} ({lm[-1][1]})")
print(f"LM time-of-day min={by_time[0]} max={by_time[-1]}")

print("\n== live Gamma rule text: Sep-30 market ==")
for slug in ["which-cities-face-tornado-risk-on-september-30-2026",
             "which-cities-face-tornado-risk-on-august-19-2026"]:
    r = s.get("https://gamma-api.polymarket.com/events", params={"slug": slug}, timeout=30)
    e = r.json()[0]
    mk = next(m for m in e["markets"] if m["slug"].endswith("chicago-il"))
    desc = mk.get("description", "")
    print(f"\n--- {slug} / {mk['slug']} ---")
    print(f"resolutionSource={mk.get('resolutionSource')}")
    print(f"feeSchedule={json.dumps(mk.get('feeSchedule'), sort_keys=True)}")
    for sentence in re.split(r"(?<=[.!?])\s+", desc):
        low = sentence.lower()
        if any(k in low for k in ["not been published", "subsequent revision", "scheduled", "resolution source", "borderline", "coordinates"]):
            print("RULE:", sentence.strip())

print("\n== gate 4 settlement source / payer ==")
r = s.get("https://gamma-api.polymarket.com/events", params={"slug": "which-cities-face-tornado-risk-on-september-30-2026"}, timeout=30)
e = r.json()[0]
mk = next(m for m in e["markets"] if m["slug"].endswith("chicago-il"))
print(f"event={e['slug']}")
print(f"market={mk['slug']}")
print(f"resolutionSource={mk.get('resolutionSource')}")
print("settlement variable=city coordinate inside SPC Day-1 tornado probability area >=2%")
print("payer=trader pricing off an older outlook or the literal '2%' label")
