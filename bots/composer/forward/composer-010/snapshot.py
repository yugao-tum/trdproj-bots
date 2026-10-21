#!/usr/bin/env python3
"""One forward snapshot for composer-010.

Live RealClearPolling is fetched and the HTTP status is recorded. When that
page is blocked, the latest Wayback copy is parsed and labeled with its own
timestamp. It is not the 2026-10-23 17:00 ET resolution print. Gamma quotes
and recent data-api YES prints are stored beside it.
"""
from __future__ import annotations

import json
import re
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "snapshot_latest.json"
LIVE = "https://www.realclearpolling.com/polls/approval/donald-trump/approval-rating"
WAYBACK_API = "https://archive.org/wayback/available?url=" + LIVE
GAMMA = "https://gamma-api.polymarket.com/events?slug=trump-approval-rating-on-october-23"
TRADES = "https://data-api.polymarket.com/trades?limit=100&market="


def curl(url: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["curl", "-sS", "-L", "-A", "Mozilla/5.0", "--max-time", "40", "-w", "\n%{http_code}", url],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 and not proc.stdout:
        return 0, proc.stderr[-300:]
    body, _, code = proc.stdout.rpartition("\n")
    try:
        status = int(code.strip())
    except ValueError:
        status = 0
    return status, body


def parse_archive(html: str) -> dict | None:
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<svg[\s\S]*?</svg>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]
    for i, line in enumerate(lines):
        if line != "RCP Average":
            continue
        window = lines[i : i + 8]
        nums = [ln for ln in window if re.fullmatch(r"\d{2}\.\d", ln)]
        if len(nums) >= 2 and any(re.fullmatch(r"\d{1,2}/\d{1,2} - \d{1,2}/\d{1,2}", ln) for ln in window):
            return {
                "sample_window": next(ln for ln in window if "/" in ln and "-" in ln),
                "approve": float(nums[0]),
                "disapprove": float(nums[1]),
            }
    return None


def bracket_for(approve: float, titles: list[str]) -> str | None:
    for title in titles:
        label = title.replace("–", "-").replace("—", "-")
        if label.startswith("<"):
            if approve < float(label[1:]):
                return title
            continue
        if label.endswith("+"):
            if approve >= float(label[:-1]):
                return title
            continue
        lo, hi = label.split("-")
        if float(lo) <= approve <= float(hi):
            return title
    return None


def recent_yes(condition_id: str) -> dict:
    status, body = curl(TRADES + condition_id)
    time.sleep(0.3)
    try:
        batch = json.loads(body)
    except json.JSONDecodeError:
        return {"http": status, "error": "not_json"}
    if not isinstance(batch, list):
        return {"http": status, "error": str(batch)[:200]}
    yes = []
    for trade in batch:
        if (trade.get("outcome") or "") != "Yes":
            continue
        yes.append(
            {
                "ts": datetime.fromtimestamp(int(trade["timestamp"]), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "price": float(trade["price"]),
                "size": trade.get("size"),
            }
        )
    band = [p for p in yes if 0.02 < p["price"] < 0.97][:30]
    return {
        "http": status,
        "yes_in_page": len(yes),
        "latest": yes[0] if yes else None,
        "median_30_in_band": round(statistics.median(p["price"] for p in band), 4) if band else None,
        "n_median": len(band),
    }


def main() -> int:
    live_status, live_body = curl(LIVE)
    live = {
        "url": LIVE,
        "http": live_status,
        "bytes": len(live_body),
        "approve": None,
        "note": "DataDome block; no Approve value parsed" if live_status == 403 or "datadome" in live_body.lower() else "parsed" if "RCP Average" in live_body else "no RCP Average row in body",
    }
    if live["note"] == "parsed":
        parsed_live = parse_archive(live_body)
        if parsed_live:
            live.update(parsed_live)

    wb_status, wb_body = curl(WAYBACK_API)
    archive = {"available_http": wb_status}
    try:
        closest = json.loads(wb_body)["archived_snapshots"]["closest"]
    except (json.JSONDecodeError, KeyError, TypeError):
        closest = None
    if closest and closest.get("available"):
        stamp = closest["timestamp"]
        fetch_url = f"https://web.archive.org/web/{stamp}id_/{LIVE}"
        page_status, page = curl(fetch_url)
        parsed = parse_archive(page) if page_status == 200 else None
        archive.update(
            {
                "timestamp": closest["timestamp"],
                "page_http": page_status,
                "parsed": parsed,
                "note": "Wayback copy. Not the live page and not the 2026-10-23 17:00 ET print.",
            }
        )
    else:
        archive["note"] = "no Wayback snapshot"

    g_status, g_body = curl(GAMMA)
    event = json.loads(g_body)
    if isinstance(event, list):
        event = event[0] if event else {}
    markets = []
    titles = []
    for market in event.get("markets") or []:
        title = market.get("groupItemTitle")
        titles.append(title)
        cid = market.get("conditionId")
        row = {
            "bracket": title,
            "conditionId": cid,
            "bestBid": market.get("bestBid"),
            "bestAsk": market.get("bestAsk"),
            "book_note": "Gamma bestBid/bestAsk are quotes, not fills",
        }
        if cid:
            row["trades"] = recent_yes(cid)
        markets.append(row)

    approve = (archive.get("parsed") or {}).get("approve")
    mapped = bracket_for(approve, titles) if approve is not None else None
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_slug": "trump-approval-rating-on-october-23",
        "gamma_http": g_status,
        "event_end": event.get("endDate"),
        "live_rcp": live,
        "wayback": {k: v for k, v in archive.items() if k != "parsed"} | {"parsed": archive.get("parsed")},
        "archive_approve_maps_to": mapped,
        "mapping_note": "Conditional on the Wayback figure still being the live average. It is not a trade.",
        "markets": markets,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "generated_utc": out["generated_utc"],
                "live_http": live["http"],
                "archive_approve": approve,
                "maps_to": mapped,
                "n_markets": len(markets),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
