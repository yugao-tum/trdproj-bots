#!/usr/bin/env python3
"""H-quant-020 source verification (2026-10-21).

Re-fetches every endpoint cited by bots/quant/entries/quant-020-*.md and
prints the live values next to the claims.  Keyless public GET only.
Downloads cached under _cache/ (gitignored).
"""
import csv, json, math, re, statistics, time
from pathlib import Path
from collections import Counter
import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
AS_OF = "2026-10-21"
UA = "quant-research-H-quant-020/1.0 (keyless public data)"
S = requests.Session(); S.headers.update({"User-Agent": UA})

CACHE.mkdir(exist_ok=True)
def get(url, params=None, cache_name=None, tries=5):
    if cache_name:
        p = CACHE / (cache_name + ".json")
        if p.exists():
            return json.loads(p.read_text())
    for i in range(tries):
        try:
            r = S.get(url, params=params, timeout=60)
            r.raise_for_status()
            d = r.json()
            if cache_name:
                p.write_text(json.dumps(d, separators=(",", ":")))
            time.sleep(0.15)
            return d
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(1.5 * (i + 1))

def load_csv():
    # scratch/H-quant-020 -> scratch -> scheduler -> notes; q020-oos sits in notes
    p = HERE.parents[2] / "q020-oos" / "events.csv"
    return list(csv.DictReader(p.open()))

print("H-quant-020 source verification as_of=%s" % AS_OF)

# 1 Gamma closed earnings events
allv, off = [], 0
while True:
    page = get(GAMMA + "/events", {"tag_slug":"earnings","limit":100,"offset":off,
                                  "closed":"true","order":"endDate","ascending":"false"},
               cache_name="gamma_closed_%d" % off)
    if not page: break
    allv += page; off += 100
    if len(page) < 100: break
print("\n[1] Gamma closed events tag_slug=earnings: %d" % len(allv))
dates = [e.get("endDate") or "" for e in allv]
print("    endDate span: %s .. %s" % (min(dates), max(dates)))
earn = [e for e in allv if "earnings" in (e.get("slug") or "").lower()
        or any("EPS" in (m.get("question") or "") for m in e.get("markets", []))]
print("    earnings-beat filter: %d" % len(earn))
mc = Counter(d[:7] for d in dates)
print("    monthly counts: " + " ".join("%s=%d" % (k, mc[k]) for k in sorted(mc)))
yes = no = other = yn = nn = 0
for e in allv:
    for m in e.get("markets", []):
        op = m.get("outcomePrices")
        if isinstance(op, str):
            try: op = json.loads(op)
            except Exception: op = None
        if not op or len(op) < 2: other += 1; continue
        g = "nongaap" in (e.get("slug") or "")
        if str(op[0]) == "1": yes += 1; yn += g
        elif str(op[1]) == "1": no += 1; nn += g
        else: other += 1
print("    markets yes/no/other: %d/%d/%d YES=%.4f" % (yes, no, other, yes/(yes+no)))
print("    nongaap yes/no=%d/%d rate=%.4f; gaap yes/no=%d/%d rate=%.4f"
      % (yn, nn, yn/(yn+nn) if yn+nn else float('nan'),
         yes-yn, no-nn, (yes-yn)/(yes-yn+no-nn)))
# dedupe company+date same as q020_oos
earn.sort(key=lambda e:(e["endDate"], e["slug"]))
seen=set(); ded=[]; dropped=[]
for e in earn:
    parts=e["slug"].split("-"); company=parts[1] if parts[0]=="will" and len(parts)>1 else parts[0]
    k=(company,e["endDate"][:10])
    if k in seen: dropped.append(e["slug"]); continue
    seen.add(k); ded.append(e)
print("    deduped company-quarter: %d; dropped: %s" % (len(ded), ", ".join(dropped) or "none"))
print("    events != 1 market: %d" % sum(1 for e in ded if len(e.get("markets", [])) != 1))

# compare with q020-oos events.csv
rows = load_csv()
slugs_csv = {r["slug"] for r in rows}
slugs_live = {e["slug"] for e in ded}
print("\n[2] q020-oos events.csv rows=%d; live deduped=%d" % (len(rows), len(ded)))
print("    only in csv: %d; only live: %d" % (len(slugs_csv-slugs_live), len(slugs_live-slugs_csv)))
new_live = sorted(slugs_live - slugs_csv)
if new_live:
    print("    new since csv (first 10): %s" % ", ".join(new_live[:10]))
old_only = sorted(slugs_csv - slugs_live)
if old_only:
    print("    csv-only (first 10): %s" % ", ".join(old_only[:10]))
print("    csv date span: %s .. %s" % (min(r["endDate"] for r in rows), max(r["endDate"] for r in rows)))
print("    csv in-band: %d" % sum(1 for r in rows if r["in_band"] == "True"))

# 3 rule text / hims
print("\n[3] rule source: hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05")
h = get(GAMMA + "/events", {"slug":"hims-quarterly-earnings-gaap-eps-02-23-2026-0pt05"},
        cache_name="hims")
