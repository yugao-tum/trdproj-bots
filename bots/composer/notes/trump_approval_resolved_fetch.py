#!/usr/bin/env python3
"""Fetch closed Polymarket «Trump approval rating on <date>» ladder events."""
from __future__ import annotations

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

GAMMA = "https://gamma-api.polymarket.com"
SLUG_RE = re.compile(r"^trump-approval-rating-on-[a-z0-9-]+$")
OUT = Path(__file__).resolve().parent / "trump_approval_resolved.json"


def curl_json(url: str) -> dict | list:
    out = subprocess.check_output(
        ["curl", "-sS", "-A", "Mozilla/5.0", url], text=True, timeout=120
    )
    return json.loads(out)


def list_slugs() -> list[str]:
    slugs: set[str] = set()
    for offset in range(0, 500, 50):
        url = (
            f"{GAMMA}/public-search?q=trump+approval+rating+on"
            f"&limit_per_type=50&events_status=closed&offset={offset}"
        )
        batch = curl_json(url).get("events") or []
        if not batch:
            break
        for e in batch:
            s = e.get("slug") or ""
            if SLUG_RE.match(s):
                slugs.add(s)
        if len(batch) < 50:
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
        "winning_bracket": win,
    }


def main() -> None:
    slugs = list_slugs()
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(winning, s): s for s in slugs}
        for fut in as_completed(futs):
            rows.append(fut.result())
    rows.sort(key=lambda r: r.get("endDate") or "")
    payload = {
        "fetched_utc": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "source": "gamma public-search + per-slug events",
        "count": len(rows),
        "events": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(rows), "path": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
