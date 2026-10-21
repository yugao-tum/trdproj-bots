#!/usr/bin/env python3
"""Verify every URL cited by bots/quant/entries/quant-014-pm-spx-lognormal-calibration.md.

Read-only, keyless public GETs.  Time-varying quotes are re-read but NOT asserted
to equal the 2026-10-20 snapshot; only rules, structure and the as-of-2026-10-19
Yahoo sample are asserted.  Run:
    python3 verify_sources.py
"""
import datetime as dt
import json
import math
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

UA = {"User-Agent": "Mozilla/5.0 (research; quant-014 source verification)"}
S = requests.Session()
S.headers.update(UA)
OK = 0
FAIL = 0


def check(name, cond, detail=""):
    global OK, FAIL
    if cond:
        OK += 1
        print("OK   %-56s %s" % (name, detail))
    else:
        FAIL += 1
        print("FAIL %-56s %s" % (name, detail))


def _fee(m):
    f = m.get("feeSchedule")
    return f if isinstance(f, dict) else json.loads(f)


def get(url, **kw):
    r = S.get(url, timeout=kw.pop("timeout", 45), **kw)
    r.raise_for_status()
    return r


def main():
    print("quant-014 source verification, %s UTC" % dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"))
    print("=" * 100)

    # 1. daily Up/Down event: rules + resolution source + fee
    u = "https://gamma-api.polymarket.com/events?slug=spx-up-or-down-on-october-20-2026"
    e = get(u).json()[0]
    m = e["markets"][0]
    desc = e.get("description", "")
    check("daily event HTTP/JSON", bool(e.get("slug")), e["slug"])
    check("daily rule: official SPX closing price", "official S&P 500 Index closing price" in desc)
    check("daily rule: exactly equal -> 50-50", "exactly equal" in desc and "50-50" in desc)
    check("daily rule: WSJ Historical Prices", "Wall Street Journal" in desc and "Historical Prices" in desc)
    check("daily resolutionSource = WSJ", e.get("resolutionSource") == "https://www.wsj.com/market-data/stocks",
          str(e.get("resolutionSource")))
    check("daily endDate = 2026-10-20T20:00:00Z", e.get("endDate") == "2026-10-20T20:00:00Z", str(e.get("endDate")))
    check("daily startDate = 2026-10-19T12:00:52Z", e.get("startDate") == "2026-10-19T12:00:52Z", str(e.get("startDate")))
    # Time-varying: the 2026-10-20 snapshot showed rate 0.04; as of 2026-10-21 these
    # SPX finance markets report feeType=zero_fees / rate=0.  Record, do not assert.
    print("TIME daily feeSchedule now %s (entry snapshot 2026-10-20: rate=0.04)"
          % _fee(m))
    check("daily feeSchedule is a recognised taker schedule", _fee(m).get("takerOnly") is True)
    check("daily resolved now (outcomePrices 1/0)", json.loads(m["outcomePrices"]) in (["1", "0"], ["0", "1"]),
          m["outcomePrices"])

    # 2. Dec close ladder: rules + Yahoo source + six brackets
    u = "https://gamma-api.polymarket.com/events?slug=spx-close-dec-2026"
    e2 = get(u).json()[0]
    d2 = e2.get("description", "")
    check("Dec ladder HTTP/JSON", bool(e2.get("slug")), e2["slug"])
    check("Dec ladder rule: final trading day Dec 2026", "final trading day of December 2026" in d2)
    check("Dec ladder rule: between brackets -> higher", "falls exactly between two brackets" in d2
          and "higher range bracket" in d2)
    check("Dec ladder rule: Yahoo ^GSPC source", "finance.yahoo.com/quote/%5EGSPC/history" in d2)
    check("Dec ladder has 6 markets", len(e2.get("markets", [])) == 6, str(len(e2.get("markets", []))))
    check("Dec ladder endDate = 2026-12-31T21:00:00Z", e2.get("endDate") == "2026-12-31T21:00:00Z",
          str(e2.get("endDate")))
    print("     Dec ladder groupItemTitles: %s" % [x.get("groupItemTitle") for x in e2["markets"]])

    # 3. series 10383: 100 closed events, month counts, total volume
    u = ("https://gamma-api.polymarket.com/events?series_id=10383&limit=100&closed=true"
         "&order=endDate&ascending=false")
    ev = get(u).json()
    months = {}
    for x in ev:
        months[x["endDate"][:7]] = months.get(x["endDate"][:7], 0) + 1
    vol = sum(float(x.get("volume") or 0) for x in ev)
    check("series 10383 returns 100 closed events", len(ev) == 100, str(len(ev)))
    mm = {k: months.get(k, 0) for k in ("2026-06", "2026-07", "2026-08", "2026-09", "2026-10")}
    check("series 10383 month counts 06..09 = 21 each, Oct >=13", mm["2026-06"] == 21 and
          mm["2026-07"] == 21 and mm["2026-08"] == 21 and mm["2026-09"] == 21 and mm["2026-10"] >= 13, str(mm))
    check("series 10383 total volume ~10.7-10.8m (self-reported)", 10_700_000 < vol < 10_900_000, "%.2f" % vol)

    # 4. CLOB prices-history: the cited Oct-16 token has data, Sep-18 token is empty
    tok_oct16 = "37867517699597038332707589432698261528449111760519164430714310172860137405315"
    tok_sep18 = "56470952261346405661865784125968649112655146418378832479574947524904990438477"
    h1 = get("https://clob.polymarket.com/prices-history?market=%s&interval=max&fidelity=60" % tok_oct16).json()["history"]
    h2 = get("https://clob.polymarket.com/prices-history?market=%s&interval=max&fidelity=60" % tok_sep18).json()["history"]
    check("CLOB 2026-10-16 closed market has price history", len(h1) > 0, "%d points" % len(h1))
    check("CLOB 2026-09-18 closed market returns empty history", h2 == [], str(h2[:1]))

    def hist_len(x):
        tok = json.loads(x["markets"][0]["clobTokenIds"])[0]
        try:
            return len(S.get("https://clob.polymarket.com/prices-history?market=%s&interval=max&fidelity=60"
                               % tok, timeout=30).json().get("history", []))
        except Exception:
            return -1

    with ThreadPoolExecutor(max_workers=8) as pool:
        lens = list(pool.map(hist_len, ev))
    n_hist = sum(1 for n in lens if n > 0)
    check("CLOB history coverage on 100 closed events (entry said 21; now 22)",
          n_hist in (21, 22), "%d/100 non-empty" % n_hist)

    # 5. NVDA close-above ladder: Pyth, equal->No, five strikes
    u = "https://gamma-api.polymarket.com/events?slug=nvda-close-above-on-october-20-2026"
    e3 = get(u).json()[0]
    d3 = e3.get("description", "")
    strikes = [x.get("groupItemTitle") for x in e3.get("markets", [])]
    check("NVDA event HTTP/JSON", bool(e3.get("slug")), e3["slug"])
    check("NVDA rule: Pyth closing price, no rounding", "published by Pyth" in d3 and "without rounding" in d3)
    check("NVDA rule: equal -> No", "exactly equal" in d3 and "resolve to \"No\"" in d3)
    check("NVDA has 5 strikes 210..230", len(strikes) == 5, str(strikes))
    print("TIME NVDA feeSchedule now %s (entry snapshot 2026-10-20: rate=0.04)"
          % _fee(e3["markets"][0]))
    check("NVDA feeSchedule is a recognised taker schedule", _fee(e3["markets"][0]).get("takerOnly") is True)

    # 6. public-search endpoints cited
    for q, needles in (("SPX", ("spx-up-or-down-on-", "spx-close-", "spx-hit-")),
                       ("NVDA", ("what-price-will-nvda-hit-in-october-2026",))):
        u = "https://gamma-api.polymarket.com/public-search?q=%s&limit_per_type=20&events_status=all" % q
        data = get(u).json()
        slugs = [x.get("slug", "") for x in data.get("events", [])]
        check("public-search q=%s" % q, all(any(n in s for s in slugs) for n in needles),
              "%d events" % len(slugs))

    # 7. Yahoo ^SPX, replay input; assert as-of-2026-10-19 numbers in the entry
    u = "https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=6y&interval=1d"
    y = get(u).json()["chart"]["result"][0]
    ts = y["timestamp"]
    cl = y["indicators"]["quote"][0]["close"]
    rows = sorted((dt.datetime.fromtimestamp(t, dt.timezone.utc).date(), c) for t, c in zip(ts, cl) if c)
    rows = [r for r in rows if dt.date(2021, 10, 20) <= r[0] <= dt.date(2026, 10, 19)]
    dates = [r[0] for r in rows]
    closes = [r[1] for r in rows]
    lr = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    rv = lambda n: statistics.stdev(lr[-n:]) * math.sqrt(252.0)
    check("Yahoo as-of 2026-10-19 has 1,254 bars", len(closes) == 1254, str(len(closes)))
    check("Yahoo first/last 2021-10-20..2026-10-19", (dates[0].isoformat(), dates[-1].isoformat()) ==
          ("2021-10-20", "2026-10-19"), "%s..%s" % (dates[0], dates[-1]))
    check("Yahoo 2021-10-20 close 4536.19", abs(closes[0] - 4536.19) < 0.005, "%.2f" % closes[0])
    check("Yahoo 2026-10-19 close 7690.73", abs(closes[-1] - 7690.73) < 0.005, "%.2f" % closes[-1])
    check("sigma20 = 0.0904", abs(rv(20) - 0.0904) < 0.0001, "%.4f" % rv(20))
    check("sigma60 = 0.1100", abs(rv(60) - 0.1100) < 0.0001, "%.4f" % rv(60))
    check("sigma252 = 0.1271", abs(rv(252) - 0.1271) < 0.0001, "%.4f" % rv(252))
    up = sum(1 for x in lr if x > 0)
    check("up days 664/1253", (up, len(lr)) == (664, 1253), "%d/%d" % (up, len(lr)))

    # 8. data-api per-trade fills, the round-2 execution source
    cid = "0x223e81ff2ad483a001bdfc50a14e7d55d805980e3a84507b43ba7880e27c21cb"
    tr = get("https://data-api.polymarket.com/trades?market=%s&limit=5" % cid).json()
    check("data-api /trades returns per-trade fills", isinstance(tr, list) and len(tr) > 0, "%d rows" % len(tr))
    check("data-api trade has timestamp/price/side/outcome",
          all(k in tr[0] for k in ("timestamp", "price", "side", "outcome", "conditionId")))

    # 9. stooq: the entry says it is blocked by a JS challenge; verify failure
    r = S.get("https://stooq.com/q/d/l/?s=%5Espx&i=d", timeout=45)
    check("stooq still returns JS challenge (entry did not use it)",
          r.status_code == 200 and "requires JavaScript" in r.text and "Date,Open" not in r.text,
          "HTTP %d, %d bytes" % (r.status_code, len(r.content)))

    # 10. FRED, the replay's model input (not in the entry's citation list)
    try:
        r = S.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500", timeout=25)
        ok = r.status_code == 200 and r.text.startswith("observation_date")
        check("FRED SP500 CSV reachable now", ok, "HTTP %d, %d bytes" % (r.status_code, len(r.content)))
    except Exception as exc:
        print("WARN FRED SP500 CSV not reachable from this worker now: %r" % exc)
        print("     (merged q014-hist fetched it on 2026-10-20; replay.py has a Yahoo fallback)")

    print("=" * 100)
    print("checks OK=%d FAIL=%d" % (OK, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
