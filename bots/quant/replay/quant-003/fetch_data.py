#!/usr/bin/env python3
"""Download Binance spot daily klines 2022-01..2024-12 for the frozen top-10
universe (list carried over from PRESPEC_R003, see
bots/quant/notes/r2prep-verification/quant-003.md) into _cache/ as CSV.

Only public, keyless URLs: https://data.binance.vision/data/spot/monthly/klines/
No 2021-or-earlier and no 2025-or-later data is requested.
"""
import io
import pathlib
import urllib.request
import zipfile
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "_cache"
DATA.mkdir(exist_ok=True)
SYMS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "LTCUSDT", "GRTUSDT",
        "BCHUSDT", "LINKUSDT", "BNBUSDT", "ADAUSDT", "XLMUSDT"]
BASE = "https://data.binance.vision/data/spot/monthly/klines"
MONTHS = pd.period_range("2022-01", "2024-12", freq="M")
START, END = "2022-01-01", "2024-12-31"


def get(url, tries=4):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:  # transient S3 disconnects happen under concurrency
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def build(sym):
    cache = DATA / f"{sym}_1d_2022_2024.csv"
    if cache.exists():
        df = pd.read_csv(cache, index_col=0, parse_dates=True)
        return sym, f"cached {len(df)} rows {df.index[0].date()}..{df.index[-1].date()}"
    urls = [f"{BASE}/{sym}/1d/{sym}-1d-{m}.zip" for m in MONTHS]

    def fetch(u):
        z = zipfile.ZipFile(io.BytesIO(get(u)))
        return pd.read_csv(z.open(z.namelist()[0]), header=None).iloc[:, :8]

    with ThreadPoolExecutor(max_workers=6) as ex:
        frames = list(ex.map(fetch, urls))
    raw = pd.concat(frames)
    t = raw[0].astype("int64")
    t = np.where(t > 10**14, t // 1000, t)
    df = pd.DataFrame({"open": raw[1].values, "high": raw[2].values,
                       "low": raw[3].values, "close": raw[4].values,
                       "volume": raw[5].values, "quote_volume": raw[7].values},
                      index=pd.to_datetime(t, unit="ms")).sort_index()
    df = df[~df.index.duplicated()].loc[START:END].astype(float)
    df.to_csv(cache)
    return sym, f"{len(df)} rows {df.index[0].date()}..{df.index[-1].date()}"


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=10) as ex:
        for sym, msg in ex.map(build, SYMS):
            print(sym, msg)
    panel = pd.DataFrame({s: pd.read_csv(DATA / f"{s}_1d_2022_2024.csv",
                                         index_col=0, parse_dates=True)["close"]
                          for s in SYMS}).dropna()
    print("common close panel:", panel.index[0].date(), panel.index[-1].date(), len(panel))
