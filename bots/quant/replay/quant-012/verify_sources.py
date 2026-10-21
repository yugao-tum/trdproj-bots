#!/usr/bin/env python3
"""Re-check every external endpoint this replay cites (free, keyless, read-only).

Run: python3 verify_sources.py | tee verify_output.txt
"""

import json
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
S = requests.Session()
S.headers["User-Agent"] = "quant-research/1.0 (public keyless data)"


def show(name, ok, detail):
    print(f"[{'OK ' if ok else 'FAIL'}] {name}: {detail}")
    return ok


def main():
    ok = True

    r = S.get(
        "https://gamma-api.polymarket.com/events",
        params={"tag_slug": "earthquake", "limit": 500, "closed": "true",
                "order": "endDate", "ascending": "false"},
        timeout=60,
    )
    if r.status_code == 200:
        d = r.json()
        hm = [e for e in d if e.get("slug", "").startswith("how-many") and e.get("closed")]
        ok &= show("gamma tag=earthquake closed", True,
                   f"HTTP 200, events={len(d)}, how-many ladder events={len(hm)}")
    else:
        ok &= show("gamma tag=earthquake closed", False, f"HTTP {r.status_code}")

    slug = "how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25"
    r = S.get("https://gamma-api.polymarket.com/events", params={"slug": slug}, timeout=60)
    if r.status_code == 200 and r.json():
        ev = r.json()[0]
        desc = ev.get("description", "")
        keys = ["United States Geological Survey", "48 hours", "lowest bracket",
                "anywhere on Earth"]
        hits = {k: (k in desc) for k in keys}
        ok &= show("gamma event rules", all(hits.values()),
                   f"HTTP 200, markets={len(ev.get('markets', []))}, keyword hits={hits}")
        fees = sorted({(m.get("feeSchedule") or {}).get("rate") for m in ev.get("markets", [])})
        print(f"       live feeSchedule rates on this event: {fees}")
    else:
        ok &= show("gamma event rules", False, f"HTTP {r.status_code}")

    for mag, expected in ((6.5, 462), (7.0, 153), (5.5, 5031)):
        r = S.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/count",
            params={"format": "geojson", "starttime": "2015-01-01",
                    "endtime": "2026-01-01", "minmagnitude": mag},
            timeout=60,
        )
        got = r.json().get("count") if r.status_code == 200 else None
        ok &= show(f"USGS count M{mag}+ 2015..2026", got == expected, f"{got} (entry says {expected})")

    r = S.get(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        params={"format": "csv", "starttime": "2000-01-01", "endtime": "2026-10-21",
                "minmagnitude": 6.4, "orderby": "time-asc"},
        timeout=180,
    )
    if r.status_code == 200:
        rows = r.text.strip().splitlines()
        n65 = sum(1 for line in rows[1:] if line.split(",")[4] and float(line.split(",")[4]) >= 6.5)
        ok &= show("USGS CSV catalog", True, f"HTTP 200, rows={len(rows)} (header incl.), mag>=6.5 rows={n65}")
    else:
        ok &= show("USGS CSV catalog", False, f"HTTP {r.status_code}")

    cid = "0xcc51bf3e53b2cb6ca7e49c53ed4fc6f906684c0ec61206441d85759448c3b2b7"
    r = S.get("https://data-api.polymarket.com/trades",
              params={"market": cid, "limit": 5, "offset": 0}, timeout=60)
    if r.status_code == 200:
        d = r.json()
        fields = sorted(d[0].keys()) if d else []
        need = {"side", "price", "size", "timestamp", "outcome"}
        ok &= show("data-api trades", bool(d) and need <= set(fields),
                   f"HTTP 200, n={len(d)}, has {sorted(need)}")
    else:
        ok &= show("data-api trades", False, f"HTTP {r.status_code}")

    r = S.get("https://clob.polymarket.com/prices-history",
              params={"market": "101519993085150541985963030400073395102135944737997204045298260898135285026732",
                      "interval": "max", "fidelity": 60}, timeout=60)
    ok &= show("CLOB prices-history closed token", r.status_code == 200 and r.json().get("history") == [],
               f"HTTP {r.status_code}, body={r.text[:40]}")

    for name, n in (("trades.csv", 184), ("events.csv", 69), ("equity.csv", 323)):
        p = HERE / name
        lines = sum(1 for _ in p.open(encoding="utf-8")) if p.exists() else 0
        print(f"[{'OK ' if lines == n else 'INFO'}] local {name}: {lines} lines (expected {n} incl. header)")

    print(f"\nALL EXTERNAL CHECKS PASS: {ok}")


if __name__ == "__main__":
    main()
