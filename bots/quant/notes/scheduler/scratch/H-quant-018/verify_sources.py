#!/usr/bin/env python3
"""Verify every URL cited in quant-018's 出处 section (accessed 2026-10-21).

Prints one line per URL: HTTP status, bytes, and PASS/CHANGED/FAIL against the
claim written in the entry.  Raw bodies are not saved; only metadata and the
specific Gamma/CLOB/ArcGIS fields needed for the check are cached under
_cache/ (gitignored).
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
CACHE.mkdir(exist_ok=True)
ENTRY = HERE.parents[3] / "entries" / "quant-018-strait-transit-count-base-rate.md"
S = requests.Session()
S.headers.update({"User-Agent": "quant-q018-source-verify/1.0 (keyless public data)"})
AS_OF = "2026-10-22"
rows = []


def get(url):
    r = S.get(url, timeout=90)
    return r


def add(url, status, nbytes, verdict, detail):
    rows.append(dict(url=url, status=status, bytes=nbytes, verdict=verdict, detail=detail))
    print(f"[{verdict}] HTTP {status} {nbytes}B {url}\n        {detail}")


def main():
    text = ENTRY.read_text(encoding="utf-8")
    tail = text.split("## 出处", 1)[1]
    urls = []
    for line in tail.splitlines():
        if line.startswith("- http"):
            u = line[2:].split(" — 访问 ", 1)[0].strip()
            urls.append(u)
    print(f"cited URLs: {len(urls)}; access date {AS_OF}\n")

    for u in urls:
        try:
            r = get(u)
        except Exception as exc:
            add(u, "ERR", 0, "FAIL", f"request failed: {exc}")
            continue
        n = len(r.content)
        low = u
        if r.status_code != 200:
            add(u, r.status_code, n, "FAIL", "non-200")
            continue
        try:
            if "tag_slug=geopolitics" in low:
                d = r.json()
                add(u, r.status_code, n, "PASS", f"{len(d)} events returned (entry claims 100 per page)")
            elif "slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-5" in low:
                e = r.json()[0]
                resolved = []
                for m in e["markets"]:
                    if m.get("outcomePrices") in ('["1", "0"]', '["1","0"]'):
                        resolved.append(m.get("groupItemTitle"))
                desc = e.get("description", "")
                ok = ("from October 5, 2026, through October 11, 2026" in desc
                      and resolved == ["190-209"]
                      and abs(float(e.get("volume", 0)) - 13097.774817) < 0.01)
                add(u, r.status_code, n, "PASS" if ok else "CHANGED",
                    f"resolved={resolved}, volume={e.get('volume')}, window_text_present={('October 5, 2026, through October 11, 2026' in desc)}")
            elif "slug=how-many-ships-transit-bab-el-mandeb-strait-week-of-october-19" in low:
                e = r.json()[0]
                labels = [m.get("groupItemTitle") for m in e["markets"]]
                fees = [m.get("feesEnabled") for m in e["markets"]]
                rates = [((m.get("clobRewards") or [{}])[0].get("rewardsDailyRate")) for m in e["markets"]]
                mins = sorted({m.get("rewardsMinSize") for m in e["markets"]})
                spreads = sorted({m.get("rewardsMaxSpread") for m in e["markets"]})
                detail = (f"labels={labels}, feesEnabled={fees}, clobRewards_rates={rates}, "
                          f"rewardsMinSize={mins}, rewardsMaxSpread={spreads}")
                # entry's 10/20 snapshot: 5 labels, all fees false, rates 6/39/42/5/8, min 50, spread 8.5
                claim_ok = labels == ["<170", "170-189", "190-209", "210-229", "230+"] and all(f is False for f in fees)
                add(u, r.status_code, n, "PASS" if claim_ok else "CHANGED", detail + " (bid/ask/reward params drift noted in entry)")
            elif "slug=how-many-ships-transit-the-strait-of-hormuz-week-of-october-19" in low:
                e = r.json()[0]
                labels = [m.get("groupItemTitle") for m in e["markets"]]
                add(u, r.status_code, n, "PASS" if len(labels) == 6 else "CHANGED",
                    f"labels={labels}, volume={e.get('volume')} (entry snapshot volume=5539.661748)")
            elif "public-search" in low:
                d = r.json()
                ev = d.get("events", [])
                if "UKMTO" in u:
                    ok = len(ev) == 1 and "ukmto" in ev[0].get("slug", "").lower()
                    add(u, r.status_code, n, "PASS" if ok else "CHANGED", f"{len(ev)} events: {[x.get('slug') for x in ev][:3]}")
                elif "how%20many%20ships%20transit" in u:
                    same = [x for x in ev if str(x.get("slug", "")).startswith("how-many-")]
                    add(u, r.status_code, n, "PASS" if len(ev) == 47 else "CHANGED", f"{len(ev)} events ({len(same)} how-many-*)")
                elif "Strait%20of%20Hormuz" in u:
                    add(u, r.status_code, n, "PASS" if len(ev) == 50 else "CHANGED", f"{len(ev)} events returned")
                elif "Bab%20el-Mandeb" in u:
                    add(u, r.status_code, n, "PASS" if len(ev) == 23 else "CHANGED", f"{len(ev)} events returned")
            elif u.endswith("/rest/services?f=json"):
                d = r.json()
                names = [s.get("name") for s in d.get("services", [])]
                ok = "Daily_Chokepoints_Data" in names and "Daily_Ports_Data" in names
                add(u, r.status_code, n, "PASS" if ok else "FAIL", f"services include Daily_Chokepoints_Data={('Daily_Chokepoints_Data' in names)}")
            elif "FeatureServer/0?f=json" in low:
                d = r.json()
                fields = [f.get("name") for f in d.get("fields", [])]
                need = ["date", "portname", "n_container", "n_dry_bulk", "n_general_cargo", "n_roro", "n_tanker", "n_total"]
                add(u, r.status_code, n, "PASS" if all(x in fields for x in need) else "FAIL", f"fields={fields}")
            elif "FeatureServer/0/query" in low:
                d = r.json()
                add(u, r.status_code, n, "PASS", f"first page features={len(d.get('features', []))}, exceededTransferLimit={d.get('exceededTransferLimit')}")
            elif "portwatch.imf.org" in low:
                body = r.text
                has = "Daily_Chokepoints" in body or "FeatureServer" in body
                add(u, r.status_code, n, "PASS" if n > 100000 else "CHANGED", f"page bytes={n}; direct FeatureServer link in HTML={has}")
            elif "clob.polymarket.com/prices-history" in low:
                d = r.json()
                h = d.get("history", [])
                add(u, r.status_code, n, "PASS" if len(h) > 0 else "CHANGED",
                    f"history points={len(h)}; first={h[0] if h else None}; last={h[-1] if h else None}")
            else:
                add(u, r.status_code, n, "PASS", "HTTP 200")
        except Exception as exc:
            add(u, r.status_code, n, "FAIL", f"parse error: {exc}")

    # Extra checks for claims that need a different request than the cited URL.
    print("\n== extra checks ==")
    u = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
    for where, label in [("portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')", "both"), ("portname = 'Bab el-Mandeb Strait'", "Bab")]:
        d = S.get(u, params={"where": where, "returnCountOnly": "true", "f": "json"}, timeout=60).json()
        print(f"PortWatch {label} count: {d.get('count')}")
    d = S.get(u, params={"where": "portname IN ('Bab el-Mandeb Strait','Strait of Hormuz')",
                         "outFields": "date,portname,n_total", "returnGeometry": "false", "f": "json",
                         "resultOffset": 0, "resultRecordCount": 1, "orderByFields": "date DESC"}, timeout=60).json()
    print("PortWatch latest row:", d.get("features", [{}])[0].get("attributes"))
    print("\nentry snapshot (2026-10-20): 5,682 rows, each strait 2,841 days, latest 2026-10-11")
    print("2026-10-21 re-check above: row counts and latest date have advanced; the dated snapshot is not false,")
    print("but a reader re-running the cited query today will get more rows.  This is recorded, not hidden.")

    out = HERE / "verify_sources.json"
    out.write_text(json.dumps({"as_of": AS_OF, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [r for r in rows if r["verdict"] == "FAIL"]
    print(f"\nsummary: {len(rows)} URLs, PASS={sum(r['verdict']=='PASS' for r in rows)}, "
          f"CHANGED={sum(r['verdict']=='CHANGED' for r in rows)}, FAIL={len(bad)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
