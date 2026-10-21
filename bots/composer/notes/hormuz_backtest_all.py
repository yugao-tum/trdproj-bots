#!/usr/bin/env python3
"""Batch-replay closed Hormuz weekly PM events against IMF PortWatch sums."""
from __future__ import annotations

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

GAMMA = "https://gamma-api.polymarket.com"
ARC = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0/query"
)
CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)


def curl_json(url: str) -> dict:
    out = subprocess.check_output(
        ["curl", "-sS", "-A", "Mozilla/5.0", url], text=True, timeout=120
    )
    return json.loads(out)


def load_portwatch() -> dict[str, float]:
    by: dict[str, float] = {}
    offset = 0
    while True:
        url = (
            f"{ARC}?where=portid%3D%27chokepoint6%27&outFields=date%2Cn_total"
            f"&orderByFields=date%20ASC&resultRecordCount=1000&resultOffset={offset}&f=json"
        )
        data = curl_json(url)
        feats = data.get("features") or []
        if not feats:
            break
        for f in feats:
            a = f["attributes"]
            by[str(a["date"])[:10]] = float(a["n_total"])
        if not data.get("exceededTransferLimit"):
            break
        offset += 1000
    return by


def week_sum(by: dict[str, float], start: date) -> float:
    return sum(by.get((start + timedelta(days=i)).isoformat(), 0.0) for i in range(7))


def parse_week_start(desc: str, title: str) -> date | None:
    m = re.search(
        r"from\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4}),\s+through",
        desc,
        re.I,
    )
    if m:
        month_s, day, year = m.group(1), int(m.group(2)), int(m.group(3))
        month = {
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
        }.get(month_s.lower())
        if month:
            return date(int(year), month, day)
    m2 = re.search(r"week of\s+([A-Za-z]+)\s+(\d{1,2})", title, re.I)
    if m2:
        month_s, day = m2.group(1), int(m2.group(2))
        month = {
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
        }.get(month_s.lower())
        if month:
            return date(2026, month, day)
    return None


def bracket_for_sum(s: float, titles: list[str]) -> str | None:
    """Map sum to groupItemTitle like <20, 20-24, 40+."""
    for t in titles:
        t = t.strip()
        if t.startswith("<"):
            hi = float(t[1:].strip())
            if s < hi:
                return t
        elif t.endswith("+"):
            lo = float(t[:-1].strip())
            if s >= lo:
                return t
        elif "-" in t:
            a, b = t.split("-", 1)
            lo, hi = float(a), float(b)
            if lo <= s <= hi:
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


def list_closed_slugs() -> list[str]:
    url = (
        f"{GAMMA}/public-search?q=how-many-ships-transit-the-strait-of-hormuz-week"
        "&limit_per_type=100&events_status=closed"
    )
    data = curl_json(url)
    slugs = []
    for e in data.get("events", []):
        s = e.get("slug") or ""
        if s.startswith("how-many-ships-transit-the-strait-of-hormuz-week"):
            slugs.append(s)
    return sorted(set(slugs))


def process_slug(slug: str, by: dict[str, float]) -> dict:
    ev = curl_json(f"{GAMMA}/events?slug={slug}")[0]
    desc = ev.get("description") or ""
    title = ev.get("title") or ""
    start = parse_week_start(desc, title)
    win = winning_title(ev.get("markets") or [])
    titles = [m.get("groupItemTitle") for m in ev.get("markets") or []]
    s = week_sum(by, start) if start else None
    pred = bracket_for_sum(s, titles) if s is not None and titles else None
    return {
        "slug": slug,
        "week_start": start.isoformat() if start else None,
        "sum7": s,
        "resolved": win,
        "predicted": pred,
        "match": pred == win if pred and win else None,
    }


def main():
    by = load_portwatch()
    slugs = list_closed_slugs()
    rows = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(process_slug, slug, by): slug for slug in slugs}
        for fut in as_completed(futs):
            rows.append(fut.result())
    rows.sort(key=lambda r: r.get("week_start") or "")
    matched = sum(1 for r in rows if r.get("match") is True)
    total = sum(1 for r in rows if r.get("match") is not None)
    out = {
        "generated_utc": date.today().isoformat(),
        "closed_count": len(slugs),
        "match_rate": matched / total if total else None,
        "matched": matched,
        "scored": total,
        "rows": rows,
    }
    path = CACHE / "hormuz_replay.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"closed_count": len(slugs), "matched": matched, "scored": total, "path": str(path)}))


if __name__ == "__main__":
    main()
