#!/usr/bin/env python3
"""Re-check every URL cited in quant-016 and the numeric claims attached to it.

Access date is fixed to 2026-10-21 UTC. Keyless public GET only. Large responses are
processed in memory (not written) so every cached file stays < 1 MB.
"""
import json, re, statistics, time, datetime as dt
import requests

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15"}
S = requests.Session(); S.headers.update(UA)
ACCESS = "2026-10-21"
PASS = FAIL = 0


def get(url, params=None, tries=3):
    for i in range(tries):
        try:
            r = S.get(url, params=params, timeout=40)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (i + 1)); continue
            return r
        except Exception as e:
            err = e
            time.sleep(1.5 * (i + 1))
    return None


def check(name, cond, detail):
    global PASS, FAIL
    if cond: PASS += 1; tag = "PASS"
    else: FAIL += 1; tag = "FAIL"
    print(f"[{tag}] {name}: {detail}")


def rt_critics(slug):
    r = get(f"https://www.rottentomatoes.com/m/{slug}")
    if r is None:
        return None, "GET failed"
    m = re.search(r'"criticsScore":\{([^}]*)\}', r.text)
    if not m:
        return None, f"HTTP {r.status_code}, no criticsScore"
    try:
        d = json.loads("{" + m.group(1) + "}")
    except Exception as e:
        return None, f"HTTP {r.status_code}, unparsable ({e})"
    return d, f"HTTP {r.status_code}, {len(r.content)} bytes"


print("access date:", ACCESS, "UTC\n")
print("== Gamma ==")
r = get("https://gamma-api.polymarket.com/public-search?q=rotten%20tomatoes&limit_per_type=100")
j = r.json() if r is not None and r.status_code == 200 else {}
evs = j.get("events", [])
pat = re.compile(r"^.+rotten-tomato(?:es)?-score(?:-\d+)?$")
check("public-search", r is not None and r.status_code == 200 and j.get("pagination", {}).get("totalResults") == 163,
      f"HTTP {getattr(r,'status_code',None)}, totalResults={j.get('pagination',{}).get('totalResults')}, events={len(evs)}, family-pattern={sum(1 for e in evs if pat.match(e.get('slug','')))}/{len(evs)}, 8-digit={sum(1 for e in evs if re.search(r'-score-\d{8}$',e.get('slug','')))}, 17-digit={sum(1 for e in evs if re.search(r'-score-\d{17}$',e.get('slug','')))}, no-suffix={sum(1 for e in evs if re.search(r'-score$',e.get('slug','')))}")

r = get("https://gamma-api.polymarket.com/events", params={"slug": "clayface-rotten-tomatoes-score-20261026"})
ev = (r.json() or [{}])[0] if r is not None and r.status_code == 200 else {}
rule = ev.get("description", "") or ""
mk = ev.get("markets", [])
fsraw = mk[0].get("feeSchedule") if mk else None
fs = json.loads(fsraw) if isinstance(fsraw, str) else (fsraw or {})
labels = [m.get("groupItemTitle") for m in mk]
check("clayface rules", "10:00 AM ET on October 26, 2026" in rule and "All Critics" in rule and "resolution data is unavailable" in rule and "October 30, 2026, 11:59 PM ET" in rule and ev.get("resolutionSource") == "",
      f"HTTP {getattr(r,'status_code',None)}, endDate={ev.get('endDate')}, markets={len(mk)}, labels={labels}, resolutionSource={ev.get('resolutionSource')!r}, feeRate={fs.get('rate')}, volume={ev.get('volume')}")

r = get("https://gamma-api.polymarket.com/events", params={"slug": "sense-and-sensibility-rotten-tomatoes-score-20261019"})
ev2 = (r.json() or [{}])[0] if r is not None and r.status_code == 200 else {}
mk2 = ev2.get("markets", [])
yes = []
for m in mk2:
    try: op = json.loads(m.get("outcomePrices") or "[]")
    except Exception: op = []
    if op and float(op[0]) == 1: yes.append(m.get("groupItemTitle"))
check("sense event", r is not None and r.status_code == 200 and len(mk2) == 11 and ev2.get("closedTime") == "2026-10-19T16:03:29Z",
      f"HTTP {getattr(r,'status_code',None)}, markets={len(mk2)}, closedTime={ev2.get('closedTime')}, YES labels={yes}")

