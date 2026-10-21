#!/usr/bin/env python3
"""Re-fetch every source cited by quant-016 and print what it actually says.

Also fetches the max-window CLOB history cited in the entry, and reads the RT
pages cached by check_rounding.py. No credential, no login.
"""
import json, os, re, datetime, statistics, collections
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (research; quant-016 hardening)"})

def get(url, **kw):
    r = S.get(url, timeout=40, **kw)
    return r

def jget(url):
    r = get(url)
    if r.status_code != 200:
        return None, r.status_code
    try:
        return r.json(), r.status_code
    except Exception:
        return None, r.status_code

def thr(m):
    t = str(m.get("groupItemTitle", "")).replace("+", "").strip()
    return int(t) if re.fullmatch(r"\d+", t) else None

print("access date: 2026-10-21 UTC\n")

# 1 public-search
u = "https://gamma-api.polymarket.com/public-search?q=rotten%20tomatoes&limit_per_type=100"
d, st = jget(u)
print(f"[1] {u}\n    HTTP {st}")
if d:
    ev = d.get("events", [])
    print("    totalResults =", d.get("pagination", {}).get("totalResults"),
          "| events returned =", len(ev))
    pat = re.compile(r"-rotten-tomato(es)?-score(-|$)")
    print("    slug pattern matches:", sum(1 for e in ev if pat.search(e.get("slug", ""))), "/", len(ev))
    print("    first slug:", ev[0].get("slug") if ev else None)

# 2 clayface event
u = "https://gamma-api.polymarket.com/events?slug=clayface-rotten-tomatoes-score-20261026"
d, st = jget(u)
print(f"\n[2] {u}\n    HTTP {st}")
if d:
    e = d[0]
    print("    endDate =", e.get("endDate"), "| closedTime =", e.get("closedTime"),
          "| negRisk =", e.get("negRisk"), "| volume =", e.get("volume"),
          "| liquidity =", e.get("liquidity"))
    print("    tags =", [(t.get("id"), t.get("slug")) for t in e.get("tags", [])])
    desc = " ".join((m.get("description") or "") for m in e.get("markets", []))
    for s in ["10:00 AM ET on October 26, 2026", "All Critics", "resolution data is unavailable",
              "October 30, 2026, 11:59 PM ET"]:
        print(f"    rule contains {s!r}:", s in desc)
    print("    resolutionSource =", repr(e.get("resolutionSource")))
    for m in sorted(e.get("markets", []), key=lambda x: (thr(x) is None, thr(x) or 0)):
        print(f"      {m.get('groupItemTitle'):>5s} bid={m.get('bestBid')} ask={m.get('bestAsk')} "
              f"outcomePrices={m.get('outcomePrices')} feeRate={(m.get('feeSchedule') or {}).get('rate')} "
              f"rewards={(m.get('clobRewards') or [{}])[0].get('rewardsDailyRate')}")

# 3 sense event
u = "https://gamma-api.polymarket.com/events?slug=sense-and-sensibility-rotten-tomatoes-score-20261019"
d, st = jget(u)
print(f"\n[3] {u}\n    HTTP {st}")
if d:
    e = d[0]
    print("    markets =", len(e.get("markets", [])), "| closedTime =", e.get("closedTime"),
          "| endDate =", e.get("endDate"), "| resolutionSource =", repr(e.get("resolutionSource")))
    yes = []
    for m in e.get("markets", []):
        t = thr(m)
        if t is None:
            continue
        op = json.loads(m.get("outcomePrices") or "[]")
        if op[:1] == ["1"]:
            yes.append(t)
        print(f"      {t:3d}+ {op} umaEndDate={m.get('umaEndDate')} "
              f"umaResolutionStatus={m.get('umaResolutionStatus')} auto={m.get('automaticallyResolved')} "
              f"bond={m.get('umaBond')} reward={m.get('umaReward')} liveness={m.get('customLiveness')}")
    print("    YES thresholds =", sorted(yes))

# 4 closed tag
u = "https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false"
d, st = jget(u)
print(f"\n[4] {u}\n    HTTP {st}")
if d:
    vols = [e.get("volume") or 0 for e in d]
    print("    events =", len(d), "| markets =", sum(len(e.get("markets", [])) for e in d),
          "| volume sum =", round(sum(vols), 2), "| median event volume =", round(statistics.median(vols), 2),
          "| max =", round(max(vols), 2))
    months = collections.Counter((e.get("endDate") or "")[:7] for e in d)
    print("    endDate months:", sorted(months.items()))

# 5 open tag
u = "https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=false&order=endDate&ascending=false"
d, st = jget(u)
print(f"\n[5] {u}\n    HTTP {st}")
if d:
    print("    events =", len(d), "| markets =", sum(len(e.get("markets", [])) for e in d),
          "| volume sum =", round(sum((e.get("volume") or 0) for e in d), 2))
    for e in d:
        print("     ", e.get("slug"), "vol", round(e.get("volume") or 0, 2),
              "end", e.get("endDate"))

