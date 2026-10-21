#!/usr/bin/env python3
"""Spot-check CLOB prices-history prices against data-api executed trades.

For three events, walk data-api trades backwards from the settlement end and
take the last taker BUY of the YES token at/before entry_ts. Print both prices.
"""
import json, os, urllib.request, time

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_cache")
UA = "Mozilla/5.0"
df = __import__("pandas").read_csv(os.path.join(HERE, "backtest_raw.csv"))
ev = json.load(open(os.path.join(CACHE, "closed.json")))
by_slug = {e["slug"]: e for e in ev}

CHECK = [
    "which-company-has-the-best-ai-model-end-of-september-20260717143435868",
    "which-company-has-the-best-ai-model-end-of-april",
    "which-company-has-best-ai-model-end-of-april",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read())


for slug in CHECK:
    row = df[(df.slug == slug) & (df.lead == 7)].iloc[0]
    e = by_slug[slug]
    arm = row.lb_arm
    m = [x for x in e["markets"] if x["groupItemTitle"] == arm][0]
    asset = json.loads(m["clobTokenIds"])[0]
    entry = int(row.entry_ts)
    got, off, pages = None, 0, 0
    while pages < 25:
        url = ("https://data-api.polymarket.com/trades?market=%s&limit=1000&offset=%d"
               % (m["conditionId"], off))
        try:
            batch = fetch(url)
        except Exception as ex:
            print("FAIL", slug, ex)
            break
        pages += 1
        if not batch:
            break
        cand = [t for t in batch if t["timestamp"] <= entry and t["asset"] == asset]
        if cand:
            buys = [t for t in cand if t["side"] == "BUY"]
            got = max(buys or cand, key=lambda t: t["timestamp"])
            break
        if batch[-1]["timestamp"] < entry - 3 * 86400:
            break
        off += 1000
        time.sleep(0.15)
    print("%-62s arm=%-9s px_hist=%.4f  trades_page=%d" % (slug[:62], arm, row.lb_price, pages))
    if got:
        print("   data-api last fill <= entry: side=%s price=%.4f size=%.2f ts=%d (entry=%d, %.1fh before)"
              % (got["side"], got["price"], got["size"], got["timestamp"], entry,
                 (entry - got["timestamp"]) / 3600))
    else:
        print("   data-api: no trade <= entry within %d pages (未取到)" % pages)
