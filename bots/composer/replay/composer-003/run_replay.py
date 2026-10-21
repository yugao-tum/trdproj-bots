#!/usr/bin/env python3
"""composer-003 OKX funding z-score gate replay (R2 development window only).

Public OKX `funding-rate-history` paginates ~278 rows (~93d) per instrument; this script
filters to window 2022-01-01..2024-12-31 UTC inclusive. No 2025+ rows enter stats.

Output: replay/composer-003/replay_results.json + stdout summary.
"""
from __future__ import annotations

import json
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "replay_results.json"

WINDOW_START = datetime(2022, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
COINS = ("SOL", "XRP", "ADA", "AVAX")
Z_WINDOW = 30
Z_THRESH = 0.5
NOTIONAL = 2000.0  # USDT per active leg (entry §成本)
FEE_EACH_WAY = 0.003  # 0.30% per GUIDE §9


def curl_json(url: str) -> dict:
    out = subprocess.check_output(["curl", "-sS", "-A", "Mozilla/5.0", url], text=True)
    return json.loads(out)


def fetch_funding(inst_id: str, max_pages: int = 50) -> list[dict]:
    rows: list[dict] = []
    after: str | None = None
    for _ in range(max_pages):
        url = (
            f"https://www.okx.com/api/v5/public/funding-rate-history"
            f"?instId={inst_id}&limit=100"
        )
        if after:
            url += f"&after={after}"
        payload = curl_json(url)
        if payload.get("code") != "0":
            raise RuntimeError(payload)
        batch = payload.get("data") or []
        if not batch:
            break
        for x in batch:
            ts = int(x["fundingTime"]) / 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            if dt < WINDOW_START:
                return rows
            if dt <= WINDOW_END:
                rows.append(
                    {
                        "time_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "rate": float(x["fundingRate"]),
                    }
                )
        after = batch[-1]["fundingTime"]
        if len(batch) < 100:
            break
    return rows


def z_gate_backtest(rates: list[float]) -> dict:
    """Each 8h settlement = 1 independent result when gate allows carry."""
    if len(rates) <= Z_WINDOW:
        return {"n_total": len(rates), "n_gated": 0, "independent_results": 0}

    gated_rates: list[float] = []
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    prev_active = False

    for i in range(Z_WINDOW, len(rates)):
        w = rates[i - Z_WINDOW : i]
        r = rates[i]
        mu = statistics.mean(w)
        sd = statistics.pstdev(w) or 1e-12
        z = (r - mu) / sd
        active = z > Z_THRESH and r > 0
        if active:
            gated_rates.append(r)
        period_pnl = (r * NOTIONAL) if active else 0.0
        if active != prev_active:
            period_pnl -= NOTIONAL * FEE_EACH_WAY * 2
        prev_active = active
        cum += period_pnl
        peak = max(peak, cum)
        dd = (peak - cum) / 5000.0 if peak > 0 else 0.0
        max_dd = max(max_dd, dd)

    net = cum
    days = max(1, len(rates) / 3)
    years = days / 365.0
    ann = (net / 5000.0) / years if years else 0.0

    return {
        "n_total": len(rates) - Z_WINDOW,
        "n_gated": len(gated_rates),
        "independent_results": len(rates) - Z_WINDOW,
        "gated_frac": round(len(gated_rates) / max(1, len(rates) - Z_WINDOW), 3),
        "mean_gated_bps": round(statistics.mean(gated_rates) * 10000, 4) if gated_rates else None,
        "net_pnl_usdt": round(net, 2),
        "max_dd_pct": round(max_dd * 100, 2),
        "ann_contribution_pct": round(ann * 100, 2),
    }


def main() -> int:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report: dict = {
        "id": "composer-003",
        "generated_utc": generated,
        "window": "2022-01-01..2024-12-31",
        "instruments": list(COINS),
        "params": {"z_window": Z_WINDOW, "z_thresh": Z_THRESH, "notional": NOTIONAL},
        "coins": {},
    }

    for coin in COINS:
        inst = f"{coin}-USDT-SWAP"
        try:
            rows = fetch_funding(inst)
        except Exception as e:
            report["coins"][coin] = {"error": str(e)}
            continue
        rates = [x["rate"] for x in sorted(rows, key=lambda x: x["time_utc"])]
        stats = z_gate_backtest(rates) if rates else {"n_total": 0, "independent_results": 0}
        report["coins"][coin] = {
            "instId": inst,
            "rows_in_window": len(rows),
            "first": rows[0]["time_utc"] if rows else None,
            "last": rows[-1]["time_utc"] if rows else None,
            **stats,
        }

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
