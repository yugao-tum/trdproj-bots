#!/usr/bin/env python3
"""composer-008 trade-price replay using Polymarket data-api prints.

Buys the USGS-predicted bracket's YES at the median data-api trade price in the
last 48h of the spec week. Ignores CLOB prices-history. Drops prints at or above
0.97 and anything at or after week end (settlement).
"""
from __future__ import annotations

import json
import statistics
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = ROOT / "notes" / "cache" / "usgs_weekly_55_replay.json"
OUT = Path(__file__).resolve().parent / "trade_replay.json"
GAMMA = "https://gamma-api.polymarket.com/events?slug="
TRADES = "https://data-api.polymarket.com/trades?limit=500&market="
FEE_RATE = 0.05  # weather taker, GUIDE; fee per share = rate * p * (1-p)


def curl_json(url: str):
    raw = subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", url], text=True)
    return json.loads(raw)


def week_bounds(start: str, end: str) -> tuple[datetime, datetime]:
    s = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    e = datetime.fromisoformat(end).replace(tzinfo=timezone.utc)
    return s, e


def yes_trades(condition_id: str) -> list[dict]:
    found: list[dict] = []
    for offset in (0, 500, 1000, 1500):
        url = f"{TRADES}{condition_id}&offset={offset}"
        try:
            batch = curl_json(url)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            found.append({"_error": str(exc), "_offset": offset})
            break
        time.sleep(0.4)
        if isinstance(batch, dict) and batch.get("error"):
            found.append({"_error": batch["error"], "_offset": offset})
            break
        if not isinstance(batch, list) or not batch:
            break
        found.extend(batch)
        if len(batch) < 500:
            break
    return found


def match_market(markets: list[dict], predicted: str) -> dict | None:
    want = predicted.strip()
    for m in markets:
        title = (m.get("groupItemTitle") or "").strip()
        if title == want:
            return m
    return None


def main() -> int:
    src = json.loads(ROWS.read_text(encoding="utf-8"))
    rows_out = []
    for row in src["rows"]:
        predicted = row.get("predicted")
        if not predicted:
            continue
        start, end = week_bounds(row["start"], row["end"])
        window_lo = end - timedelta(hours=48)
        ev = curl_json(GAMMA + row["slug"])
        time.sleep(0.3)
        if isinstance(ev, list):
            ev = ev[0] if ev else {}
        market = match_market(ev.get("markets") or [], predicted)
        item = {
            "slug": row["slug"],
            "predicted": predicted,
            "resolved": row.get("resolved"),
            "match": row.get("match"),
            "window_utc": [window_lo.isoformat(), end.isoformat()],
        }
        if not market or not market.get("conditionId"):
            item["status"] = "no_market"
            rows_out.append(item)
            continue
        cid = market["conditionId"]
        item["conditionId"] = cid
        trades = yes_trades(cid)
        errors = [t for t in trades if "_error" in t]
        prints = []
        for t in trades:
            if "_error" in t:
                continue
            if (t.get("outcome") or "") != "Yes":
                continue
            ts = datetime.fromtimestamp(int(t["timestamp"]), timezone.utc)
            price = float(t["price"])
            if ts < window_lo or ts >= end or price >= 0.97 or price <= 0.02:
                continue
            prints.append({"ts": ts.isoformat(), "price": price, "size": t.get("size")})
        item["trades_fetched"] = len(trades) - len(errors)
        item["yes_in_window"] = len(prints)
        if errors:
            item["fetch_notes"] = errors
        if not prints:
            item["status"] = "no_fill"
            rows_out.append(item)
            continue
        entry = statistics.median(p["price"] for p in prints)
        fee = FEE_RATE * entry * (1 - entry)
        won = bool(row.get("match"))
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
        rows_out.append(item)

    filled = [r for r in rows_out if r.get("status") == "filled"]
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price_source": "https://data-api.polymarket.com/trades",
        "rule": "median YES print in last 48h of spec week on USGS predicted bracket; price in (0.02, 0.97)",
        "fee": "0.05 * p * (1-p) per share",
        "n_predicted": len(rows_out),
        "n_filled": len(filled),
        "mean_net_per_share": round(statistics.mean(r["net_per_share"] for r in filled), 4) if filled else None,
        "rows": rows_out,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("generated_utc", "n_predicted", "n_filled", "mean_net_per_share")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
