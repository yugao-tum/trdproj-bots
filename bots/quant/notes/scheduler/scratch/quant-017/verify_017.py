#!/usr/bin/env python3
"""Re-fetch the live sources used by quant-017 and recompute the figures that
the checker flagged.  Free, keyless public GETs only.

Outputs: stdout (saved as verify_017.stdout.txt), _cache/ev1.json,
_cache/ev2.json, _cache/charts_ranks.json.
"""
import gzip
import html
import json
import pathlib
import re
import time
import urllib.error
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent
CACHE = BASE / "_cache"
CACHE.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def get(url, tries=4, timeout=45):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return r.status, raw, r.geturl()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + i * 3)
    return None, None, str(last)


def as_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def parse_event(slug):
    url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    status, raw, eff = get(url)
    if status != 200:
        print(f"EVENT {slug}: HTTP {status} ({eff})")
        return None
    d = json.loads(raw)[0]
    (CACHE / ("ev1.json" if slug.startswith("1-") else "ev2.json")).write_bytes(raw)
    print(f"EVENT {slug}: HTTP 200, {len(raw)} bytes, endDate={d.get('endDate')}, negRisk={d.get('negRisk')}, restricted={d.get('restricted')}")
    print(f"  volume={d.get('volume')} liquidity={d.get('liquidity')}")
    real, placeholder = [], []
    for m in d["markets"]:
        title = m.get("groupItemTitle") or ""
        row = {
            "title": title,
            "prices": json.loads(m.get("outcomePrices") or "[]"),
            "bid": as_float(m.get("bestBid")),
            "ask": as_float(m.get("bestAsk")),
            "fee": m.get("feeSchedule"),
            "feeType": m.get("feeType"),
        }
        (placeholder if title.startswith("Reserved") or title == "Other" else real).append(row)
    print("  real candidates:", len(real), [r["title"] for r in real])
    print("  placeholders:", len(placeholder), [r["title"] for r in placeholder])
    for r in real:
        print(f"    {r['title']:<28} YES={r['prices'][0] if r['prices'] else None:<8} bid={r['bid']} ask={r['ask']}")
    yes = sum(as_float(r["prices"][0]) or 0 for r in real)
    bid = sum(r["bid"] or 0 for r in real)
    ask = sum(r["ask"] or 0 for r in real)
    print(f"  sums: YES={yes:.4f} bestBid={bid:.4f} bestAsk={ask:.4f}")
    n = len(real)
    no_cost = n - bid
    fee = sum(0.05 * (1 - (r["bid"] or 0)) * (1 - (1 - (r["bid"] or 0))) for r in real)
    net = no_cost + fee
    # basket NO payout: n if Other wins, else n-1
    breakeven = (net - (n - 1)) / ((n) - (n - 1)) if n else None
    print(f"  basket NO: cost={no_cost:.4f} fee={fee:.4f} net={net:.4f} breakeven P(Other)={breakeven:.4f}")
    return d


def parse_charts():
    url = "https://apps.apple.com/us/charts/iphone"
    status, raw, eff = get(url)
    print(f"CHARTS: HTTP {status}, {len(raw) if raw else 0} bytes, effective={eff}")
    if status != 200:
        return {}
    h = raw.decode("utf-8", errors="ignore")
    items = re.findall(
        r'<a aria-label="([^"]+)" href="https://apps\.apple\.com/us/app/[^"]+"[^>]*>.*?<div class="ordinal[^"]*">(\d+)</div>',
        h,
        re.S,
    )
    ranks = {}
    for name, pos in items:
        ranks[html.unescape(name)] = int(pos)
    (CACHE / "charts_ranks.json").write_text(json.dumps(ranks, ensure_ascii=False, indent=2))
    print(f"  parsed {len(ranks)} ranked apps; top12:")
    for name, pos in sorted(ranks.items(), key=lambda kv: kv[1])[:12]:
        print(f"    {pos:>2} {name}")
    return ranks


def main():
    print("=== quant-017 re-fetch / recompute, 2026-10-20 ===")
    rss_url = "https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json"
    st, raw, eff = get(rss_url, tries=3, timeout=30)
    print(f"RSS: HTTP {st}, {len(raw) if raw else 0} bytes, effective={eff}")
    if st == 200:
        feed = json.loads(raw)
        print("  updated=", feed.get("feed", {}).get("updated"))
        print("  top12=", [x.get("name") for x in feed.get("feed", {}).get("results", [])[:12]])
        (CACHE / "rss.json").write_bytes(raw)
    else:
        print("  RSS not available at this re-check; ranks below are from the resolution-source page only")
    ranks = parse_charts()
    ev1 = parse_event("1-free-app-in-the-us-apple-app-store-on-october-23-10172026")
    ev2 = parse_event("2-free-app-in-the-us-apple-app-store-on-october-23-10172026")
    if ev1 and ranks:
        print("RANKS for #1-board real candidates (from charts page):")
        for m in ev1["markets"]:
            t = m.get("groupItemTitle") or ""
            if t.startswith("Reserved") or t == "Other":
                continue
            hit = next((v for k, v in ranks.items() if k.lower().startswith(t.lower().split(" - ")[0].lower())), None)
            print(f"  {t:<28} rank={hit if hit is not None else '>50'}")
    if ev1 and ev2:
        print("CHECK: #1 board candidates =", [m.get("groupItemTitle") for m in ev1["markets"] if not (m.get("groupItemTitle") or "").startswith("Reserved") and m.get("groupItemTitle") != "Other"])
        print("CHECK: #2 board candidates =", [m.get("groupItemTitle") for m in ev2["markets"] if not (m.get("groupItemTitle") or "").startswith("Reserved") and m.get("groupItemTitle") != "Other"])


if __name__ == "__main__":
    main()
