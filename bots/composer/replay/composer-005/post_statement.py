#!/usr/bin/env python3
"""composer-005 post-statement lag check on data-api YES prints.

The bracket is the resolved count, which the statement has already made public.
Window is 14:00–18:00 ET on the event end date (18:00–22:00 UTC in EDT,
19:00–23:00 UTC in EST). The tradable entry is the median YES print from
minute 2 to minute 30. The opening two minutes are stale statement-second
prints and are not the fill. Prints at or above 0.97 are settlement.
"""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trade_replay import FEE_RATE, GAMMA, ROOT, curl_json, match_market, yes_trades

ROWS = ROOT / "notes" / "dissent_resolved.json"
OUT = Path(__file__).resolve().parent / "post_statement.json"
EST_DATES = {"2025-12-10", "2026-01-28"}


def window_for(end_date: str) -> tuple[datetime, datetime, str]:
    day = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    if end_date in EST_DATES:
        start = day.replace(hour=19, minute=0, second=0, microsecond=0)
        note = "EST: 19:00–23:00 UTC = 14:00–18:00 ET"
    else:
        start = day.replace(hour=18, minute=0, second=0, microsecond=0)
        note = "EDT: 18:00–22:00 UTC = 14:00–18:00 ET"
    return start, start + timedelta(hours=4), note


def main() -> int:
    src = json.loads(ROWS.read_text(encoding="utf-8"))
    closed = [r for r in src["rows"] if r.get("resolved")]
    closed.sort(key=lambda r: r["endDate"])
    rows_out = []
    for row in closed:
        start, end, note = window_for(row["endDate"])
        predicted = row["resolved"]
        item = {
            "slug": row["slug"],
            "endDate": row["endDate"],
            "resolved": predicted,
            "predicted": predicted,
            "window_utc": [start.isoformat(), end.isoformat()],
            "window_note": note,
        }
        ev = curl_json(GAMMA + row["slug"])
        if isinstance(ev, list):
            ev = ev[0] if ev else {}
        market = match_market(ev.get("markets") or [], predicted)
        if not market or not market.get("conditionId"):
            item["status"] = "no_market"
            rows_out.append(item)
            continue
        item["conditionId"] = market["conditionId"]
        trades = yes_trades(item["conditionId"])
        errors = [t for t in trades if "_error" in t]
        in_band = []
        early = []
        readable = []
        ge_097 = 0
        any_yes = 0
        read_lo = start + timedelta(minutes=2)
        read_hi = start + timedelta(minutes=30)
        for trade in trades:
            if "_error" in trade or (trade.get("outcome") or "") != "Yes":
                continue
            ts = datetime.fromtimestamp(int(trade["timestamp"]), timezone.utc)
            if ts < start or ts >= end:
                continue
            any_yes += 1
            price = float(trade["price"])
            if price >= 0.97 or price <= 0.02:
                ge_097 += 1
                continue
            in_band.append(price)
            if ts < read_lo:
                early.append(price)
            elif ts < read_hi:
                readable.append(price)
        item["trades_fetched"] = len(trades) - len(errors)
        item["yes_in_window"] = any_yes
        item["yes_settlement_prints"] = ge_097
        item["yes_in_band"] = len(in_band)
        item["yes_first_2min"] = len(early)
        item["yes_2min_to_30min"] = len(readable)
        if in_band:
            item["four_hour_median"] = round(statistics.median(in_band), 4)
        if early:
            item["first_2min_median"] = round(statistics.median(early), 4)
        if errors:
            item["fetch_notes"] = errors
        if not readable:
            item["status"] = "no_fill"
            item["no_fill_reason"] = "no YES print in (0.02, 0.97) from minute 2 to minute 30"
            rows_out.append(item)
            continue
        entry = statistics.median(readable)
        fee = FEE_RATE * entry * (1 - entry)
        net = (1 - entry) - fee
        item.update(
            {
                "status": "filled",
                "entry_price": round(entry, 4),
                "fee_per_share": round(fee, 4),
                "won": True,
                "net_per_share": round(net, 4),
                "price_source": "data-api",
                "win_by_construction": True,
            }
        )
        rows_out.append(item)

    filled = [r for r in rows_out if r.get("status") == "filled"]
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price_source": "https://data-api.polymarket.com/trades",
        "rule": (
            "predicted bracket = resolved count (statement already public); "
            "tradable entry = median YES print from minute 2 to minute 30 after 14:00 ET, "
            "price in (0.02, 0.97). The first 2 minutes are reported separately because they "
            "are the statement-second stale prints. four_hour_median covers 14:00–18:00 ET "
            "and is not the fill. EDT uses 18:00 UTC; EST dates 2025-12-10 and 2026-01-28 use 19:00 UTC"
        ),
        "fee": "0.05 * p * (1-p) per share",
        "n_resolved": len(closed),
        "n_filled": len(filled),
        "n_no_fill": sum(1 for r in rows_out if r.get("status") == "no_fill"),
        "mean_net_per_share": round(statistics.mean(r["net_per_share"] for r in filled), 4) if filled else None,
        "rows": rows_out,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {k: out[k] for k in ("generated_utc", "n_resolved", "n_filled", "n_no_fill", "mean_net_per_share")},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
