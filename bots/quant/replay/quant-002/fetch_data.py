#!/usr/bin/env python3
"""quant-002 replay data fetch: free, keyless Binance spot klines, 2022-2024 only.

Endpoints (full query URLs, verified in verify_sources.py):
  https://data-api.binance.vision/api/v3/klines
      ?symbol=BTCUSDT&interval=1d&startTime=...&endTime=...&limit=1000
      ?symbol=BTCUSDT&interval=1h&startTime=...&endTime=...&limit=1000

Window: 2022-01-01 00:00 UTC .. 2024-12-31 23:59 UTC (GUIDE section 9).
2021 and 2025+ are deliberately NOT requested.

Raw 1d pages are cached under _cache/ (gitignored).  The 1h pages are not kept
raw (they are ~3 MB); only the derived first/last-hour VWAP is saved, so every
file in the worktree stays < 1 MB.  Outputs: daily_{SYM}.csv
(open/high/low/close/volume/quote_volume) and hourly_{SYM}.csv
(first_hour_vwap/last_hour_vwap) for each day.

No API keys, no trading.
Run: python3 fetch_data.py
"""
import json
import pathlib
import time
import urllib.request

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "_cache"
CACHE.mkdir(parents=True, exist_ok=True)
BASE = "https://data-api.binance.vision/api/v3/klines"
SYMS = ["BTC", "ETH"]
START = pd.Timestamp("2022-01-01 00:00:00", tz="UTC")
END = pd.Timestamp("2025-01-01 00:00:00", tz="UTC")  # exclusive
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_base", "taker_quote", "ignore"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (quant replay)"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def download(sym, interval, keep_raw=True):
    cache = CACHE / f"{sym}-{interval}.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["open_time"])
    rows, cur = [], int(START.timestamp() * 1000)
    end = int(END.timestamp() * 1000) - 1
    step = 24 * 3600 * 1000 if interval == "1d" else 3600 * 1000
    while cur <= end:
        url = (f"{BASE}?symbol={sym}USDT&interval={interval}"
               f"&startTime={cur}&endTime={end}&limit=1000")
        page = get(url)
        if not page:
            break
        rows += page
        cur = page[-1][0] + step
        if len(page) < 1000:
            break
        time.sleep(0.05)
    df = pd.DataFrame(rows, columns=COLS)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for c in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[c] = df[c].astype(float)
    df = df[["open_time", "open", "high", "low", "close", "volume", "quote_volume"]]
    df = df[(df.open_time >= START) & (df.open_time < END)].drop_duplicates("open_time")
    if keep_raw:
        df.to_csv(cache, index=False, float_format="%.8f")
    return df


def main():
    lines = []
    for sym in SYMS:
        d = download(sym, "1d")
        d = d.set_index("open_time").sort_index()
        d.index.name = "date"
        d.to_csv(CACHE / f"daily_{sym}.csv", float_format="%.8f")
        h = download(sym, "1h", keep_raw=False)
        h["date"] = h.open_time.dt.normalize()
        h["vwap"] = h["quote_volume"] / h["volume"].replace(0, float("nan"))
        first = h[h.open_time.dt.hour == 0].set_index("date")["vwap"]
        last = h[h.open_time.dt.hour == 23].set_index("date")["vwap"]
        fills = pd.DataFrame({"first_hour_vwap": first, "last_hour_vwap": last}).dropna()
        fills.index.name = "date"
        fills.to_csv(CACHE / f"hourly_{sym}.csv", float_format="%.8f")
        lines.append(f"{sym}: daily rows={len(d)} {d.index.min().date()}..{d.index.max().date()}; "
                     f"hourly rows={len(h)}; first/last-hour VWAP days={len(fills)}")
    text = "\n".join(lines)
    print(text)
    (HERE / "_cache" / "fetch_stdout.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
