#!/usr/bin/env python3
"""composer-001 static trade replay.

The rule is the entry's sensitivity case, not a recovered SWPC forecast:
buy the YES of bracket \"0\" in the 48h before the week starts (midnight ET).
Weeks whose ladder has no \"0\" market are no_market. Historical forecast
text is not used.
"""
from __future__ import annotations

import json
import re
import statistics
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent / "trade_replay.json"
SEARCH = (
    "https://gamma-api.polymarket.com/public-search"
    "?q=how-many-major-space-weather-events&limit_per_type=50&events_status=closed"
)
TRADES = "https://data-api.polymarket.com/trades?limit=500&market="
FEE_RATE = 0.05  # weather taker, same schedule as composer-008
MONTHS = {
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


def curl_json(url: str):
    raw = subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", "--max-time", "40", url], text=True)
    return json.loads(raw)


def week_start(slug: str, end_date: str) -> datetime:
    match = re.search(r"this-week-([a-z]+)-(\d+)-", slug)
    if not match:
        raise ValueError(slug)
    year = datetime.fromisoformat(end_date.replace("Z", "+00:00")).year
    # April–May 2026 are EDT, so midnight ET is 04:00 UTC.
    return datetime(year, MONTHS[match.group(1)], int(match.group(2)), 4, tzinfo=timezone.utc)


def yes_won(market: dict) -> bool:
    prices = market.get("outcomePrices")
    if isinstance(prices, str):
        prices = json.loads(prices)
    return bool(prices) and str(prices[0]) in {"1", "1.0"}


def yes_trades(condition_id: str) -> list[dict]:
    found: list[dict] = []
    for offset in (0, 500, 1000, 1500):
        try:
            batch = curl_json(f"{TRADES}{condition_id}&offset={offset}")
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            found.append({"_error": str(exc), "_offset": offset})
            break
        time.sleep(0.35)
        if isinstance(batch, dict) and batch.get("error"):
            found.append({"_error": batch["error"], "_offset": offset})
            break
        if not isinstance(batch, list) or not batch:
            break
        found.extend(batch)
        if len(batch) < 500:
            break
    return found


def main() -> int:
    payload = curl_json(SEARCH)
    events = [e for e in payload.get("events") or [] if "space-weather" in (e.get("slug") or "")]
    rows = []
    for event in sorted(events, key=lambda e: e.get("endDate") or ""):
        markets = event.get("markets") or []
        winner = next((m.get("groupItemTitle") for m in markets if yes_won(m)), None)
        zero = next((m for m in markets if (m.get("groupItemTitle") or "").strip() == "0"), None)
        start = week_start(event["slug"], event["endDate"])
        window_lo = start - timedelta(hours=48)
        item = {
            "slug": event["slug"],
            "endDate": event["endDate"],
            "titles": [m.get("groupItemTitle") for m in markets],
            "resolved": winner,
            "predicted": "0" if zero else None,
            "window_utc": [window_lo.isoformat(), start.isoformat()],
        }
        if zero is None:
            item["status"] = "no_market"
            item["note"] = "ladder has no bracket titled 0; lowest bracket was not substituted"
            rows.append(item)
            continue
        item["match"] = winner == "0"
        cid = zero.get("conditionId")
        item["conditionId"] = cid
        trades = yes_trades(cid)
        errors = [t for t in trades if "_error" in t]
        prints = []
        for trade in trades:
            if "_error" in trade or (trade.get("outcome") or "") != "Yes":
                continue
            ts = datetime.fromtimestamp(int(trade["timestamp"]), timezone.utc)
            price = float(trade["price"])
            if ts < window_lo or ts >= start or price >= 0.97 or price <= 0.02:
                continue
            prints.append(price)
        item["trades_fetched"] = len(trades) - len(errors)
        item["yes_in_window"] = len(prints)
        if errors:
            item["fetch_notes"] = errors
        if not prints:
            item["status"] = "no_fill"
            rows.append(item)
            continue
        entry = statistics.median(prints)
        fee = FEE_RATE * entry * (1 - entry)
        won = winner == "0"
        net = ((1 - entry) - fee) if won else (-entry - fee)
        item.update(
            {
                "status": "filled",
                "entry_price": round(entry, 4),
                "fee_per_share": round(fee, 4),
                "won": won,
                "net_per_share": round(net, 4),
                "price_source": "data-api",
            }
        )
        rows.append(item)

    filled = [r for r in rows if r.get("status") == "filled"]
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price_source": "https://data-api.polymarket.com/trades",
        "rule": (
            "static sensitivity only: buy YES on the bracket titled 0 during the 48h "
            "before midnight ET on the slug's first day. No historical SWPC forecast text. "
            "Weeks with no 0 bracket are no_market. Price in (0.02, 0.97)."
        ),
        "fee": "0.05 * p * (1-p) per share",
        "n_events": len(rows),
        "n_with_zero_bracket": sum(1 for r in rows if r.get("predicted") == "0"),
        "n_filled": len(filled),
        "n_won": sum(1 for r in filled if r.get("won")),
        "mean_net_per_share": round(statistics.mean(r["net_per_share"] for r in filled), 4) if filled else None,
        "rows": rows,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: out[k]
                for k in ("generated_utc", "n_events", "n_with_zero_bracket", "n_filled", "n_won", "mean_net_per_share")
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
