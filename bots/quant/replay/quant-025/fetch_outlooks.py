#!/usr/bin/env python3
"""Fetch Gamma tornado-risk-daily events and archived SPC Day-1 tornado GeoJSON."""
import json, os, re, time, datetime, requests
UA={"User-Agent":"Mozilla/5.0 (research)"}
B="https://www.spc.noaa.gov/products/outlook/archive/2026/"
os.makedirs("_cache/geojson", exist_ok=True)
s=requests.Session(); s.headers.update(UA)
events=[]; offset=0
while True:
    r=s.get("https://gamma-api.polymarket.com/events",params={"series_id":12689,"closed":"true","limit":100,"offset":offset},timeout=30)
    r.raise_for_status(); batch=r.json()
    if not batch: break
    events+=batch; offset+=len(batch)
    if len(batch)<100: break
print("events",len(events))
out=[]
for e in events:
    m=re.search(r"on-([a-z]+)-(\d+)-(\d{4})", e["slug"])
    mon,day,yr=m.group(1),int(m.group(2)),int(m.group(3))
    dt=datetime.datetime.strptime(f"{mon} {day} {yr}","%B %d %Y").date()
    prev=dt.strftime("%Y%m%d"); nxt=(dt+datetime.timedelta(days=1)).strftime("%Y%m%d")
    rec={"slug":e["slug"],"date":dt.isoformat(),"prev":prev,"next":nxt,"endDate":e["endDate"],"volume":e.get("volume"),"markets":[]}
    for mk in e["markets"]:
        cm=re.search(r"coordinates\s+([-\d.]+),\s*([-\d.]+)", mk.get("description",""))
        rec["markets"].append({"q":mk["question"],"slug":mk["slug"],"conditionId":mk["conditionId"],
            "outcomePrices":mk.get("outcomePrices"),"closed":mk.get("closed"),"feeSchedule":mk.get("feeSchedule"),
            "lat":float(cm.group(1)) if cm else None,"lon":float(cm.group(2)) if cm else None})
    out.append(rec)
out.sort(key=lambda r:r["date"])
json.dump(out,open("_cache/events_meta.json","w"))
print("markets",sum(len(r['markets']) for r in out),"missing coords",sum(1 for r in out for m in r['markets'] if m['lat'] is None))
ok=0; miss=[]
for r in out:
    for tag,date in [("final",r["next"]),("2000",r["prev"]),("1630",r["prev"])]:
        hh="0100" if tag=="final" else tag
        fn=f"_cache/geojson/{date}_{hh}_torn.nolyr.geojson"
        if os.path.exists(fn): ok+=1; continue
        u=f"{B}day1otlk_{date}_{hh}_torn.nolyr.geojson"
        resp=None
        for attempt in range(3):
            try:
                resp=s.get(u,timeout=30)
                if resp.status_code==200 and resp.text.strip().startswith("{"):
                    open(fn,"w").write(resp.text); ok+=1; break
            except requests.RequestException:
                resp=None
            time.sleep(1+attempt)
        else:
            miss.append((u,getattr(resp,"status_code","ERR")))
        time.sleep(0.05)
print("geojson ok",ok,"miss",len(miss))
for m in miss[:10]: print(m)
