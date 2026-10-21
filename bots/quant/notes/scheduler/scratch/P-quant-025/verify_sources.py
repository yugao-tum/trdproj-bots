#!/usr/bin/env python3
import json, csv, re, datetime, statistics, urllib.request, urllib.error, ssl, sys
sys.dont_write_bytecode=True
UA={"User-Agent":"Mozilla/5.0 (research)"}

URLS=[
 ("series","https://gamma-api.polymarket.com/series?slug=tornado-risk-daily"),
 ("events","https://gamma-api.polymarket.com/events?series_id=12689&closed=true&limit=100&offset=0"),
 ("event_sep30","https://gamma-api.polymarket.com/events?slug=which-cities-face-tornado-risk-on-september-30-2026"),
 ("spc_1630_html","https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20260930_1630.html"),
 ("spc_1630_zip","https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20260930_1630-geojson.zip"),
 ("spc_2000_html","https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20260930_2000.html"),
 ("spc_final_html","https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20261001_0100.html"),
 ("spc_entry","https://www.spc.noaa.gov/products/outlook/day1otlk.html"),
 ("trades_wichita","https://data-api.polymarket.com/trades?market=0x4ea215eb9352e9723fed1435ab9824c2cb15a439bcc28c0980a2b02fea84839b&limit=1000"),
 ("trades_columbus","https://data-api.polymarket.com/trades?market=0x84cba6ff32d9afc8012f76e83d9c269c0f1c1d0c77c4ffde66b5396ab5a94391&limit=1000"),
]
print("== URL re-fetch (2026-10-21) ==")
for name,u in URLS:
    req=urllib.request.Request(u,headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=40) as r:
            b=r.read(); print(f"{name}\t{r.status}\t{len(b)}B\t{r.headers.get('Last-Modified')}")
    except Exception as e:
        print(f"{name}\tERR\t{e}")

print("\n== Gamma series / event counts ==")
req=urllib.request.Request(URLS[0][1],headers=UA)
ser=json.load(urllib.request.urlopen(req,timeout=40))
print("series id",ser[0]["id"],"slug",ser[0]["slug"],"recurrence",ser[0].get("recurrence"))
req=urllib.request.Request(URLS[1][1],headers=UA)
ev=json.load(urllib.request.urlopen(req,timeout=40))
print("closed events now",len(ev),"first",ev[-1]["slug"],"last",ev[0]["slug"])
print("events in entry sample (<=2026-10-19)",sum(1 for e in ev if re.search(r"on-(\w+)-(\d+)-(\d{4})",e["slug"]) and datetime.datetime.strptime(" ".join(re.search(r"on-(\w+)-(\d+)-(\d{4})",e["slug"]).groups()),"%B %d %Y").date().isoformat()<="2026-10-19"))
req=urllib.request.Request(URLS[2][1],headers=UA)
e30=json.load(urllib.request.urlopen(req,timeout=40))[0]
print("sep30 markets",len(e30["markets"]),"volume",e30.get("volume"))
ch=[m for m in e30["markets"] if m["slug"].endswith("chicago-il")][0]
print("chicago feeSchedule",ch.get("feeSchedule"))
print("chicago resolutionSource",ch.get("resolutionSource"))

print("\n== SPC html key lines ==")
for name in ["spc_1630_html","spc_2000_html","spc_final_html"]:
    u=dict(URLS)[name]
    t=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read().decode("utf-8","replace")
    for line in re.findall(r"(Updated:[^<\n]+|Valid[^<\n]+)",t)[:4]: print(name,"|",line.strip())

print("\n== cached geometry / headers (entry sample: events 2026-08-19..2026-10-19) ==")
lm={}
for r in csv.DictReader(open("_cache/last_modified.csv")):
    if r["status"]=="200" and r["last_modified"]:
        dt=datetime.datetime.strptime(r["last_modified"],"%a, %d %b %Y %H:%M:%S %Z")
        lm.setdefault(r["tag"],[]).append(dt.strftime("%H:%M"))
for tag in ["1630","2000","final"]:
    vals=sorted(lm[tag]); print(tag,"Last-Modified time-of-day",vals[0],"..",vals[-1],"n",len(vals))
issues=[]
import glob
for fn in glob.glob("_cache/geojson/*_0100_torn.nolyr.geojson"):
    d=fn.split("/")[-1][:8]
    if d>"20261020": continue
    j=json.load(open(fn))
    if j.get("features"):
        iso=j["features"][0]["properties"].get("ISSUE_ISO")
        if iso: issues.append(iso)
issues.sort(); tod=sorted(i[11:16] for i in issues)
print("sample final files",len(issues),"ISSUE_ISO",issues[0],"..",issues[-1])
print("final ISSUE time-of-day",tod[0],"..",tod[-1])

print("\n== trade size ranges ==")
rows=json.load(open("_cache/classified.json"))
# recompute strict/broad exactly as reproduce.py, then size ranges
import importlib.util, sys
spec=importlib.util.spec_from_file_location("rep","reproduce.py"); rep=importlib.util.module_from_spec(spec); spec.loader.exec_module(rep)
evm=json.load(open("_cache/events_meta.json")); lmm=rep.load_lm()
strict=[]; broad=[]
for r in rows:
    d=r["date"]; evr=next(x for x in evm if x["date"]==d)
    lm1630=lmm.get(("1630",d)); lm2000=lmm.get(("2000",d)); lmfinal=lmm.get(("final",evr["next"]))
    windows=[]
    if r["yes_1630"]: windows.append(("1630",(lm1630+120) if lm1630 else rep.ts(d,16,45),(lm2000+120) if lm2000 else rep.ts(d,19,55)))
    if r["yes_2000"]: windows.append(("2000",(lm2000+120) if lm2000 else rep.ts(d,20,20),(lmfinal+120) if lmfinal else rep.nextts(d,1,15)))
    t=rep.load_trades(r["conditionId"])
    for wname,lo,hi in windows:
        z=next((v for v in t if lo<=v["timestamp"]<hi and v["side"]=="BUY" and v["outcome"]=="Yes"),None)
        if z and z["yespx"]<=rep.THRESH: strict.append((z["size"],z["yespx"]))
        z2=next((v for v in t if lo<=v["timestamp"]<hi and v["yespx"]<=rep.THRESH),None)
        if z2: broad.append((z2["size"],z2["yespx"]))
print("strict n",len(strict),"size min/max",min(x[0] for x in strict),max(x[0] for x in strict),"yespx",min(x[1] for x in strict),max(x[1] for x in strict))
print("broad  n",len(broad),"size min/max",min(x[0] for x in broad),max(x[0] for x in broad),"yespx",min(x[1] for x in broad),max(x[1] for x in broad))

print("\n== capacity arithmetic ==")
print("broad 16.93 x10 /62d = %.2f/day"%(16.93*10/62))
print("strict 16.03 x10 /62d = %.2f/day"%(16.03*10/62))
print("max-day 9.61 x10 = %.2f"%(9.61*10))
print("strict volume shares=%.2f"%sum(x[0] for x in strict))
