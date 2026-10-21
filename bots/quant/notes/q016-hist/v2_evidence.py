#!/usr/bin/env python3
"""Extra v2 evidence: recheck suspicious empty CDX caches and fallback slug identities."""
import datetime as dt
import json
import re
import time
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
CACHE = BASE / "_cache" / "cdx_recheck"
CACHE.mkdir(parents=True, exist_ok=True)
HDR = {"User-Agent": "q016-review/1.0 (academic keyless, <=1 req/s)",
       "Accept-Language": "en-US,en;q=0.9"}
S = requests.Session()
S.headers.update(HDR)
LAST = [0.0]


def get(url, params=None, tries=5, timeout=75):
    global LAST
    last = None
    for i in range(tries):
        wait = 1.05 - (time.monotonic() - LAST[0])
        if wait > 0:
            time.sleep(wait)
        try:
            r = S.get(url, params=params, timeout=timeout)
            LAST[0] = time.monotonic()
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
        except Exception as e:
            LAST[0] = time.monotonic()
            last = f"{type(e).__name__}: {e}"
        time.sleep(min(20, 2 ** i))
    raise RuntimeError(f"GET failed {url} {params}: {last}")


def cdx(slug, start, end):
    key = f"{slug}_{start:%Y%m%d%H%M}_{end:%Y%m%d%H%M}.json"
    path = CACHE / key
    if path.exists():
        return json.loads(path.read_text())
    p = {"url": f"rottentomatoes.com/m/{slug}", "output": "json",
         "from": start.strftime("%Y%m%d%H%M%S"), "to": end.strftime("%Y%m%d%H%M%S"),
         "filter": "statuscode:200"}
    text = get("https://web.archive.org/cdx/search/cdx", params=p).text.strip()
    rows = json.loads(text) if text else []
    path.write_text(json.dumps(rows))
    return rows


def cdx_rows(j):
    if not j:
        return []
    head = j[0]
    return [dict(zip(head, row)) for row in j[1:]]


def main():
    print("== recheck empty CDX caches (genuine empty vs partial) ==")
    checks = [
        ("fantasy_life", dt.datetime(2026, 3, 23, 14, tzinfo=dt.timezone.utc),
         dt.datetime(2026, 3, 30, 14, tzinfo=dt.timezone.utc)),
        ("the_weight_2026", dt.datetime(2026, 9, 14, 14, tzinfo=dt.timezone.utc),
         dt.datetime(2026, 9, 21, 14, tzinfo=dt.timezone.utc)),
    ]
    for slug, start, end in checks:
        broad_start = start - dt.timedelta(days=10)
        broad_end = end + dt.timedelta(days=10)
        try:
            rows = cdx_rows(cdx(slug, broad_start, broad_end))
        except Exception as e:
            print(f"{slug}: 未取到 broad CDX ({e})")
            continue
        inside = [r for r in rows if start <= dt.datetime.strptime(r["timestamp"], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc) <= end]
        print(f"{slug}: broad[{broad_start:%Y-%m-%d}..{broad_end:%Y-%m-%d}] captures={len(rows)} "
              f"in_window[{start:%Y-%m-%d %H:%M}..{end:%Y-%m-%d %H:%M}]={len(inside)}")
        print("  broad timestamps: " + ", ".join(r["timestamp"] for r in rows[:20]))

    print("\n== old fallback slug vs corrected slug (live RT, keyless) ==")
    for slug in ("over_your_live_body", "over_your_dead_body", "over_your_dead_body_2026"):
        try:
            r = S.get(f"https://www.rottentomatoes.com/m/{slug}", timeout=45)
            m = re.search(r"<title>(.*?)</title>", r.text, re.S | re.I)
            title = re.sub(r"\s*\|\s*Rotten Tomatoes.*$", "", m.group(1)).strip() if m else ""
            print(f"{slug}: HTTP {r.status_code}; title={title!r}; bytes={len(r.content)}")
        except Exception as e:
            print(f"{slug}: 未取到 ({type(e).__name__}: {e})")
        time.sleep(1.0)


if __name__ == "__main__":
    main()
