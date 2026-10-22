#!/usr/bin/env python3
"""Re-check every URL and local evidence path cited in the quant-012 entry.

Free, keyless, read-only. Templated URLs in the entry are replaced with the
concrete examples the entry itself says were used:
  <conditionId>  -> 0xcc51bf3e... (the example in the entry's 出处 section)
  <clobTokenId>  -> the open-market token used in 出处
  <event-slug>   -> the 2026-10-19 event slug
  page=N         -> page=1
  starttime=...&endtime=... -> 2000-01-01..2026-10-21 (as used by the replay)

It also re-computes the numeric claims attached to the USGS and Gamma URLs.
Run: python3 verify_entry_urls.py | tee verify_entry_urls_output.txt
"""

import re
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
ENTRY = ROOT / "bots/quant/entries/quant-012-earthquake-count-base-rate.md"
S = requests.Session()
S.headers["User-Agent"] = "quant-research/1.0 (public keyless data)"

COND = "0xcc51bf3e53b2cb6ca7e49c53ed4fc6f906684c0ec61206441d85759448c3b2b7"
TOKEN = "2500092545816023700094480893694885475686508335314406123382468585117526026802"
SLUG = "how-many-6pt5-or-above-earthquakes-worldwide-october-19-october-25"


def normalize(url):
    url = url.rstrip("`.,;，。；")
    url = url.replace("<conditionId>", COND).replace("<clobTokenId>", TOKEN)
    url = url.replace("<event-slug>", SLUG).replace("<event-slug", SLUG)
    url = url.replace("page=N", "page=1")
    url = url.replace("starttime=...&endtime=...", "starttime=2000-01-01&endtime=2026-10-21")
    return url


def main():
    text = ENTRY.read_text(encoding="utf-8")
    sources = text.split("## 出处", 1)[1]
    urls = []
    for line in sources.splitlines():
        for m in re.finditer(r"https?://[^\s)\]}，。；`]+", line):
            urls.append(normalize(m.group(0)))
    urls = list(dict.fromkeys(urls))
    print(f"entry: {ENTRY.relative_to(ROOT)}")
    print(f"unique cited URLs: {len(urls)}\n")

    ok = True
    for url in urls:
        try:
            r = S.get(url, timeout=180)
            good = r.status_code == 200
            ok &= good
            print(f"[{'OK ' if good else 'FAIL'}] HTTP {r.status_code} {url}")
            body = r.text
            if "earthquake.usgs.gov/fdsnws/event/1/count" in url:
                print(f"       count={r.json().get('count')}")
            elif "format=csv" in url and "starttime=2000-01-01" in url:
                lines = body.strip().splitlines()
                n65 = sum(1 for l in lines[1:] if l.split(",")[4] and float(l.split(",")[4]) >= 6.5)
                print(f"       rows={len(lines)} mag>=6.5={n65}")
                ok &= len(lines) == 1513 and n65 == 1216
            elif "format=text" in url and "2026-10-12" in url:
                evs = [l.split("|")[0] for l in body.splitlines() if l and not l.startswith("#")]
                print(f"       events={len(evs)} ids={evs}")
                ok &= evs == ["us6000u2mq", "us6000u214", "us6000u1z5"]
            elif url.rstrip("/").endswith("earthquakes/search"):
                print(f"       title_ok={'Search Earthquake Catalog' in body}")
            elif "gamma-api.polymarket.com/events?slug=" in url:
                d = r.json()
                ev = d[0] if isinstance(d, list) and d else {}
                desc = ev.get("description", "")
                keys = ["United States Geological Survey", "48 hours", "lowest bracket", "anywhere on Earth"]
                print(f"       closed={ev.get('closed')} markets={len(ev.get('markets', []))} "
                      f"keywords={all(k in desc for k in keys)}")
            elif "gamma-api.polymarket.com/events?tag_slug=earthquake" in url:
                d = r.json()
                hm = [e for e in d if e.get("slug", "").startswith("how-many") and e.get("closed")]
                vol = sum(float(e.get("volume") or 0) for e in d)
                print(f"       events={len(d)} how-many={len(hm)} volume={vol:.2f}")
                ok &= len(d) == 69 and len(hm) == 37
            elif "gamma-api.polymarket.com/markets?slug=" in url:
                print(f"       body={body[:60]}")
                ok &= r.json() == []
            elif "public-search" in url:
                d = r.json()
                print(f"       events={len(d.get('events', []))}")
                ok &= bool(d.get("events"))
            elif "clob.polymarket.com/prices-history" in url:
                h = r.json().get("history", [])
                print(f"       history_points={len(h)}")
                if TOKEN in url:
                    ok &= len(h) > 0
                else:
                    ok &= h == []
            elif "data-api.polymarket.com/trades" in url:
                d = r.json()
                need = {"side", "price", "size", "timestamp", "outcome"}
                print(f"       n={len(d)} fields_ok={bool(d) and need <= set(d[0])}")
                ok &= bool(d) and need <= set(d[0])
        except Exception as exc:
            ok = False
            print(f"[FAIL] {url}: {exc!r}")

    print("\nlocal evidence paths cited in 出处:")
    tokens = []
    for m in re.finditer(r"`([^`]+)`", sources):
        t = m.group(1).strip()
        if t.startswith("http") or " " in t or "..." in t:
            continue
        if t.startswith("bots/") or t.endswith((".py", ".md", ".csv", ".txt", ".json")):
            tokens.append(t)
    dirs = [ROOT / "bots/quant/notes/q012-hist", HERE, HERE.parent / "I01",
            ROOT / "bots/quant/replay/quant-012"]
    for t in dict.fromkeys(tokens):
        hit = next((c for c in [ROOT / t] + [d / t for d in dirs] if c.exists()), None)
        good = hit is not None
        ok &= good
        print(f"[{'OK ' if good else 'FAIL'}] {t}" + ("" if hit is None else f" -> {hit.relative_to(ROOT)}"))

    print(f"\nALL CITED SOURCES/POINTERS OK: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
