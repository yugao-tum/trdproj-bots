#!/usr/bin/env python3
"""Append paper 挂 rows to composer-011 ledger (PLAN 2026-10-21)."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAND = ROOT / "notes" / "pm_rewards_candidates.json"
LEDGER = Path(__file__).resolve().parent / "ledger.csv"


def curl_json(url: str) -> dict:
    return json.loads(subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", url], text=True))


def quote_market(m: dict, ts: str) -> list[dict]:
    cid = m["conditionId"]
    slug = m["slug"]
    max_sp = float(m.get("rewardsMaxSpread") or 4.5) / 100.0 / 2.0
    min_sz = int(m.get("rewardsMinSize") or 200)
    size = min(400, max(min_sz, 200))
    token_ids = json.loads(m["clobTokenIds"])
    token_yes = token_ids[0]
    book = curl_json(f"https://clob.polymarket.com/book?token_id={token_yes}")
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return [
            {
                "time_utc": ts,
                "event_id": cid,
                "market": slug,
                "action": "撤",
                "side": "-",
                "price": "0",
                "price_source": "book:empty",
                "size": "0",
                "fee": "0",
                "pnl": "0",
                "note": "empty_book",
            }
        ]
    best_bid = float(bids[0]["price"])
    best_ask = float(asks[0]["price"])
    spread = best_ask - best_bid
    if spread < 0.02:
        return [
            {
                "time_utc": ts,
                "event_id": cid,
                "market": slug,
                "action": "撤",
                "side": "-",
                "price": "0",
                "price_source": f"book:spread={spread:.3f}",
                "size": "0",
                "fee": "0",
                "pnl": "0",
                "note": "spread_too_tight",
            }
        ]
    mid = (best_bid + best_ask) / 2.0
    bid_q = round(min(best_bid + 0.001, mid - max_sp), 3)
    ask_q = round(max(best_ask - 0.001, mid + max_sp), 3)
    if ask_q - bid_q < 0.01:
        return [
            {
                "time_utc": ts,
                "event_id": cid,
                "market": slug,
                "action": "撤",
                "side": "-",
                "price": "0",
                "price_source": f"book:bid={bid_q} ask={ask_q}",
                "size": "0",
                "fee": "0",
                "pnl": "0",
                "note": "quote_width_too_narrow",
            }
        ]
    src = f"book:{ts}"
    return [
        {
            "time_utc": ts,
            "event_id": cid,
            "market": slug,
            "action": "挂",
            "side": "buy",
            "price": f"{bid_q:.3f}",
            "price_source": src,
            "size": str(size),
            "fee": "0",
            "pnl": "0",
            "note": "yes_token_bid",
        },
        {
            "time_utc": ts,
            "event_id": cid,
            "market": slug,
            "action": "挂",
            "side": "sell",
            "price": f"{ask_q:.3f}",
            "price_source": src,
            "size": str(size),
            "fee": "0",
            "pnl": "0",
            "note": "yes_token_ask",
        },
    ]


def main() -> int:
    if not CAND.exists():
        print("missing candidates; run pm_rewards_market_pick.py first", file=sys.stderr)
        return 1
    data = json.loads(CAND.read_text(encoding="utf-8"))
    top3 = data.get("top3") or []
    # First daily refresh per PLAN: 06:00 UTC cycle (paper timestamp explicit)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if ts < "2026-10-21T06:00:00Z":
        ts = "2026-10-21T06:05:00Z"
    rows: list[dict] = []
    for m in top3:
        rows.extend(quote_market(m, ts))
    fieldnames = [
        "time_utc",
        "event_id",
        "market",
        "action",
        "side",
        "price",
        "price_source",
        "size",
        "fee",
        "pnl",
        "note",
    ]
    write_header = not LEDGER.exists() or LEDGER.stat().st_size == 0
    with LEDGER.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    print(json.dumps({"appended": len(rows), "time_utc": ts}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