he = h[0] if h else None
if not he:
    print("    MISSING")
else:
    d = he.get("description") or ""
    snippets = [
      "as of market creation", "SeekingAlpha estimates", "greater than $0.05",
      "within 96h", "45 calendar days", "rounded to the nearest cent",
      "IFRS EPS will be treated as GAAP EPS", "diluted GAAP EPS",
      "fat finger errors", "Lyft",
    ]
    print("    slug exists; title=%r" % he.get("title"))
    for s in snippets:
        print("    %-48s %s" % (s, "FOUND" if s.lower() in d.lower() else "MISSING"))
    print("    resolutionSource=%r restricted=%r volume=%r closed=%r"
          % (he.get("resolutionSource"), he.get("restricted"), he.get("volume"), he.get("closed")))
    m = (he.get("markets") or [{}])[0]
    print("    feeSchedule=%r feesEnabled=%r orderMinSize=%r orderPriceMinTickSize=%r negRisk=%r"
          % (m.get("feeSchedule"), m.get("feesEnabled"), m.get("orderMinSize"),
             m.get("orderPriceMinTickSize"), m.get("negRisk")))
    print("    outcomePrices=%r endDate=%r" % (m.get("outcomePrices"), m.get("endDate")))

# 4 public search
print("\n[4] public-search q=earnings")
ps = get(GAMMA + "/public-search", {"q":"earnings","limit_per_type":20,"events_status":"all"},
         cache_name="public_search")
evs = ps.get("events") or []
print("    events returned=%d pagination=%r" % (len(evs), ps.get("pagination")))
if evs:
    x = evs[0]
    print("    first: slug=%r title=%r resolutionSource=%r restricted=%r volume=%r"
          % (x.get("slug"), x.get("title"), x.get("resolutionSource"), x.get("restricted"), x.get("volume")))

# 5 open events
openevs, off = [], 0
while True:
    page = get(GAMMA + "/events", {"tag_slug":"earnings","limit":100,"offset":off,
                                  "closed":"false","order":"endDate","ascending":"true"},
               cache_name="gamma_open_%d" % off)
    if not page: break
    openevs += page; off += 100
    if len(page) < 100: break
print("\n[5] Gamma open events: %d" % len(openevs))
if openevs:
    print("    endDate span: %s .. %s" % (min(e["endDate"] for e in openevs), max(e["endDate"] for e in openevs)))
    for e in openevs[:3]:
        m = (e.get("markets") or [{}])[0]
        print("    %s | %s | bid=%r ask=%r fee=%r" % (e["slug"], e["endDate"], m.get("bestBid"), m.get("bestAsk"), m.get("feeSchedule")))

# 6 CLOB history + data-api trade on one closed in-band event
print("\n[6] CLOB prices-history + data-api trades (closed in-band example)")
ex = next(r for r in rows if r["in_band"] == "True")
import datetime as dt
end = dt.datetime.fromisoformat(ex["endDate"].replace("Z","+00:00"))
lo, hi = int((end-dt.timedelta(hours=72)).timestamp()), int(end.timestamp())
# need token id from live event or csv lacks it; fetch event
ee = get(GAMMA + "/events", {"slug": ex["slug"]}, cache_name="example_event")
tok = json.loads((ee[0]["markets"][0]["clobTokenIds"]))[0]
hist = get(CLOB + "/prices-history", {"market":tok,"startTs":lo,"endTs":hi,"fidelity":60},
           cache_name="example_history")
hh = hist.get("history") or []
pre = [p for p in hh if int(p["t"]) <= int((end-dt.timedelta(hours=24)).timestamp())]
print("    %s | history points=%d | last<=end-24h=%r" % (ex["slug"], len(hh), pre[-1] if pre else None))
tr = get(DATA_API + "/trades", {"market":ex["conditionId"],"limit":500,"offset":0},
         cache_name="example_trades")
tw = [t for t in tr if lo <= t["timestamp"] <= hi]
print("    data-api trades total=%d in window=%d fields=%s" % (len(tr), len(tw), sorted(tr[0].keys()) if tr else None))
if tw:
    t = sorted(tw, key=lambda x:x["timestamp"])[-1]
    print("    last trade: ts=%d side=%s outcome=%s price=%r size=%r" % (t["timestamp"], t["side"], t["outcome"], t["price"], t["size"]))

# 7 SEC EDGAR
print("\n[7] SEC EDGAR full-text search")
try:
    sec = get("https://efts.sec.gov/LATEST/search-index", {"q":"form:8-K items:2.02","forms":"8-K"},
              cache_name="sec_search")
    print("    hits.total=%r relation=%r" % (sec.get("hits",{}).get("total",{}).get("value"),
                                             sec.get("hits",{}).get("total",{}).get("relation")))
except Exception as e:
    print("    FAILED: %r" % (e,))
print("\ndone")
