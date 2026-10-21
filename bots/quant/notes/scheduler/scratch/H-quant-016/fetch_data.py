#!/usr/bin/env python3
"""Fetch closed Rotten Tomatoes Tomatometer events + historical prices/fills.

Keyless public endpoints only. Raw JSON is cached under _cache/ (gitignored).
Decision times are defined relative to Gamma event endDate (UTC).
"""
import json, os, re, sys, time, datetime
import concurrent.futures as cf
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research; quant-016 hardening)"}
S = requests.Session()
S.headers.update(UA)

def get(url, **kw):
    for attempt in range(4):
        try:
            r = S.get(url, timeout=30, **kw)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (attempt + 1))
                continue
            return r
        except Exception as e:
            time.sleep(2 * (attempt + 1))
    return None

def load_or_fetch(name, url):
    path = os.path.join(CACHE, name)
    if os.path.exists(path) and os.path.getsize(path) > 2:
        return json.load(open(path))
    r = get(url)
    if r is None or r.status_code != 200:
        print(f"FAIL {name} {getattr(r,'status_code',None)}", flush=True)
        return None
    open(path, "wb").write(r.content)
    return r.json()

def threshold(m):
    t = str(m.get("groupItemTitle", "")).replace("+", "").strip()
    if re.fullmatch(r"\d+", t):
        return int(t)
    return None

def main():
    events = load_or_fetch(
        "gamma_closed.json",
        "https://gamma-api.polymarket.com/events?tag_slug=rotten-tomatoes&limit=500&closed=true&order=endDate&ascending=false",
    )
    if events is None:
        sys.exit("no events")
    rows = []
    for e in events:
        end = e.get("endDate")
        if not end:
            continue
        end_ts = int(datetime.datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp())
        for m in e.get("markets", []):
            t = threshold(m)
            if t is None:
                continue
            try:
                toks = json.loads(m.get("clobTokenIds") or "[]")
                op = json.loads(m.get("outcomePrices") or "[]")
            except Exception:
                continue
            if len(toks) < 1 or len(op) < 2:
                continue
            rows.append(
                dict(
                    event=e["slug"],
                    endDate=end,
                    end_ts=end_ts,
                    threshold=t,
                    conditionId=m.get("conditionId"),
                    yes_token=toks[0],
                    outcome_yes=1 if float(op[0]) >= 0.5 else 0,
                    outcome_raw=op,
                    volume=float(m.get("volume") or 0),
                )
            )
    print("events", len(events), "bracket markets", len(rows), flush=True)

    # Price history: one request per bracket token, 9 days before event end.
    def fetch_ph(row):
        tok = row["yes_token"]
        name = f"ph_{tok}.json"
        path = os.path.join(CACHE, name)
        if os.path.exists(path) and os.path.getsize(path) > 10:
            return tok, "cached"
        s = row["end_ts"] - 9 * 86400
        u = (
            "https://clob.polymarket.com/prices-history?market="
            f"{tok}&startTs={s}&endTs={row['end_ts']+3600}&fidelity=60"
        )
        r = get(u)
        if r is None or r.status_code != 200:
            return tok, f"fail:{getattr(r,'status_code',None)}"
        open(path, "wb").write(r.content)
        return tok, "ok"

    tokens = sorted({r["yes_token"] for r in rows})
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(fetch_ph, {t: next(r for r in rows if r["yes_token"] == t) for t in tokens}.values()))
    print("price-history", len(res), "ok", sum(1 for _, s in res if s in ("ok", "cached")), flush=True)

    # Real fills: newest-first pages until we pass endDate-9d or 4 pages.
    def fetch_tr(row):
        cid = row["conditionId"]
        name = f"tr_{cid}.json"
        path = os.path.join(CACHE, name)
        if os.path.exists(path) and os.path.getsize(path) > 2:
            return cid, "cached"
        cutoff = row["end_ts"] - 9 * 86400
        trades = []
        for page in range(4):
            u = f"https://data-api.polymarket.com/trades?market={cid}&limit=500&offset={page*500}"
            r = get(u)
            if r is None or r.status_code != 200:
                break
            try:
                batch = r.json()
            except Exception:
                break
            if not isinstance(batch, list) or not batch:
                break
            trades.extend(batch)
            oldest = min(int(x.get("timestamp", 0)) for x in batch)
            if oldest < cutoff:
                break
        json.dump(trades, open(path, "w"))
        return cid, f"ok:{len(trades)}"

    conds = sorted({r["conditionId"] for r in rows})
    by_cid = {r["conditionId"]: r for r in rows}
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        res2 = list(ex.map(fetch_tr, [by_cid[c] for c in conds]))
    n_ok = sum(1 for _, s in res2 if s.startswith("ok") or s == "cached")
    print("trades", len(res2), "ok", n_ok, flush=True)

    with open(os.path.join(BASE, "markets.json"), "w") as f:
        json.dump(rows, f)
    print("wrote markets.json", flush=True)

if __name__ == "__main__":
    main()
