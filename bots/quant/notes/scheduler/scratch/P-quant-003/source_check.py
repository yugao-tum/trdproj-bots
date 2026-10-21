#!/usr/bin/env python3
"""Re-verify every data URL cited by quant-003 and the local cache bounds.
Only free, keyless public GETs.  Deliberately does NOT touch 2021-or-earlier
or 2025-or-later files (GUIDE section 9 hold-out)."""
import pathlib
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
URLS = [
    "https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1d/",
    "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/BTCUSDT/1d/",
    "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2022-01.zip",
    "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-12.zip",
    "https://data.binance.vision/data/spot/monthly/klines/GRTUSDT/1d/GRTUSDT-1d-2022-01.zip",
    "https://data.binance.vision/data/spot/monthly/klines/XLMUSDT/1d/XLMUSDT-1d-2024-12.zip",
    "https://data.binance.vision/data/spot/monthly/klines/ADAUSDT/1d/ADAUSDT-1d-2023-06.zip",
]

for u in URLS:
    try:
        with urllib.request.urlopen(u, timeout=60) as r:
            b = r.read()
        print(f"HTTP {r.status} bytes {len(b)} type {r.headers.get('Content-Type')}  {u}")
    except Exception as e:
        print(f"FAIL {type(e).__name__}: {e}  {u}")

print("\nlocal cache bounds (must stay inside 2022-01-01..2024-12-31):")
import pandas as pd
bad = []
for p in sorted((HERE / "_cache").glob("*_1d_2022_2024.csv")):
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    lo, hi = df.index[0].date(), df.index[-1].date()
    ok = str(lo) >= "2022-01-01" and str(hi) <= "2024-12-31"
    if not ok:
        bad.append(p.name)
    print(f"  {p.stem:28s} rows {len(df):4d}  {lo}..{hi}  {'ok' if ok else 'OUT OF WINDOW'}")
print(f"\nfiles outside window: {len(bad)}")
