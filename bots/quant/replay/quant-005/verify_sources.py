#!/usr/bin/env python3
"""Re-fetch every source cited by quant-005 and check the specific claims."""
import json, sys, time
from datetime import datetime, timezone
import requests

UA = {"User-Agent": "Mozilla/5.0 (quant-005 source check; keyless)"}
OUT = {}

def get(url, params=None):
    r = requests.get(url, params=params, headers=UA, timeout=60)
    return r.status_code, r

def show(label, ok, detail):
    print(f"[{'OK ' if ok else 'BAD'}] {label}: {detail}")
    OUT[label] = {"ok": bool(ok), "detail": detail}

def main():
    # 1. current Elon 48h example event
    u = "https://gamma-api.polymarket.com/events"
    sc, r = get(u, {"slug": "elon-musk-of-tweets-october-19-october-21-2026"})
    ev = r.json()[0] if sc == 200 and r.json() else None
    if ev:
        ms = ev.get("markets", [])
        rates = sorted({(m.get("feeSchedule") or {}).get("rate") for m in ms if isinstance(m.get("feeSchedule"), dict)})
        labels = [m.get("groupItemTitle") for m in ms]
        show("Elon 48h event exists", True,
             f"title={ev.get('title')!r} endDate={ev.get('endDate')} negRisk={ev.get('negRisk')} restricted={ev.get('restricted')} series={ev.get('series',[{}])[0].get('id') if ev.get('series') else None} n_markets={len(ms)}")
        show("Elon 48h brackets", labels == ['<40','40-64','65-89','90-114','115-139','140-164','165-189','190-214','215-239','240+'], str(labels))
        show("Elon 48h fee rate", rates == [0.05], f"rates={rates}")
        OUT["elon_event_id"] = ev.get("id")
        OUT["elon_condition_40_64"] = next((m.get("conditionId") for m in ms if m.get("groupItemTitle") == "40-64"), None)
    else:
        show("Elon 48h event exists", False, f"HTTP {sc}")

    # 2. settled event and resolution
    sc, r = get(u, {"slug": "elon-musk-of-tweets-october-17-october-19-2026"})
    ev2 = r.json()[0] if sc == 200 and r.json() else None
    if ev2:
        m = next((m for m in ev2.get("markets", []) if m.get("groupItemTitle") == "40-64"), None)
        op = json.loads(m.get("outcomePrices")) if m and m.get("outcomePrices") else None
        show("Settled Oct17-19 exists", True,
             f"closed={ev2.get('closed')} winner_40_64={op} status={m.get('umaResolutionStatus') if m else None} closedTime={m.get('closedTime') if m else None}")
        show("Settled 40-64 is Yes", op == [1.0, 0.0] or op == ["1", "0"], f"outcomePrices={m.get('outcomePrices') if m else None}")
        show("resolvedBy", bool(m and m.get("resolvedBy")), str(m.get("resolvedBy") if m else None))
    else:
        show("Settled Oct17-19 exists", False, f"HTTP {sc}")

    # 3. Trump event
    sc, r = get(u, {"slug": "donald-trump-of-truth-social-posts-october-20-october-27-2026"})
    ev3 = r.json()[0] if sc == 200 and r.json() else None
    if ev3:
        ms = ev3.get("markets", [])
        show("Trump 7d event exists", True,
             f"title={ev3.get('title')!r} endDate={ev3.get('endDate')} n_markets={len(ms)}")
        show("Trump brackets count 11", len(ms) == 11, f"n={len(ms)} first={ms[0].get('groupItemTitle') if ms else None} last={ms[-1].get('groupItemTitle') if ms else None}")
        show("Trump fee rate", all(((m.get('feeSchedule') or {}).get('rate') == 0.05) for m in ms), "all rate=0.05" if ms else "no markets")
    else:
        show("Trump 7d event exists", False, f"HTTP {sc}")

    # 4. series 10816 closed count by pagination
    n, first, last, off = 0, None, None, 0
    while off < 5000:
        sc, r = get(u, {"series_id": 10816, "closed": "true", "limit": 100, "offset": off})
        page = r.json() if sc == 200 else []
        if not page:
            break
        n += len(page)
        ds = [e.get("endDate") for e in page if e.get("endDate")]
        if ds:
            first = min(ds) if first is None else min(first, min(ds))
            last = max(ds) if last is None else max(last, max(ds))
        if len(page) < 100:
            break
        off += 100
    show("series 10816 paginates", n >= 100, f"closed_events={n} span={first}..{last}")

    # 5. xtracker posts
    sc, r = get("https://xtracker.polymarket.com/api/users/elonmusk/posts", {"limit": 100, "offset": 0})
    d = r.json() if sc == 200 else {}
    rows = d.get("data", d) if isinstance(d, dict) else d
    ts = sorted(x["createdAt"] for x in rows if x.get("createdAt"))
    show("Elon posts feed", sc == 200 and len(ts) > 1000, f"HTTP {sc} posts={len(ts)} first={ts[0] if ts else None} last={ts[-1] if ts else None}")
    # count posts in the settled 48h window [2026-10-17T16:00Z, 2026-10-19T16:00Z)
    lo = "2026-10-17T16:00:00"
    hi = "2026-10-19T16:00:00"
    cnt = sum(1 for t in ts if lo <= t[:19] < hi)
    show("Settled window tracker count", cnt == 62, f"posts in [2026-10-17T16:00Z,2026-10-19T16:00Z)={cnt} (entry claims 62)")

    # 6. data-api trades on the 40-64 settled market
    if OUT.get("elon_condition_40_64"):
        cid = OUT["elon_condition_40_64"]
        sc, r = get("https://data-api.polymarket.com/trades", {"market": cid, "limit": 500, "offset": 0})
        tr = r.json() if sc == 200 else []
        show("data-api trades", sc == 200 and isinstance(tr, list) and len(tr) > 0,
             f"conditionId={cid} HTTP={sc} n_first_page={len(tr)} sample={tr[0] if tr else None}")

    # 7. CLOB prices-history for the settled 40-64 YES token
    if ev2:
        m = next((m for m in ev2.get("markets", []) if m.get("groupItemTitle") == "40-64"), None)
        toks = json.loads(m.get("clobTokenIds")) if m and m.get("clobTokenIds") else []
        if toks:
            sc, r = get("https://clob.polymarket.com/prices-history", {"market": toks[0], "interval": "max", "fidelity": 60})
            h = (r.json() or {}).get("history", []) if sc == 200 else []
            show("CLOB prices-history", sc == 200 and len(h) > 0,
                 f"HTTP={sc} points={len(h)} first={h[0] if h else None} last={h[-1] if h else None}")

    # 8. public-search counter
    sc, r = get("https://gamma-api.polymarket.com/public-search",
                {"q": "elon musk tweets", "limit_per_type": 25, "events_status": "closed", "page": 1})
    j = r.json() if sc == 200 else {}
    show("public-search", sc == 200, f"HTTP={sc} totalResults={(j.get('pagination') or {}).get('totalResults')}")

    with open("source_check.json", "w", encoding="utf-8") as f:
        json.dump(OUT, f, indent=2, ensure_ascii=False)
    print("\nwrote source_check.json")

if __name__ == "__main__":
    main()
