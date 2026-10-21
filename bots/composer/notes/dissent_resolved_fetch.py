#!/usr/bin/env python3
"""Fetch closed Polymarket FOMC dissent-count events and winning brackets."""
from __future__ import annotations

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

GAMMA = "https://gamma-api.polymarket.com"
OUT = Path(__file__).resolve().parent / "dissent_resolved.json"


def curl_json(url: str) -> dict:
    out = subprocess.check_output(
        ["curl", "-sS", "-A", "Mozilla/5.0", url], text=True, timeout=120
    )
    return json.loads(out)


def list_slugs() -> list[str]:
    slugs: set[str] = set()
    for offset in range(0, 500, 100):
        url = (
            f"{GAMMA}/public-search?q=dissent+fed+meeting"
            f"&limit_per_type=100&events_status=closed&offset={offset}"
        )
        batch = curl_json(url).get("events") or []
        if not batch:
            break
        for e in batch:
            s = e.get("slug") or ""
            if "dissent" in s and "fed" in s:
                slugs.add(s)
        if len(batch) < 100:
            break
    return sorted(slugs)


def winning(slug: str) -> dict:
    ev = curl_json(f"{GAMMA}/events?slug={slug}")[0]
    win = None
    for m in ev.get("markets") or []:
        op = m.get("outcomePrices")
        if isinstance(op, str):
            op = json.loads(op)
        if op and op[0] == "1":
            win = m.get("groupItemTitle")
            break
    return {
        "slug": slug,
        "title": ev.get("title"),
        "endDate": (ev.get("endDate") or "")[:10],
        "resolved": win,
    }


def main():
    slugs = list_slugs()
    rows = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(winning, s): s for s in slugs}
        for fut in as_completed(futs):
            rows.append(fut.result())
    rows.sort(key=lambda r: r.get("endDate") or "")
    payload = {"fetched_utc": "2026-10-21", "closed_count": len(rows), "rows": rows}
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    from collections import Counter

    c = Counter(r["resolved"] for r in rows if r.get("resolved"))
    print(json.dumps({"closed_count": len(rows), "distribution": dict(c), "path": str(OUT)}))


if __name__ == "__main__":
    main()
