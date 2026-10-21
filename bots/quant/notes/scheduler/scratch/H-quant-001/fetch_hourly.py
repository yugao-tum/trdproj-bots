#!/usr/bin/env python3
"""Fetch free, keyless Binance 1h klines for BTC/ETH/SOL and derive a tradable
daily fill price = VWAP of the first hourly bar (00:00-01:00 UTC).

Endpoint: https://data-api.binance.vision/api/v3/klines  (public market data, no key)
Raw pages are cached per symbol-year as .csv.gz under _cache/klines1h/ (each < 1 MB).
Output:
  fills_{SYM}.csv  date,first_open,fill_vwap,first_high,first_low,first_close,base_vol,quote_vol
  fetch_stdout.txt
"""
import gzip, io, json, pathlib, time, urllib.request
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "_cache" / "klines1h"
CACHE.mkdir(parents=True, exist_ok=True)
BASE = "https://data-api.binance.vision/api/v3/klines"
START = int(pd.Timestamp("2020-12-25", tz="UTC").timestamp() * 1000)
END = int(pd.Timestamp("2026-10-14", tz="UTC").timestamp() * 1000)
SYMS = ["BTC", "ETH", "SOL"]
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_base", "taker_quote", "ignore"]


def get_page(sym, start):
    url = f"{BASE}?symbol={sym}USDT&interval=1h&startTime={start}&endTime={END}&limit=1000"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def load_year(sym, year):
    p = CACHE / f"{sym}-{year}.csv.gz"
    if p.exists():
        return pd.read_csv(p, parse_dates=["open_time"])
    start = int(pd.Timestamp(f"{year}-01-01", tz="UTC").timestamp() * 1000)
    if year == 2020:
        start = START
    end = int(pd.Timestamp(f"{year + 1}-01-01", tz="UTC").timestamp() * 1000) - 1
    rows = []
    cur = start
    while cur <= end:
        url = f"{BASE}?symbol={sym}USDT&interval=1h&startTime={cur}&endTime={min(end, END)}&limit=1000"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    page = json.loads(r.read())
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
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
              (h.open_time < pd.Timestamp("2026-10-14", tz="UTC"))]
        h["date"] = h.open_time.dt.date
        # first hourly bar of each UTC day is the 00:00 bar
        first = h[h.open_time.dt.hour == 0].copy()
        first["fill_vwap"] = first["quote_volume"] / first["volume"]
        first = first.rename(columns={"open": "first_open", "high": "first_high",
                                      "low": "first_low", "close": "first_close",
                                      "volume": "base_vol", "quote_volume": "quote_vol"})
        first[["date", "first_open", "fill_vwap", "first_high", "first_low",
               "first_close", "base_vol", "quote_vol"]].to_csv(
            HERE / f"fills_{sym}.csv", index=False, float_format="%.8f")
        dev = (first["fill_vwap"] / first["first_open"] - 1).abs()
        out.append(f"{sym}: hourly rows={len(h)}, daily first-hour rows={len(first)}, "
                   f"{first['date'].min()}..{first['date'].max()}, "
                   f"median|VWAP/open-1|={dev.median()*1e4:.2f}bp, "
                   f"p95={dev.quantile(.95)*1e4:.2f}bp")
        print(out[-1])
    (HERE / "fetch_stdout.txt").write_text("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
