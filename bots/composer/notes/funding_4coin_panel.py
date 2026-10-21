#!/usr/bin/env python3
"""OKX 四币 12mo funding 面板（composer-003 / T03b）。公开 API，免密钥。"""
from __future__ import annotations

import json
import statistics
import subprocess
from pathlib import Path

COINS = ("SOL", "XRP", "ADA", "AVAX")
OUT = Path(__file__).resolve().parent / "funding_4coin_panel.json"
TARGET_PERIODS = 1095  # ~365d * 3 funding/ day


def curl_json(url: str) -> dict:
    out = subprocess.check_output(
        ["curl", "-sS", "-A", "Mozilla/5.0", url], text=True, timeout=120
    )
    return json.loads(out)


def fetch_rates(inst: str, max_periods: int = TARGET_PERIODS) -> list[float]:
    rates: list[float] = []
    after: str | None = None
    while len(rates) < max_periods:
        url = (
            f"https://www.okx.com/api/v5/public/funding-rate-history"
            f"?instId={inst}&limit=100"
        )
        if after:
            url += f"&after={after}"
        payload = curl_json(url)
        if payload.get("code") != "0":
            raise RuntimeError(f"{inst} API {payload}")
        data = payload.get("data") or []
        if not data:
            break
        rates.extend(float(x["fundingRate"]) for x in data)
        after = data[-1]["fundingTime"]
        if len(data) < 100:
            break
    return rates[:max_periods]


def gated_stats(rates: list[float]) -> dict:
    gated: list[float] = []
    for i, r in enumerate(rates):
        if i < 30:
            continue
        w = rates[i - 30 : i]
        sd = statistics.pstdev(w) or 1e-9
        z = (r - statistics.mean(w)) / sd
        if z > 0.5 and r > 0:
            gated.append(r)
    out: dict = {"gated_n": len(gated)}
    if gated:
        m = statistics.mean(gated)
        out["gated_mean_bps"] = round(m * 10000, 4)
        out["gated_annual_pct"] = round(m * 3 * 365 * 100, 2)
    return out


def coin_row(coin: str) -> dict:
    inst = f"{coin}-USDT-SWAP"
    rates = fetch_rates(inst)
    m = statistics.mean(rates) if rates else 0.0
    row = {
        "instId": inst,
        "n": len(rates),
        "days_approx": round(len(rates) / 3, 1),
        "mean_bps": round(m * 10000, 4),
        "frac_positive": round(sum(r > 0 for r in rates) / len(rates), 3) if rates else 0,
        "naive_annual_pct": round(m * 3 * 365 * 100, 2) if rates else 0,
    }
    row.update(gated_stats(rates))
    return row


def main() -> None:
    panel = {"generated_utc": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True).strip(), "coins": []}
    for c in COINS:
        panel["coins"].append(coin_row(c))
    OUT.write_text(json.dumps(panel, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(panel, indent=2))


if __name__ == "__main__":
    main()
