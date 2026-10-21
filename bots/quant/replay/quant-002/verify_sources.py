#!/usr/bin/env python3
"""Verify every source cited by quant-002 and the numbers the entry quotes.

Checks (all keyless public endpoints, all inside the 2022-2024 development window):
 1. data.binance.vision listing pages for BTC/ETH daily klines (HTTP 200).
 2. A real monthly zip (2024-12) for BTC and ETH: HTTP 200, zip member, rows, cols.
 3. Full daily and hourly klines query URLs used by fetch_data.py: HTTP 200, rows.
 4. aggTrades for 2024-10-09 00:00-01:00 UTC: first trade price == daily open;
    trade VWAP == first-hour VWAP in _cache/hourly_BTC.csv (proves the fill is a
    real traded price, not a modelled one).
 5. Local merged notes exist; the old xqt-migration window is as claimed.
 6. known/KNOWN.md contains E-E2-turn-of-month.
 7. Entry front matter keeps id/date/status.

No keys, no trading.  Writes verify_stdout.txt.
Run: python3 verify_sources.py
"""
import io
import json
import pathlib
import re
import urllib.request
import zipfile

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
BOT = HERE.parent.parent
ENTRY = BOT / "entries" / "quant-002-tom-monday-oos-counterevidence.md"
NOTES = BOT / "notes"
CACHE = HERE / "_cache"
UA = {"User-Agent": "Mozilla/5.0 (compatible; quant-replay/1.0)"}
lines = []


