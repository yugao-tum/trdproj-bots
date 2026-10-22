#!/usr/bin/env python3
"""Re-check every external source cited by quant-009 (free, keyless, read-only).

Run: python3 verify_sources.py | tee verify_output.txt

The script prints PASS/FAIL per claim.  Coinbase 403/404 is EXPECTED and is
recorded as a negative result (the entry says that source is unavailable), not
as a script failure.
"""
import datetime as dt
import json
import re

import requests

S = requests.Session()
S.headers["User-Agent"] = "quant-research/1.0 (public keyless data)"
OK = True


def check(name, cond, detail):
    global OK
    OK &= bool(cond)
    print(f"[{'OK  ' if cond else 'FAIL'}] {name}: {detail}")


def get(url, **params):
    return S.get(url, params=params, timeout=60)


def main():
    # --- Gamma public-search: the 4 queries used in the original entry
    search_counts = {}
    union = {}
    for q in ("listed on binance", "listed on coinbase", "listed on robinhood", "be listed"):
        r = get("https://gamma-api.polymarket.com/public-search", q=q, limit_per_type=50)
        d = r.json() if r.status_code == 200 else {}
        evs = d.get("events", [])
        search_counts[q] = len(evs)
        for e in evs:
            union.setdefault(e.get("slug"), e)
        check(f"gamma public-search q={q!r}", r.status_code == 200,
              f"HTTP {r.status_code}, events={len(evs)}")
    pat = re.compile(r"listed on (binance|coinbase|robinhood)", re.I)
    matched = [e for e in union.values() if pat.search(e.get("title", ""))]
    n_closed = sum(1 for e in matched if e.get("closed"))
    check("4-query union and title match", len(union) == 53 and len(matched) == 24 and n_closed == 24,
          f"union={len(union)} matched={len(matched)} closed={n_closed} (entry wrote 53 / 24 / 24)")

    # --- specific markets / events quoted in the entry
    m = get("https://gamma-api.polymarket.com/markets",
            slug="will-coinbase-list-hype-in-2025", closed="true").json()[0]
    desc = m.get("description", "")
    check("HYPE/Coinbase 2025 rule text",
          "listed for spot purchase on Coinbase by December 31, 2025, 11:59 PM ET" in desc
          and "consensus of credible reporting" in desc,
          f"outcomePrices={m.get('outcomePrices')}, volumeNum={m.get('volumeNum')}, "
          f"umaStatus={m.get('umaResolutionStatus')}, feeSchedule={m.get('feeSchedule')}")

    ev = get("https://gamma-api.polymarket.com/events",
             slug="hyperliquid-listed-on-coinbase-before-2027").json()[0]
    check("HYPE/Coinbase 2027 event", ev.get("closed") is True,
          f"volume={ev.get('volume')}, markets={len(ev.get('markets', []))}")

    ev = get("https://gamma-api.polymarket.com/events",
             slug="hyperliquid-listed-on-binance-by").json()[0]
    ms = ev.get("markets", [])
    sides = {x.get("slug"): x.get("outcomePrices") for x in ms}
    check("HYPE/Binance by-event (2 markets)", ev.get("closed") is True and len(ms) == 2,
          f"volume={ev.get('volume')}, outcomePrices={sides}")

    m = get("https://gamma-api.polymarket.com/markets",
            slug="penguin-listed-on-binance-by-march-31", closed="true").json()[0]
    check("PENGUIN contract address in rule",
          "8Jx8AAHj86wbQgUTjGuj6GTTL5Ps3cqxKRTvpaJApump" in (m.get("description") or ""),
          f"volumeNum={m.get('volumeNum')}, outcomePrices={m.get('outcomePrices')}")

    m = get("https://gamma-api.polymarket.com/markets",
            slug="will-fartcoin-be-listed-on-robinhood-before-june", closed="true").json()[0]
    check("FARTCOIN/Robinhood U.S. rule",
          "Robinhood U.S." in (m.get("description") or ""),
          f"volumeNum={m.get('volumeNum')}, endDate={m.get('endDate')}")

    # --- Binance CMS: catalog size, HYPE release timestamp, open-trading text
    d = get("https://www.binance.com/bapi/composite/v1/public/cms/article/list/query",
            type=1, pageNo=1, pageSize=20).json()["data"]
    cat = next(c for c in d["catalogs"] if c.get("catalogId") == 48)
    art = next(a for a in cat["articles"] if a.get("code") == "d49de208bb6d4a26b02677d7c3d89b5d")
    release = dt.datetime.fromtimestamp(art["releaseDate"] / 1000, tz=dt.timezone.utc)
    check("Binance catalog 48 total / HYPE releaseDate",
          release.strftime("%Y-%m-%d %H:%M") == "2026-09-24 07:30",
          f"catalog total={cat['total']} (entry saw 2283 on 2026-10-20), "
          f"HYPE releaseDate={release.isoformat()}")

    det = get("https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query",
              articleCode="d49de208bb6d4a26b02677d7c3d89b5d").json()["data"]
    body = json.dumps(det, ensure_ascii=False)
    has_open = "2026-09-24 11:00 (UTC)" in body
    has_wd = "2026-09-25 11:00 (UTC)" in body
    check("Binance HYPE article times", det.get("title") == "Binance Will List Hyperliquid (HYPE) with Seed Tag Applied"
          and has_open and has_wd,
          f"title={det.get('title')!r}, open_trading_11:00={has_open}, withdrawals_next_day={has_wd}")

    # --- data-api trades: fields and a real closed-market fill used by the replay
    cid = "0xa647149953da495e58a3ecc417c9edfed9f71e74265433507bb84ea7a425fbad"
    r = get("https://data-api.polymarket.com/trades", market=cid, limit=5, offset=0,
            start=1735040000, end=1735042000)
    rows = r.json() if r.status_code == 200 else []
    need = {"side", "price", "size", "timestamp", "outcome"}
    check("data-api trades fields", r.status_code == 200 and bool(rows) and need <= set(rows[0]),
          f"HTTP {r.status_code}, n={len(rows)}, fields={sorted(rows[0]) if rows else []}")

    # --- CLOB prices-history: the exact cited request
    token = "72111237001093028212763921723631481836210139498389057357896030642910594584975"
    r = get("https://clob.polymarket.com/prices-history",
            market=token, startTs=1766707200, endTs=1767225600, fidelity=60)
    hist = r.json().get("history", []) if r.status_code == 200 else []
    first = hist[0] if hist else {}
    check("CLOB prices-history cited token", r.status_code == 200 and first.get("p") == 0.011,
          f"HTTP {r.status_code}, points={len(hist)}, first={first} (entry wrote t=1766707211, p=0.011)")

    # --- sources the entry records as unavailable (expected failures)
    for url, want in (("https://www.coinbase.com/blog/listing", 403),
                      ("https://www.coinbase.com/blog/rss", 403),
                      ("https://www.coinbase.com/rss/blog?category=listing", 404)):
        try:
            r = S.get(url, timeout=30, allow_redirects=True)
            check(f"Coinbase unavailable as recorded {url.split('coinbase.com')[1]}",
                  r.status_code == want, f"HTTP {r.status_code} (expected {want})")
        except Exception as e:
            check(f"Coinbase unavailable as recorded {url}", False, f"exception {e}")

    try:
        r = S.get("https://archive.org/wayback/available",
                  params={"url": "www.coinbase.com/blog/listing"}, timeout=60)
        if r.status_code == 429:
            print("[INFO] Wayback snapshot check: HTTP 429 (rate-limited today); "
                  "entry result from 2026-10-20 was archived_snapshots={} and is kept as-is")
        else:
            ok = r.status_code == 200 and r.json().get("archived_snapshots") == {}
            check("Wayback has no Coinbase listing snapshot", ok,
                  f"HTTP {r.status_code}, body={r.text[:120]}")
    except Exception as e:
        print(f"[INFO] Wayback check skipped: {e}")

    print(f"\nALL EXTERNAL CHECKS PASS: {OK}")


if __name__ == "__main__":
    main()