r = get("https://gamma-api.polymarket.com/events", params={"tag_slug": "rotten-tomatoes", "limit": 500, "closed": "true", "order": "endDate", "ascending": "false"})
evs = r.json() if r is not None and r.status_code == 200 else []
vols = [float(e.get("volume") or 0) for e in evs]
months = {}
for e in evs:
    ed = e.get("endDate") or ""
    months[ed[:7]] = months.get(ed[:7], 0) + 1
nmk = sum(len(e.get("markets", [])) for e in evs)
check("closed events", r is not None and r.status_code == 200 and len(evs) == 85 and nmk == 530 and abs(sum(vols) - 1818572.46) < 0.01,
      f"HTTP {getattr(r,'status_code',None)}, events={len(evs)}, markets={nmk}, volume_sum={sum(vols):.2f}, median={statistics.median(vols):.2f}, max={max(vols):.2f}, months={sorted(months.items())}")

r = get("https://gamma-api.polymarket.com/events", params={"tag_slug": "rotten-tomatoes", "limit": 500, "closed": "false", "order": "endDate", "ascending": "false"})
evs = r.json() if r is not None and r.status_code == 200 else []
vols = [float(e.get("volume") or 0) for e in evs]
nmk = sum(len(e.get("markets", [])) for e in evs)
check("open events snapshot (may drift)", r is not None and r.status_code == 200 and len(evs) == 9,
      f"HTTP {getattr(r,'status_code',None)}, events={len(evs)}, markets={nmk}, volume_sum={sum(vols):.2f}, slugs={[e.get('slug') for e in evs]}")

r = get("https://gamma-api.polymarket.com/events", params={"tag_slug": "culture", "limit": 3})
evs = r.json() if r is not None and r.status_code == 200 else []
check("culture tag endpoint", r is not None and r.status_code == 200 and len(evs) == 0,
      f"HTTP {getattr(r,'status_code',None)}, events={len(evs)}")

r = get("https://gamma-api.polymarket.com/tags", params={"limit": 200})
tags = r.json() if r is not None and r.status_code == 200 else []
slugs = [t.get("slug") for t in tags]
check("tags endpoint", r is not None and r.status_code == 200 and len(tags) == 100 and "rotten-tomatoes" not in slugs,
      f"HTTP {getattr(r,'status_code',None)}, returned={len(tags)} (requested 200), has rotten-tomatoes={'rotten-tomatoes' in slugs}")

print("\n== CLOB / data-api ==")
r = get("https://clob.polymarket.com/prices-history", params={"market": "115247292569760568274899790090301720359959003343471261064290162154153281032682", "interval": "max", "fidelity": 60})
h = r.json().get("history", []) if r is not None and r.status_code == 200 else []
fmt = lambda t: dt.datetime.fromtimestamp(int(t), tz=dt.timezone.utc).isoformat()
if h:
    first, last = h[0], h[-1]
    lo = min(h, key=lambda x: float(x["p"]))
    byt = {fmt(x["t"]): float(x["p"]) for x in h}
    check("CLOB prices-history", r.status_code == 200 and len(h) == 564,
          f"HTTP {r.status_code}, points={len(h)}, first={fmt(first['t'])} {first['p']}, last={fmt(last['t'])} {last['p']}, min={fmt(lo['t'])} {lo['p']}")
else:
    check("CLOB prices-history", False, f"HTTP {getattr(r,'status_code',None)}, points=0")

r = get("https://data-api.polymarket.com/trades", params={"market": "0x9bd927360a0fc46492f245d2d1bc4b6ef3fcbe750f916c59df0837b1eef259b3", "limit": 5, "offset": 0})
tr = r.json() if r is not None and r.status_code == 200 else []
need = {"side", "outcome", "price", "size", "timestamp"}
check("data-api trades", r is not None and r.status_code == 200 and len(tr) == 5 and need <= set(tr[0].keys()) if tr else False,
      f"HTTP {getattr(r,'status_code',None)}, returned={len(tr)}, fields_ok={bool(tr) and need <= set(tr[0].keys())}, first={tr[0].get('timestamp') if tr else None} {tr[0].get('side') if tr else None} {tr[0].get('outcome') if tr else None} {tr[0].get('price') if tr else None}")

