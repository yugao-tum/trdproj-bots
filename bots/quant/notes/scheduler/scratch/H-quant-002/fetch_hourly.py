#!/usr/bin/env python3
"""Fetch free, keyless Binance 1h klines for BTC/ETH and derive tradable fills.

Endpoint: https://data-api.binance.vision/api/v3/klines  (public market data, no key)
Raw pages are cached per symbol-year as .csv.gz under _cache/klines1h/ (each < 1 MB).
Outputs (small, committed):
  fills_{SYM}.csv       date, first_open, first_vwap, first_close, last_vwap, day_close
  daily_{SYM}.csv       date, open, high, low, close, volume, quote_volume
  fetch_stdout.txt

first_vwap = quote_volume / base_volume of the 00:00-01:00 UTC bar (actual trades).
last_vwap  = same for the 23:00-24:00 UTC bar.
No API keys, no trading.
Run: python3 fetch_hourly.py     (first run ~1-2 min for two symbols)
"""
import json, pathlib, time, urllib.request
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "_cache" / "klines1h"
CACHE.mkdir(parents=True, exist_ok=True)
BASE = "https://data-api.binance.vision/api/v3/klines"
START = int(pd.Timestamp("2020-12-25", tz="UTC").timestamp() * 1000)
END = int(pd.Timestamp("2026-10-14", tz="UTC").timestamp() * 1000)
SYMS = ["BTC", "ETH"]
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_base", "taker_quote", "ignore"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def load_year(sym, year):
    p = CACHE / f"{sym}-{year}.csv.gz"
    if p.exists():
        return pd.read_csv(p, parse_dates=["open_time"])
    start = int(pd.Timestamp(f"{year}-01-01", tz="UTC").timestamp() * 1000)
    if year == 2020:
        start = START
    end = int(pd.Timestamp(f"{year + 1}-01-01", tz="UTC").timestamp() * 1000) - 1
    rows, cur = [], start
    while cur <= end:
        url = f"{BASE}?symbol={sym}USDT&interval=1h&startTime={cur}&endTime={min(end, END)}&limit=1000"
        page = get(url)
        if not page:
            break
        rows += page
        cur = page[-1][0] + 3_600_000
        if len(page) < 1000:
            break
    df = pd.DataFrame(rows, columns=COLS)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for c in COLS[1:6] + ["quote_volume"]:
        df[c] = df[c].astype(float)
    df = df[["open_time", "open", "high", "low", "close", "volume", "quote_volume"]]
    df.to_csv(p, index=False, compression="gzip", float_format="%.8f")
    return df


def main():
    out = []
    for sym in SYMS:
        parts = []
        for y in range(2020, 2027):
            df = load_year(sym, y)
            if len(df):
                parts.append(df)
        h = pd.concat(parts).drop_duplicates("open_time").sort_values("open_time")
        h = h[(h.open_time >= pd.Timestamp("2020-12-31", tz="UTC")) &
              (h.open_time < pd.Timestamp("2026-10-14", tz="UTC"))].copy()
        h["date"] = h.open_time.dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None)
        h["vwap"] = h["quote_volume"] / h["volume"].replace(0, float("nan"))
        first = h[h.open_time.dt.hour == 0].set_index("date")
        last = h[h.open_time.dt.hour == 23].set_index("date")
        g = h.groupby("date")
        daily = pd.DataFrame({
            "open": g["open"].first(), "high": g["high"].max(),
            "low": g["low"].min(), "close": g["close"].last(),
            "volume": g["volume"].sum(), "quote_volume": g["quote_volume"].sum(),
        })
        fills = pd.DataFrame({
            "first_open": first["open"], "first_vwap": first["vwap"],
            "first_close": first["close"], "last_vwap": last["vwap"],
            "day_close": daily["close"],
        })
        fills = fills.dropna()
        fills.index.name = "date"
        fills.to_csv(HERE / f"fills_{sym}.csv", float_format="%.8f")
        daily.to_csv(HERE / f"daily_{sym}.csv", float_format="%.8f")
        dev = (fills["first_vwap"] / fills["first_open"] - 1).abs()
        out.append(f"{sym}: hourly rows={len(h)}, days={len(fills)}, "
                   f"{fills.index.min().date()}..{fills.index.max().date()}, "
                   f"median|firstVWAP/firstOpen-1|={dev.median()*1e4:.2f}bp, "
                   f"p95={dev.quantile(.95)*1e4:.2f}bp, "
                   f"max={dev.max()*1e4:.1f}bp")
        print(out[-1])
    (HERE / "fetch_stdout.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
