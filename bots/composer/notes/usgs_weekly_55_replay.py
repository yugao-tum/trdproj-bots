#!/usr/bin/env python3
"""Replay closed Polymarket M5.5+ weekly count events vs USGS (composer-008 / T08b)."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

GAMMA = "https://gamma-api.polymarket.com"
USGS_COUNT = "https://earthquake.usgs.gov/fdsnws/event/1/count"
OUT = Path(__file__).resolve().parent / "cache" / "usgs_weekly_55_replay.json"
MONTH = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def curl_json(url: str) -> dict | list:
    out = subprocess.check_output(
        ["curl", "-sS", "-A", "Mozilla/5.0", url], text=True, timeout=120
    )
    return json.loads(out)


def parse_slug_window(slug: str, year: int = 2026) -> tuple[str, str] | None:
    m = re.search(
        r"earthquakes-([a-z]+)-(\d{1,2})-([a-z]+)-(\d{1,2})$",
        slug,
    )
    if not m:
        return None
    m1, d1, m2, d2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
    mo1, mo2 = MONTH.get(m1), MONTH.get(m2)
    if not mo1 or not mo2:
        return None
    start = f"{year}-{mo1:02d}-{d1:02d}"
    end = f"{year}-{mo2:02d}-{d2 + 1:02d}" if d2 < 28 else f"{year}-{mo2:02d}-{d2:02d}"
    return start, end


def bracket_for_count(n: int, titles: list[str]) -> str | None:
    cleaned = [(t or "").strip() for t in titles if t]
    for t in cleaned:
        if t.isdigit() and n == int(t):
            return t
    for t in cleaned:
        if t.startswith(">"):
            lo = int(re.sub(r"[^\d]", "", t) or "0")
            if n > lo:
                return t
    for t in cleaned:
        if t.startswith("≤") or t.startswith("<"):
            hi = int(re.sub(r"[^\d]", "", t) or "0")
            if n <= hi:
                return t
    return None


def winning_title(markets: list[dict]) -> str | None:
    for m in markets:
        op = m.get("outcomePrices")
        if isinstance(op, str):
            op = json.loads(op)
        if op and op[0] == "1":
            return m.get("groupItemTitle")
    return None


def usgs_count(start: str, end: str) -> int:
    url = f"{USGS_COUNT}?format=geojson&starttime={start}&endtime={end}&minmagnitude=5.5"
    return int(curl_json(url)["count"])


def list_slugs() -> list[str]:
    slugs: set[str] = set()
    for offset in range(0, 100, 20):
        url = (
            f"{GAMMA}/public-search?q=5pt5-or-above-earthquakes"
            f"&limit_per_type=20&events_status=closed&offset={offset}"
        )
        batch = curl_json(url).get("events") or []
        if not batch:
            break
        for e in batch:
            s = e.get("slug") or ""
            if "5pt5-or-above-earthquakes" in s and "7pt0" not in s:
                slugs.add(s)
        if len(batch) < 20:
            break
    return sorted(slugs)


def main() -> None:
    rows = []
    for slug in list_slugs():
        window = parse_slug_window(slug)
        if not window:
            continue
        start, end = window
        ev = curl_json(f"{GAMMA}/events?slug={slug}")[0]
        titles = [m.get("groupItemTitle") for m in ev.get("markets") or []]
        win = winning_title(ev.get("markets") or [])
        try:
            n = usgs_count(start, end)
        except (KeyError, TypeError, ValueError):
            continue
        pred = bracket_for_count(n, titles)
        rows.append(
            {
                "slug": slug,
                "start": start,
                "end": end,
                "usgs_count": n,
                "resolved": win,
                "predicted": pred,
                "match": pred == win if pred and win else None,
            }
        )
    matched = sum(1 for r in rows if r.get("match") is True)
    scored = sum(1 for r in rows if r.get("match") is not None)
    out = {
        "generated_utc": subprocess.check_output(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True
        ).strip(),
        "scored": scored,
        "matched": matched,
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scored": scored, "matched": matched, "path": str(OUT)}))


if __name__ == "__main__":
    main()
