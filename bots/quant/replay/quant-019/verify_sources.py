#!/usr/bin/env python3
"""Re-check every URL cited by the quant-019 entry (free, keyless, read-only)."""
import json
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html,application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def show(label, url):
    try:
        st, raw = get(url)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {label}: {url} -> {exc}")
        return None, None
    print(f"[OK]   {label}: HTTP {st}, {len(raw)} bytes")
    return raw, url


# 1) CDC page
raw, _ = show("CDC measles counter", "https://www.cdc.gov/measles/data-research/index.html")
if raw:
    txt = raw.decode("utf-8", "replace")
    for needle in ["4,410 confirmed measles cases", "4,392 measles cases",
                   "Updated on October 16, 2026", "12:00PM on Thursday",
                   "epidemiological week of the date of rash onset",
                   "preliminary and subject to change",
                   "Weekly measles cases by rash onset date 2022"]:
        print(f"    '{needle}': {'FOUND' if needle in txt else 'MISSING'}")
    print(f"    data csv/json download link: "
          f"{'FOUND' if '.csv' in txt else 'no .csv'}; "
          f"{'FOUND' if 'manifest.json' in txt else 'no manifest.json'}")

# 2) Gamma public search
url = "https://gamma-api.polymarket.com/public-search?q=measles&limit_per_type=100&events_status=all"
raw, _ = show("Gamma public-search measles", url)
if raw:
    d = json.loads(raw)
    evs = d["events"]
    print(f"    events: {len(evs)}")
    e = next(x for x in evs if x["slug"] == "measles-cases-in-us-in-2026")
    print(f"    in-2026 volume={e.get('volume')} liquidity={e.get('liquidity')} "
          f"openInterest={e.get('openInterest')} negRisk={e.get('negRisk')} "
          f"markets={len(e.get('markets') or [])}")

# 3) annual event
url = "https://gamma-api.polymarket.com/events?slug=measles-cases-in-us-in-2026"
raw, _ = show("Gamma annual event", url)
if raw:
    d = json.loads(raw)
    e = d[0] if isinstance(d, list) else d
    print(f"    markets={len(e['markets'])} negRisk={e.get('negRisk')} "
          f"volume={e.get('volume')} liquidity={e.get('liquidity')} "
          f"openInterest={e.get('openInterest')} volume1wk={e.get('volume1wk')} "
          f"endDate={e.get('endDate')}")
    for m in e["markets"]:
        if "7500" in (m.get("slug") or ""):
            print(f"    >=7500: feesEnabled={m.get('feesEnabled')} "
                  f"feeSchedule={m.get('feeSchedule')} tick={m.get('orderPriceMinTickSize')} "
                  f"minSize={m.get('orderMinSize')} umaBond={m.get('umaBond')} "
                  f"umaReward={m.get('umaReward')} clobRewards={m.get('clobRewards')} "
                  f"bid={m.get('bestBid')} ask={m.get('bestAsk')}")

# 4) October short ladder
url = "https://gamma-api.polymarket.com/events?slug=measles-cases-in-uptspt-by-october-31-20260928t160000000z"
raw, _ = show("Gamma Oct-31 ladder", url)
if raw:
    d = json.loads(raw)
    e = d[0] if isinstance(d, list) else d
    print(f"    markets={len(e['markets'])} volume={e.get('volume')} "
          f"liquidity={e.get('liquidity')} endDate={e.get('endDate')}")
    fees = {json.dumps(m.get("feeSchedule"), sort_keys=True) for m in e["markets"]}
    print(f"    feeSchedule set: {fees}")

# 5) single market >=7500
url = ("https://gamma-api.polymarket.com/markets?slug=will-there-be-at-least-7500-"
       "measles-cases-in-the-us-in-2026-287-181-314-511-633")
raw, _ = show("Gamma >=7500 market", url)
if raw:
    d = json.loads(raw)
    m = d[0] if isinstance(d, list) else d
    print(f"    feesEnabled={m.get('feesEnabled')} feeSchedule={m.get('feeSchedule')} "
          f"tick={m.get('orderPriceMinTickSize')} minSize={m.get('orderMinSize')} "
          f"umaBond={m.get('umaBond')} umaReward={m.get('umaReward')} "
          f"clobRewards={m.get('clobRewards')}")

# 6) bird flu
url = "https://gamma-api.polymarket.com/public-search?q=bird%20flu&limit_per_type=30&events_status=all"
raw, _ = show("Gamma bird flu search", url)
if raw:
    evs = json.loads(raw)["events"]
    print(f"    events={len(evs)} all_closed={all(x.get('closed') for x in evs)} "
          f"latest_end={max(x.get('endDate') or '' for x in evs)}")

# 7) tag search (returns a JSON array)
url = ("https://gamma-api.polymarket.com/events?tag_slug=measles&limit=100"
       "&closed=true&order=endDate&ascending=false")
raw, _ = show("Gamma measles tag closed", url)
if raw:
    d = json.loads(raw)
    print(f"    type={type(d).__name__} entries={len(d) if isinstance(d, list) else 1}")

# 8) data-api per-trade fills used by the replay
cond = "0x976617bfd741c1b8f47acf3712081614610d0dcfc05314c3cf5ec0a5f7958074"
url = f"https://data-api.polymarket.com/trades?market={cond}&limit=2"
raw, _ = show("data-api trades (March 1400 ladder)", url)
if raw:
    d = json.loads(raw)
    print(f"    rows={len(d)} first_price={d[0]['price']} side={d[0]['side']} "
          f"outcome={d[0]['outcome']} ts={d[0]['timestamp']}")