print("\n== Rotten Tomatoes ==")
for slug, exp_k, exp_m, exp_score in [("clayface", 0, 0, None),
                                      ("sense_and_sensibility_2026", 82, 24, "77"),
                                      ("other_mommy", 16, 73, "18"),
                                      ("by_any_means", 0, 0, None)]:
    d, msg = rt_critics(slug)
    if d is None:
        check(f"RT {slug}", False, msg); continue
    k, m = int(d.get("likedCount") or 0), int(d.get("notLikedCount") or 0)
    sc = d.get("score")
    ok = (k, m, sc) == (exp_k, exp_m, exp_score)
    check(f"RT {slug}", ok, f"{msg}; criticsScore k={k}, notLiked={m}, reviewCount={d.get('reviewCount')}, score={sc!r} (entry: k={exp_k}, m={exp_m}, score={exp_score!r})")

r = get("https://www.rottentomatoes.com/m/sense_and_sensibility_2026/reviews")
txt = r.text if r is not None and r.status_code == 200 else ""
found = {k: len(re.findall(k, txt)) for k in ["publicationDate", "reviewDate", "dateCreated", "datePublished", "createDate"]}
check("RT /reviews has no dates", r is not None and r.status_code == 200 and sum(found.values()) == 0,
      f"HTTP {getattr(r,'status_code',None)}, bytes={len(r.content) if r is not None else 0}, date-field matches={found}")

print("\n== rounding samples (entry says 22/22 round, 12 decisive) ==")
for slug, ek, em, esc in [("the_wild_robot", 252, 261, 97), ("inside_out_2", 298, 329, 91),
                          ("klara_and_the_sun", 5, 21, 24), ("wicked_for_good", 234, 356, 66),
                          ("project_hail_mary", 407, 430, 95)]:
    d, msg = rt_critics(slug)
    if d is None:
        check(f"rounding {slug}", False, msg); continue
    k, m = int(d.get("likedCount") or 0), int(d.get("notLikedCount") or 0)
    n = k + m; raw = 100.0 * k / n if n else None
    sc = d.get("score")
    check(f"rounding {slug}", n > 0 and sc is not None and int(raw + 0.5) == int(sc),
          f"{msg}; k={k}, n={n}, raw={raw:.4f}, score={sc}, round={int(raw+0.5) if n else None}, floor={int(raw//1) if n else None} (entry: k={ek}, n={em}, score={esc})")

print("\n== archive / historical snapshots ==")
for name, url in [
    ("Wayback availability", "https://archive.org/wayback/available?url=rottentomatoes.com/m/sense_and_sensibility_2026&timestamp=20261018"),
    ("Wayback CDX", "https://web.archive.org/cdx/search/cdx?url=rottentomatoes.com/m/the_sheep_detectives&output=json&limit=3"),
    ("archive.ph", "https://archive.ph/newest/https://www.rottentomatoes.com/m/sense_and_sensibility_2026"),
    ("Common Crawl index", "https://index.commoncrawl.org/CC-MAIN-2026-39-index?url=rottentomatoes.com%2Fm%2Fsense_and_sensibility_2026&output=json"),
]:
    r = get(url, tries=1)
    check(name + " (current access)", r is not None and r.status_code == 200,
          f"HTTP {getattr(r,'status_code',None)}" + (f", bytes={len(r.content)}" if r is not None else ", exception/TLS failure"))

r = get("https://web.archive.org/web/20260508165855id_/https://www.rottentomatoes.com/m/the_sheep_detectives", tries=1)
ok = r is not None and r.status_code == 200 and '"criticsScore"' in r.text
detail = f"HTTP {getattr(r,'status_code',None)}"
if ok:
    d, _ = None, None
    m = re.search(r'"criticsScore":\{([^}]*)\}', r.text)
    try:
        d = json.loads("{" + m.group(1) + "}") if m else {}
    except Exception: d = {}
    detail += f", archived criticsScore k={d.get('likedCount')}, notLiked={d.get('notLikedCount')}, reviewCount={d.get('reviewCount')}, score={d.get('score')!r} (q016-hist spot check: 101/5/106/95)"
check("q016-hist archived snapshot spot check", ok, detail)

print(f"\nsummary: PASS={PASS} FAIL={FAIL}")