def fetch(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.geturl(), r.read()


def main():
    # 1-2. monthly archive pages and real zips (2024-12, inside the window)
    for sym in ("BTC", "ETH"):
        page = f"https://data.binance.vision/?prefix=data/spot/monthly/klines/{sym}USDT/1d/"
        try:
            status, final, body = fetch(page)
            lines.append(f"listing_{sym}: HTTP {status} bytes={len(body)} url={final}")
        except Exception as e:
            lines.append(f"listing_{sym}: ERROR {type(e).__name__} {getattr(e, 'code', '')}")
        zurl = f"https://data.binance.vision/data/spot/monthly/klines/{sym}USDT/1d/{sym}USDT-1d-2024-12.zip"
        try:
            status, final, body = fetch(zurl)
            z = zipfile.ZipFile(io.BytesIO(body))
            member = z.namelist()[0]
            df = pd.read_csv(z.open(member), header=None)
            lines.append(f"zip_{sym}_2024_12: HTTP {status} bytes={len(body)} "
                         f"member={member} rows={len(df)} cols={df.shape[1]} "
                         f"first={df.iloc[0,0]} last={df.iloc[-1,0]} url={final}")
        except Exception as e:
            lines.append(f"zip_{sym}_2024_12: ERROR {type(e).__name__} {getattr(e, 'code', '')}")

    # 3. exact query URLs used by fetch_data.py
    start = 1640995200000  # 2022-01-01 00:00 UTC
    end = 1735689599999    # 2024-12-31 23:59:59.999 UTC
    for sym in ("BTC", "ETH"):
        for interval in ("1d", "1h"):
            url = (f"https://data-api.binance.vision/api/v3/klines?symbol={sym}USDT"
                   f"&interval={interval}&startTime={start}&endTime={end}&limit=1000")
            try:
                status, final, body = fetch(url)
                rows = json.loads(body)
                lines.append(f"klines_{sym}_{interval}: HTTP {status} rows={len(rows)} "
                             f"cols={len(rows[0]) if rows else 0} url={final}")
            except Exception as e:
                lines.append(f"klines_{sym}_{interval}: ERROR {type(e).__name__} "
                             f"{getattr(e, 'code', '')}")

    # 3b. derived caches actually cover the full 2022-2024 window
    for sym in ("BTC", "ETH"):
        d = pd.read_csv(CACHE / f"daily_{sym}.csv", parse_dates=["date"])
        h = pd.read_csv(CACHE / f"hourly_{sym}.csv", parse_dates=["date"])
        lines.append(f"derived_{sym}: daily_rows={len(d)} "
                     f"{d.date.min().date()}..{d.date.max().date()}; "
                     f"hourly_vwap_rows={len(h)}")

    # 4. aggTrades cross-check: daily open and first-hour VWAP are real trades
    try:
        t0 = int(pd.Timestamp("2024-10-09 00:00:00", tz="UTC").timestamp() * 1000)
        t1 = int(pd.Timestamp("2024-10-09 01:00:00", tz="UTC").timestamp() * 1000) - 1
        base = "https://data-api.binance.vision/api/v3/aggTrades"
        url = f"{base}?symbol=BTCUSDT&startTime={t0}&endTime={t1}&limit=1000"
        status, _, body = fetch(url)
        page = json.loads(body)
        trades, pages = list(page), 1
        while len(page) == 1000 and pages < 80:
            last_id = page[-1]["a"]
            status, _, body = fetch(f"{base}?symbol=BTCUSDT&fromId={last_id + 1}&limit=1000")
            page = [t for t in json.loads(body) if t["T"] <= t1]
            trades += page
            pages += 1
            if not page:
                break
        quote = sum(float(t["p"]) * float(t["q"]) for t in trades)
        baseq = sum(float(t["q"]) for t in trades)
        at_vwap = quote / baseq
        first_price = float(trades[0]["p"])
        daily = pd.read_csv(CACHE / "daily_BTC.csv", parse_dates=["date"], index_col="date")
        hourly = pd.read_csv(CACHE / "hourly_BTC.csv", parse_dates=["date"], index_col="date")
        k_open = float(daily.loc["2024-10-09", "open"])
        k_vwap = float(hourly.loc["2024-10-09", "first_hour_vwap"])
        lines.append(f"aggtrades_2024_10_09: HTTP {status} pages={pages} trades={len(trades)} "
                     f"first_trade={first_price:.8f} daily_open={k_open:.8f} "
                     f"open_diff_bp={(first_price / k_open - 1) * 1e4:.6f} url={url}")
        lines.append(f"aggtrades_vwap_2024_10_09: trades_vwap={at_vwap:.8f} "
                     f"kline_first_hour_vwap={k_vwap:.8f} "
                     f"diff_bp={(at_vwap / k_vwap - 1) * 1e4:.6f}")
    except Exception as e:
        lines.append(f"aggtrades_2024_10_09: ERROR {type(e).__name__} {getattr(e, 'code', '')}")

    # 5. local merged notes
    lines.append("")
    lines.append("local merged notes:")
    for rel in ["xqt-migration/README.md", "xqt-migration/reproduce.py", "xqt-migration/results.csv"]:
        p = NOTES / rel
        lines.append(f"  {rel}: exists={p.exists()} bytes={p.stat().st_size if p.exists() else 0}")
    readme = (NOTES / "xqt-migration" / "README.md").read_text()
    lines.append(f"  README states 2020-12-31..2026-10-13 full-window protocol: "
                 f"{'2020-12-31 至 2026-10-13' in readme}")
    res = pd.read_csv(NOTES / "xqt-migration" / "results.csv")
    names = sorted(set(res.name))
    m3 = [n for n in names if n.startswith("M3_")]
    lines.append(f"  results.csv M3 rows: {len(m3)} names, e.g. {m3[:3]}")

    # 5b. replay artefacts and scratch stdout copies
    lines.append("")
    lines.append("replay artefacts:")
    for rel in ["SUMMARY.md", "fetch_data.py", "backtest.py", "results_variants.csv",
                "trades.csv", "placebo.csv"]:
        p = HERE / rel
        lines.append(f"  replay/quant-002/{rel}: exists={p.exists()} "
                     f"bytes={p.stat().st_size if p.exists() else 0}")
    scratch = NOTES / "scheduler" / "scratch" / "H-quant-002"
    for rel in ["round2_fetch_stdout.txt", "round2_backtest_stdout.txt",
                "round2_verify_stdout.txt"]:
        p = scratch / rel
        lines.append(f"  scratch/H-quant-002/{rel}: exists={p.exists()} "
                     f"bytes={p.stat().st_size if p.exists() else 0}")

    # 6. known mechanism
    known = (BOT.parent.parent / "known" / "KNOWN.md").read_text()
    needle = "| E-E2-turn-of-month | 月末月初持有 |"
    lines.append("")
    lines.append(f"known/KNOWN.md contains {needle!r}: {needle in known}")

    # 7. entry front matter unchanged
    txt = ENTRY.read_text()
    front = txt.split("---", 2)[1]
    lines.append("")
    lines.append(f"entry: {ENTRY.relative_to(BOT.parent.parent)}")
    for key in ("id", "date", "status", "evidence", "result", "window"):
        m = re.search(rf"^{key}:\s*(.+)$", front, re.M)
        lines.append(f"  {key}: {m.group(1).strip() if m else 'MISSING'}")

    text = "\n".join(lines)
    print(text)
    (HERE / "_cache" / "verify_stdout.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
