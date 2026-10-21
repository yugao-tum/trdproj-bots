#!/usr/bin/env python3
"""P-quant-017: fetch the only historical tradable prices that exist for the
US Apple App Store weekly rank boards (Polymarket CLOB 1/10-minute history).

Free, keyless public GETs only.  Raw responses cached under _cache/ (git-ignored).
Run: python3 fetch_bt_data.py
"""
import gzip
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
                return r.status, raw
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + i * 3)
    print("ERR", url, last)
    return None, None


def main():
    events = {}
    pag = None
    for page in range(1, 6):
        url = ("https://gamma-api.polymarket.com/public-search?q=app%20store"
               f"&limit_per_type=50&events_status=all&page={page}")
        st, raw = get(url)
        print(f"public-search page {page}: HTTP {st}, {len(raw) if raw else 0} bytes")
        if st != 200:
            continue
        d = json.loads(raw)
        pag = d.get("pagination", pag)
        for e in d.get("events", []):
            events[e["slug"]] = e
    print("pagination:", pag, "unique events:", len(events))

    weekly = [e for e in events.values()
              if e.get("closed") and re.match(
                  r"^[12]-free-app-in-the-us-apple-app-store-on-", e["slug"])]
    weekly.sort(key=lambda e: e.get("endDate") or "")
    print("closed strict weekly boards:", len(weekly))

    kept = []
    for e in weekly:
        toks = []
        for m in e.get("markets", []):
            try:
                ids = json.loads(m.get("clobTokenIds") or "[]")
            except Exception:  # noqa: BLE001
                ids = []
            if ids:
                toks.append((m.get("groupItemTitle"), ids[0]))
        if not toks:
            continue
        st, raw = get("https://clob.polymarket.com/prices-history"
                      f"?market={toks[0][1]}&interval=max&fidelity=10", timeout=30)
        n = 0
        if st == 200 and raw:
            try:
                n = len(json.loads(raw).get("history", []))
            except Exception:  # noqa: BLE001
                n = 0
        if n > 0:
            kept.append(e)
            print(f"  KEEP {e['slug']} endDate={e.get('endDate')} first-token points={n}")

    print("events with >0 CLOB history:", len(kept))
    detail = {}
    for e in kept:
        st, raw = get("https://gamma-api.polymarket.com/events?slug=" + e["slug"])
        if st != 200:
            print("  detail ERR", e["slug"], st)
            continue
        d = json.loads(raw)[0]
        detail[e["slug"]] = d
        (CACHE / ("ev_" + e["slug"][:60] + ".json")).write_bytes(raw)
        print("  detail", d["slug"], "markets", len(d["markets"]),
              "endDate", d.get("endDate"))

    # all historical series for every market in those events
    n_hist = 0
    for d in detail.values():
        for m in d["markets"]:
            try:
                ids = json.loads(m.get("clobTokenIds") or "[]")
            except Exception:  # noqa: BLE001
                ids = []
            if not ids:
                continue
            tok = ids[0]
            fp = CACHE / f"hist_{tok}.json"
            if fp.exists():
                continue
            st, raw = get("https://clob.polymarket.com/prices-history"
                          f"?market={tok}&interval=max&fidelity=10", timeout=30)
            if st != 200 or not raw:
                continue
            fp.write_bytes(raw)
            try:
                if json.loads(raw).get("history"):
                    n_hist += 1
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.05)
    print("market histories with points:", n_hist)
    (CACHE / "kept_slugs.json").write_text(json.dumps(sorted(detail), indent=1))
    print("kept slugs written:", len(detail))


if __name__ == "__main__":
    main()
