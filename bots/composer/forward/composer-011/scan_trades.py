#!/usr/bin/env python3
"""Scan data-api trades vs composer-011 ledger 挂 prices; append 成交 rows."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "ledger.csv"
OUT = Path(__file__).resolve().parent / "scan_latest.json"


def curl_json(url: str):
    return json.loads(subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", url], text=True))


def main() -> int:
    if not LEDGER.exists():
        print("no ledger", file=sys.stderr)
        return 1
    quotes: list[dict] = []
    with LEDGER.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("action") == "挂":
                quotes.append(row)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    appended = 0
    matches: list[dict] = []
    by_cid: dict[str, list[dict]] = {}
    for q in quotes:
        by_cid.setdefault(q["event_id"], []).append(q)

    new_rows: list[dict] = []
    for cid, qs in by_cid.items():
        trades = curl_json(f"https://data-api.polymarket.com/trades?market={cid}&limit=200")
        if not isinstance(trades, list):
            continue
        prices = {round(float(q["price"]), 3) for q in qs}
        for t in trades:
            p = round(float(t["price"]), 3)
            if p not in prices:
                continue
            side = (t.get("side") or "").lower()
            new_rows.append(
                {
                    "time_utc": ts,
                    "event_id": cid,
                    "market": t.get("slug") or qs[0]["market"],
                    "action": "成交",
                    "side": side,
                    "price": f"{p:.3f}",
                    "price_source": f"data-api:{t.get('transactionHash','')[:18]}",
                    "size": str(min(float(t.get("size") or 0), 200)),
                    "fee": "0",
                    "pnl": "0",
                    "note": "matched_ledger_quote_pessimistic",
                }
            )
            matches.append({"cid": cid, "price": p, "hash": t.get("transactionHash")})
            appended += 1

    if new_rows:
        fieldnames = list(new_rows[0].keys())
        with LEDGER.open("a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            for r in new_rows:
                w.writerow(r)

    OUT.write_text(
        json.dumps(
            {"scanned_utc": ts, "quote_levels": len(prices) if quotes else 0, "fills_appended": appended, "matches": matches[:20]},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"fills_appended": appended, "scanned_utc": ts}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
