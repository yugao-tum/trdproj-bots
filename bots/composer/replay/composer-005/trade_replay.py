#!/usr/bin/env python3
"""composer-005 trade-price replay using Polymarket data-api prints.

Pre-statement rule only. For each closed dissent event after the first,
the predicted bracket is the mode of earlier resolved counts (tie → smaller
count). Entry is the median YES print on that bracket in the 48h before
16:00 UTC on the event end date, which is before the usual 14:00 ET statement.
Ignores CLOB prices-history. Drops prints at or above 0.97.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = ROOT / "notes" / "dissent_resolved.json"
OUT = Path(__file__).resolve().parent / "trade_replay.json"
GAMMA = "https://gamma-api.polymarket.com/events?slug="
TRADES = "https://data-api.polymarket.com/trades?limit=500&market="
FEE_RATE = 0.05  # economics taker, entry composer-005; fee per share = rate * p * (1-p)


def curl_json(url: str):
    raw = subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", url], text=True)
    return json.loads(raw)


def bracket_key(label: str) -> int:
    text = label.strip()
    if text.endswith("+"):
        return 99
    return int(text)


def prior_mode(history: list[str]) -> str | None:
    if not history:
        return None
    counts = Counter(history)
    best = max(counts.values())
    cands = [k for k, v in counts.items() if v == best]
    return min(cands, key=bracket_key)


def cutoff(end_date: str) -> datetime:
    day = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
    return day.replace(hour=16, minute=0, second=0, microsecond=0)


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
    for market in markets:
        title = (market.get("groupItemTitle") or "").strip()
        if title == want:
            return market
    return None


def main() -> int:
    src = json.loads(ROWS.read_text(encoding="utf-8"))
    closed = [r for r in src["rows"] if r.get("resolved")]
    closed.sort(key=lambda r: r["endDate"])
    history: list[str] = []
    rows_out = []
    for row in closed:
        predicted = prior_mode(history)
        end = cutoff(row["endDate"])
        window_lo = end - timedelta(hours=48)
        item = {
            "slug": row["slug"],
            "endDate": row["endDate"],
            "resolved": row["resolved"],
            "predicted": predicted,
            "prior": list(history),
            "window_utc": [window_lo.isoformat(), end.isoformat()],
        }
        history.append(row["resolved"])
        if predicted is None:
            item["status"] = "no_prior"
            rows_out.append(item)
            continue
        item["match"] = predicted == row["resolved"]
        ev = curl_json(GAMMA + row["slug"])
        time.sleep(0.3)
        if isinstance(ev, list):
            ev = ev[0] if ev else {}
        market = match_market(ev.get("markets") or [], predicted)
        if not market or not market.get("conditionId"):
            item["status"] = "no_market"
            rows_out.append(item)
            continue
        cid = market["conditionId"]
        item["conditionId"] = cid
        trades = yes_trades(cid)
        errors = [t for t in trades if "_error" in t]
        prints = []
        for trade in trades:
            if "_error" in trade:
                continue
            if (trade.get("outcome") or "") != "Yes":
                continue
            ts = datetime.fromtimestamp(int(trade["timestamp"]), timezone.utc)
            price = float(trade["price"])
            if ts < window_lo or ts >= end or price >= 0.97 or price <= 0.02:
                continue
            prints.append({"ts": ts.isoformat(), "price": price, "size": trade.get("size")})
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
        won = predicted == row["resolved"]
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

    scored = [r for r in rows_out if r.get("status") == "filled"]
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "price_source": "https://data-api.polymarket.com/trades",
        "rule": (
            "predicted bracket = mode of prior resolved counts (tie → smaller count); "
            "median YES print in the 48h before 16:00 UTC on endDate; price in (0.02, 0.97); "
            "window ends before the usual 14:00 ET FOMC statement"
        ),
        "fee": "0.05 * p * (1-p) per share",
        "n_resolved": len(closed),
        "n_predicted": sum(1 for r in rows_out if r.get("predicted")),
        "n_filled": len(scored),
        "n_won": sum(1 for r in scored if r.get("won")),
        "mean_net_per_share": round(statistics.mean(r["net_per_share"] for r in scored), 4) if scored else None,
        "rows": rows_out,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {k: out[k] for k in ("generated_utc", "n_resolved", "n_predicted", "n_filled", "n_won", "mean_net_per_share")},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
