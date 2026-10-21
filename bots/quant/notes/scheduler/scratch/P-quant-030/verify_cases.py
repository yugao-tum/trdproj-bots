import requests, json, os, time, datetime, re

CACHE = "bots/quant/notes/scheduler/scratch/P-quant-030/_cache"
os.makedirs(CACHE, exist_ok=True)

CASES = {
    "boeing-airplane-deliveries-above-in-q1": "2026-04-14",
    "costco-q3-us-adjusted-comparable-sales-growth": "2026-05-28",
    "united-airlines-ual-q2-consolidated-passenger-load-factor-20260618193152130": "2026-07-15",
    "delta-dal-q2-passenger-load-factor": "2026-07-10",
    "will-taiwan-semiconductor-tsm-q2-revenue-usd-be-above-20260618163305419": "2026-07-17",
}


def get_event(slug):
    p = os.path.join(CACHE, f"event_{slug}.json")
    if os.path.exists(p):
        return json.load(open(p))
    r = requests.get("https://gamma-api.polymarket.com/events",
                     params={"slug": slug}, timeout=40)
    r.raise_for_status()
    d = r.json()
    e = d[0] if isinstance(d, list) else d
    json.dump(e, open(p, "w"))
    return e


def get_trades(cid):
    p = os.path.join(CACHE, f"trades_{cid}.json")
    if os.path.exists(p):
        return json.load(open(p))
    tr = []
    off = 0
    while off < 40000:
        r = requests.get("https://data-api.polymarket.com/trades",
                         params={"market": cid, "limit": 1000, "offset": off}, timeout=40)
        if r.status_code != 200:
            break
        d = r.json()
        if not d:
            break
        tr += d
        off += len(d)
        if len(d) < 1000:
            break
        time.sleep(0.05)
    json.dump(tr, open(p, "w"))
    return tr


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


out = {}
for slug in CASES:
    e = get_event(slug)
    print("=" * 100)
    print(slug, "| volume", round(e.get("volume") or 0, 2), "| markets", len(e.get("markets", [])))
    out[slug] = {}
    for m in e.get("markets", []):
        cid = m["conditionId"]
        tr = get_trades(cid)
        out[slug][m["question"]] = {
            "conditionId": cid, "outcomePrices": m.get("outcomePrices"),
            "volume": m.get("volume"), "n_trades": len(tr),
            "open": m.get("closed") is False,
        }
        print(f"  [{m.get('groupItemTitle') or m['question'][-40:]}] trades={len(tr)} "
              f"vol={m.get('volume')} out={m.get('outcomePrices')} closed={m.get('closed')}")

json.dump(out, open(os.path.join(CACHE, "case_index.json"), "w"), indent=1)
