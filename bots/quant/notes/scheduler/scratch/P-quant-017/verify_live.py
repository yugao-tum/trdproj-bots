#!/usr/bin/env python3
"""P-quant-017: re-fetch the live sources and the fields the earlier reviews
flagged (umaBond/umaReward, current liquidityNum, rank order), plus the CLOB
availability check. Free, keyless public GETs only.
Run: python3 verify_live.py
"""
import gzip
import html
import json
import pathlib
import re
import time
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent
CACHE = BASE / "_cache"
CACHE.mkdir(exist_ok=True)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124 Safari/537.36")


def get(url, tries=4, timeout=45):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return r.status, raw, r.geturl()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + i * 3)
    return None, None, str(last)


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def event(slug, tag):
    st, raw, eff = get("https://gamma-api.polymarket.com/events?slug=" + slug)
    print(f"\nEVENT {slug}\n  HTTP {st}, {len(raw) if raw else 0} bytes, effective={eff}")
    if st != 200:
        return None
    d = json.loads(raw)[0]
    (CACHE / f"live_{tag}.json").write_bytes(raw)
    print(f"  endDate={d.get('endDate')} startDate={d.get('startDate')} "
          f"negRisk={d.get('negRisk')} restricted={d.get('restricted')}")
    print(f"  volume={d.get('volume')} liquidity={d.get('liquidity')} "
          f"umaBond={d.get('umaBond')} umaReward={d.get('umaReward')} "
          f"customLiveness={d.get('customLiveness')}")
    print(f"  feeType={d.get('feeType')} feeSchedule={d.get('feeSchedule')}")
    real, ph = [], []
    for m in d["markets"]:
        t = (m.get("groupItemTitle") or "").strip()
        row = (t, f(m.get("bestBid")), f(m.get("bestAsk")),
               f(m.get("liquidityNum")), m.get("volumeNum"),
               json.loads(m.get("outcomePrices") or "[]"),
               (m.get("feeSchedule") or {}).get("rate"))
        (ph if (t.lower() == "other" or t.lower().startswith("reserved")) else real).append(row)
    print(f"  real arms={len(real)} placeholders={len(ph)}")
    for t, bid, ask, liq, vol, pr, rate in real:
        print(f"    {t:<30} YES={pr[0] if pr else None:<8} bid={bid} ask={ask} "
              f"liqNum={liq} vol={vol} rate={rate}")
    print(f"  sums real: YES={sum(f(r[5][0]) or 0 for r in real):.4f} "
          f"bid={sum(r[1] or 0 for r in real):.4f} ask={sum(r[2] or 0 for r in real):.4f}")
    return d


def main():
    print("=== quant-017 live source re-check, 2026-10-21 ===")
    st, raw, eff = get("https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json")
    print(f"\nRSS: HTTP {st}, {len(raw) if raw else 0} bytes, effective={eff}")
    if st == 200:
        feed = json.loads(raw)["feed"]
        (CACHE / "live_rss.json").write_bytes(raw)
        print("  updated=", feed.get("updated"), "n=", len(feed["results"]))
        print("  top12=", [x["name"] for x in feed["results"][:12]])

    st, raw, eff = get("https://apps.apple.com/us/charts/iphone")
    print(f"\nCHARTS: HTTP {st}, {len(raw) if raw else 0} bytes, effective={eff}")
    if st == 200:
        h = raw.decode("utf-8", errors="ignore")
        (CACHE / "live_charts.html").write_bytes(raw)
        found = re.findall(r'<a aria-label="([^"]+)" href="https://apps\.apple\.com/us/app/[^"]+"', h)
        seen = []
        for name in found:
            name = html.unescape(name)
            if name not in seen:
                seen.append(name)
        print("  first 12 distinct ordered app names:", seen[:12])
        print("  HTML contains 'Top Free':", h.count("Top Free"))

    event("1-free-app-in-the-us-apple-app-store-on-october-23-10172026", "ev1")
    event("2-free-app-in-the-us-apple-app-store-on-october-23-10172026", "ev2")

    # CLOB: one 2025 closed event and one 2026-10-16 arm
    for label, tok in [
        ("2025-11-21 #1 ChatGPT arm", None),
        ("2026-10-16 #1 Muse arm",
         "18285021246022090918452030128676107131379306090501090458417099228852389012342"),
    ]:
        if tok is None:
            print(f"\nCLOB {label}: token not retained from earlier log; skipped (see r2prep note)")
            continue
        st, raw, eff = get("https://clob.polymarket.com/prices-history"
                           f"?market={tok}&interval=max&fidelity=10")
        n = 0
        if st == 200 and raw:
            n = len(json.loads(raw).get("history", []))
        print(f"\nCLOB {label}: HTTP {st}, points={n}")


if __name__ == "__main__":
    main()