# 6 culture tag
u = "https://gamma-api.polymarket.com/events?tag_slug=culture&limit=3"
d, st = jget(u)
print(f"\n[6] {u}\n    HTTP {st} | events =", len(d) if isinstance(d, list) else d)

# 7 tags
u = "https://gamma-api.polymarket.com/tags?limit=200"
d, st = jget(u)
print(f"\n[7] {u}\n    HTTP {st} | returned =", len(d) if isinstance(d, list) else d)
if isinstance(d, list):
    print("    has rotten-tomatoes:", any(t.get("slug") == "rotten-tomatoes" for t in d))

# 8 CLOB max history cited in entry
tok = "115247292569760568274899790090301720359959003343471261064290162154153281032682"
u = f"https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60"
r = get(u)
print(f"\n[8] {u}\n    HTTP {r.status_code}")
if r.status_code == 200:
    h = r.json().get("history", [])
    open(os.path.join(CACHE, "ph_max_youcansee.json"), "w").write(r.text)
    if h:
        ts = [x["t"] for x in h]; ps = [x["p"] for x in h]
        print("    points =", len(h))
        print("    first", datetime.datetime.fromtimestamp(ts[0], datetime.UTC).isoformat(), ps[0])
        print("    last ", datetime.datetime.fromtimestamp(ts[-1], datetime.UTC).isoformat(), ps[-1])
        mn = min(range(len(ps)), key=lambda i: ps[i])
        print("    min ", datetime.datetime.fromtimestamp(ts[mn], datetime.UTC).isoformat(), ps[mn])
        for days in (7, 3, 1):
            cut = ts[-1] - days * 86400
            j = max(i for i, t in enumerate(ts) if t <= cut)
            print(f"    T-{days}d p =", ps[j], "at", datetime.datetime.fromtimestamp(ts[j], datetime.UTC).isoformat())

# 9 RT pages from cache
print("\n[9] Rotten Tomatoes pages (cached 2026-10-21 by check_rounding.py)")
for slug in ["clayface", "sense_and_sensibility_2026", "other_mommy", "by_any_means"]:
    p = os.path.join(CACHE, f"rt_{slug}.html")
    if not os.path.exists(p):
        print(f"    {slug}: NOT CACHED"); continue
    h = open(p, encoding="utf-8", errors="ignore").read()
    m = re.search(r'"criticsScore":\{([^}]*)\}', h)
    print(f"    {slug}: HTTP 200 (cached, {len(h)} bytes) criticsScore={{{m.group(1) if m else 'MISSING'}}}")

# 10 reviews page dates
p = os.path.join(CACHE, "rt_sense_and_sensibility_2026.html")
print("\n[10] /reviews page (fetched live, not cached)")
r = S.get("https://www.rottentomatoes.com/m/sense_and_sensibility_2026/reviews", timeout=30)
h = r.text
print("    HTTP", r.status_code, "bytes", len(h))
for k in ["publicationDate", "reviewDate", "dateCreated", "datePublished", "createDate"]:
    print(f"    {k} occurrences:", h.count(k))

# 10b archives: document the failed attempts, do not use any number from them
print("\n[10b] archive attempts for historical (k,n)")
for u in [
    "https://archive.org/wayback/available?url=rottentomatoes.com/m/sense_and_sensibility_2026&timestamp=20261018",
    "https://web.archive.org/cdx/search/cdx?url=rottentomatoes.com/m/sense_and_sensibility_2026&output=json&limit=5",
    "https://archive.ph/newest/https://www.rottentomatoes.com/m/sense_and_sensibility_2026",
    "https://index.commoncrawl.org/CC-MAIN-2026-39-index?url=rottentomatoes.com%2Fm%2Fsense_and_sensibility_2026&output=json",
]:
    try:
        rr = S.get(u, timeout=20)
        print(f"    {u}\n      HTTP {rr.status_code} bytes {len(rr.content)}")
    except Exception as e:
        print(f"    {u}\n      ERROR {type(e).__name__}: {e}")

# 11 data-api trades
cid = "0x9bd927360a0fc46492f245d2d1bc4b6ef3fcbe750f916c59df0837b1eef259b3"
u = f"https://data-api.polymarket.com/trades?market={cid}&limit=5&offset=0"
r = get(u)
print(f"\n[11] {u}\n    HTTP {r.status_code}")
if r.status_code == 200:
    tr = r.json()
    print("    returned =", len(tr), "| keys =", sorted(tr[0].keys()) if tr else None)
    for x in tr[:5]:
        print("     ", datetime.datetime.fromtimestamp(x["timestamp"], datetime.UTC).isoformat(),
              x["side"], x["outcome"], x["price"], x["size"])
