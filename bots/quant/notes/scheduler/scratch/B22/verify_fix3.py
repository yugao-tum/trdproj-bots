#!/usr/bin/env python3
"""B22 fix3 verification (2026-10-20 UTC).

Re-checks the numbers changed in this round against the freshly rebuilt cache:
  * test_2w: strict 6 trades / 3 event-days, broad 10 trades / 7 event-days;
  * low-price claim: signal-set trade prices actually observed (1-20c);
  * queue note: B22 settlement source (SPC) vs quant-026 (USDM) is distinct.
"""
import json, datetime, requests
import reproduce as R

ev = json.load(open("_cache/events_meta.json"))
rows = json.load(open("_cache/classified.json"))
lm = R.load_lm()


def signals():
    strict, broad = [], []
    for r in rows:
        d = r["date"]
        evr = next(x for x in ev if x["date"] == d)
        lm1630 = lm.get(("1630", d)); lm2000 = lm.get(("2000", d)); lmfinal = lm.get(("final", evr["next"]))
        windows = []
        if r["yes_1630"]:
            windows.append(("1630", (lm1630 + 120) if lm1630 else R.ts(d, 16, 45), (lm2000 + 120) if lm2000 else R.ts(d, 19, 55)))
        if r["yes_2000"]:
            windows.append(("2000", (lm2000 + 120) if lm2000 else R.ts(d, 20, 20), (lmfinal + 120) if lmfinal else R.nextts(d, 1, 15)))
        t = R.load_trades(r["conditionId"])
        for wname, lo, hi in windows:
            z = next((v for v in t if lo <= v["timestamp"] < hi and v["side"] == "BUY" and v["outcome"] == "Yes"), None)
            if z and z["yespx"] <= R.THRESH:
                strict.append((d, z["yespx"]))
            z2 = next((v for v in t if lo <= v["timestamp"] < hi and v["yespx"] <= R.THRESH), None)
            if z2:
                broad.append((d, z2["yespx"]))
    return strict, broad


strict, broad = signals()
for name, arr in [("strict", strict), ("broad", broad)]:
    px = [x[1] for x in arr]
    print(f"{name}: trades={len(arr)} events={len(set(x[0] for x in arr))} "
          f"yespx_min={min(px):.3f} yespx_max={max(px):.3f}")

print("\n== settlement sources (live Gamma, 2026-10-20) ==")
s = requests.Session(); s.headers.update({"User-Agent": "Mozilla/5.0 (research)"})


def first_market_source(event_slug):
    r = s.get("https://gamma-api.polymarket.com/events", params={"slug": event_slug}, timeout=30)
    r.raise_for_status()
    e = r.json()[0]
    m = e["markets"][0]
    return e.get("title"), m.get("question"), m.get("resolutionSource")


for slug in ["which-cities-face-tornado-risk-on-september-30-2026", "state-d4-drought-2026-10-13"]:
    title, q, src = first_market_source(slug)
    print(f"{slug}\n  event={title}\n  market={q}\n  resolutionSource={src}")
