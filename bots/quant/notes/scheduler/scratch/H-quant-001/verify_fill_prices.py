#!/usr/bin/env python3
"""Spot-check that the replay fill price is a real executed trade.

The replay uses the daily bar OPEN, which Binance defines as the first trade
of the UTC day.  This script independently asks data-api for the first
aggTrade at/after 00:00:00 UTC on sampled 2024 rebalance dates and compares
it with the daily open used by the replay.

Only 2024 dates are queried (GUIDE sec. 9: never read 2025+ data).
data-api keeps a rolling window of aggTrades, so only dates that still
return data are reported; missing dates are listed, not invented.

Run: python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_fill_prices.py
"""
import datetime as dt
import json
import pathlib
import sys
import urllib.request

sys.dont_write_bytecode = True

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
REPLAY = HERE.parents[3] / "replay/quant-001"
sys.path.insert(0, str(REPLAY))
import run_replay as rr  # noqa: E402

AGG = ("https://data-api.binance.vision/api/v3/aggTrades"
       "?symbol={sym}USDT&startTime={a}&endTime={b}&limit=5")
SYMS = rr.SYMS


def first_trade(sym, day):
    a = int(pd.Timestamp(day, tz="UTC").timestamp() * 1000)
    b = a + 2 * 3600 * 1000
    url = AGG.format(sym=sym, a=a, b=b)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            rows = json.loads(r.read())
    except Exception as e:  # report, do not fabricate
        return None, f"ERR {type(e).__name__}: {e}"
    if not rows:
        return None, "no aggTrades in first 2h (outside retention or no trade)"
    return rows[0], "ok"


def main():
    panels = {s: rr.load(s) for s in SYMS}
    close = pd.DataFrame({s: panels[s]["close"] for s in SYMS}).dropna()
    w_vm = rr.vm_signal(close)
    w_entry = w_vm.shift(1).fillna(0.0)
    # execution dates on which any target weight changes
    move = w_entry.diff().abs().sum(axis=1).fillna(0.0)
    dates = [d for d in move.index if d >= pd.Timestamp("2024-10-15")
             and d <= pd.Timestamp("2024-12-31") and move.loc[d] > 1e-9]
    lines = ["fill-price verification: daily open vs first data-api aggTrade",
             "window checked: 2024-10-15..2024-12-31 (aggTrades retention), 0.30%/side replay",
             ""]
    rows = []
    for d in dates:
        day = d.date().isoformat()
        for s in SYMS:
            if w_entry.loc[d, s] == 0:
                continue
            bar = panels[s].loc[d]
            tr, status = first_trade(s, day)
            rec = {"date": day, "symbol": s, "kline_open": float(bar["open"]),
                   "status": status}
            if tr is not None:
                rec["first_trade_px"] = float(tr["p"])
                rec["first_trade_ms"] = int(tr["T"])
                rec["diff_bp"] = (rec["kline_open"] / rec["first_trade_px"] - 1) * 10000
                rec["seconds_after_open"] = (int(tr["T"]) - int(
                    pd.Timestamp(day, tz="UTC").timestamp() * 1000)) / 1000
            rows.append(rec)
            lines.append(f"{day} {s}: kline_open={rec['kline_open']:.8f} "
                         f"first={rec.get('first_trade_px', float('nan')):.8f} "
                         f"diff_bp={rec.get('diff_bp', float('nan')):+.4f} "
                         f"lag_s={rec.get('seconds_after_open', float('nan')):.1f} "
                         f"[{status}]")
    df = pd.DataFrame(rows)
    df.to_csv(HERE / "verify_fill_prices.csv", index=False, float_format="%.8f")
    ok = df[df.status == "ok"]
    if len(ok):
        max_abs = float(ok.diff_bp.abs().max())
        lines += ["", f"checked executions: {len(ok)} with data, "
                      f"{int((df.status != 'ok').sum())} missing/error",
                  f"max |daily open / first aggTrade - 1| = {max_abs:.4f} bp",
                  f"max lag of first trade after 00:00 UTC = "
                  f"{ok.seconds_after_open.max():.1f} s"]
        assert max_abs < 1.0, "daily open differs from first trade by >= 1 bp"
    else:
        lines += ["", "no aggTrade data returned; verification inconclusive"]
    text = "\n".join(lines)
    print(text)
    (HERE / "verify_fill_prices_stdout.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
