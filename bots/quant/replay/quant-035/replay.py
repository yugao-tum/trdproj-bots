#!/usr/bin/env python3
"""quant-035 replay: delta-neutral funding carry on SOL/XRP/ADA/AVAX/HYPE.

Development window is strictly 2022-01-01..2024-12-31 (HYPE starts at its
first available Hyperliquid date inside December 2024).  No 2025+ data is
downloaded, requested or read by this script.  Raw downloads are cached under
replay/quant-035/_cache/ (git-ignored); only small result files are written.

Run from the repository root:
    python3 bots/quant/replay/quant-035/replay.py

Requires Python 3.10+ and requests.  Binance monthly archives are public and
keyless; Hyperliquid's /info endpoint is public and keyless.
"""

from __future__ import annotations

import bisect
import csv
import datetime as dt
import io
import json
import math
import os
import statistics
import sys
import time
import zipfile
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
OUT = HERE
BASE = "https://data.binance.vision/data"
HL_INFO = "https://api.hyperliquid.xyz/info"

HOUR_MS = 3_600_000
DAY_MS = 86_400_000
START = dt.date(2022, 1, 1)
END = dt.date(2024, 12, 31)
START_MS = int(dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)
END_MS = int(dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc).timestamp() * 1000) - 1
MONTHS = [f"{y}-{m:02d}" for y in range(2022, 2025) for m in range(1, 13)]
BINANCE_SYMBOLS = ["SOLUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT"]
HYPE_COIN = "HYPE"
HYPE_SPOT = "@107"  # HYPE/USDC spot pair on Hyperliquid
HYPE_START_MS = int(dt.datetime(2024, 12, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)

FEE = 0.003  # 0.30% per leg-side
MAIN_LOOKBACK_DAYS = 14
MAIN_ENTRY_THR = 0.0
MAIN_EXIT_THR = 0.0
BINANCE_SLEEVE_NOTIONAL = 300.0
BINANCE_SLEEVE_BUDGET = 600.0
HYPE_NOTIONAL = 1200.0
HYPE_BUDGET = 2450.0
TOTAL_CAPITAL = 5000.0
VENUE_CAP = 2500.0
LOOKBACK_VARIANTS = [7, 14, 21, 28, 42]


# ---------------------------------------------------------------------------
# download / parse
# ---------------------------------------------------------------------------

def _download(url: str, path: Path, tries: int = 5) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(tries):
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(r.content)
            tmp.replace(path)
            return
        except Exception as exc:  # noqa: BLE001 - network retry
            last = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"download failed: {url}: {last}")


def _read_zip_rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
            rows = list(csv.reader(text))
    if rows and not rows[0][0].lstrip("\ufeff").lstrip("-").isdigit():
        rows = rows[1:]
    return [[c.lstrip("\ufeff") for c in row] for row in rows]


def _binance_url(symbol: str, kind: str, month: str) -> str:
    if kind == "fund":
        return f"{BASE}/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{month}.zip"
    prefix = {
        "spot": "spot/monthly/klines",
        "perp": "futures/um/monthly/klines",
        "mark": "futures/um/monthly/markPriceKlines",
    }[kind]
    return f"{BASE}/{prefix}/{symbol}/1h/{symbol}-1h-{month}.zip"


def _binance_cache(symbol: str, kind: str, month: str) -> Path:
    return CACHE / "binance" / symbol / f"{kind}-{month}.zip"


def load_binance(symbol: str) -> dict:
    jobs = [(kind, month) for kind in ("spot", "perp", "mark", "fund") for month in MONTHS]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(_download, _binance_url(symbol, kind, month), _binance_cache(symbol, kind, month)): (kind, month)
            for kind, month in jobs
        }
        for fut in as_completed(futures):
            fut.result()

    out = {"symbol": symbol, "venue": "Binance", "spot": [], "perp": [], "mark": [], "fund": []}
    for kind in ("spot", "perp", "mark"):
        rows = []
        for month in MONTHS:
            for row in _read_zip_rows(_binance_cache(symbol, kind, month)):
                ts = int(row[0])
                if ts < START_MS or ts > END_MS:
                    raise ValueError(f"{symbol} {kind} {month}: timestamp outside 2022-2024: {ts}")
                rows.append((ts, float(row[1]), float(row[2]), float(row[3]), float(row[4])))
        rows.sort()
        out[kind] = rows
    frows = []
    for month in MONTHS:
        for row in _read_zip_rows(_binance_cache(symbol, "fund", month)):
            ts = int(row[0])
            if ts < START_MS or ts > END_MS:
                raise ValueError(f"{symbol} funding {month}: timestamp outside 2022-2024: {ts}")
            frows.append((ts, float(row[2])))
    frows.sort()
    out["fund"] = frows
    return out


def _hl_post(payload: dict, tries: int = 5):
    last = None
    for attempt in range(tries):
        try:
            r = requests.post(HL_INFO, json=payload, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - network retry
            last = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"Hyperliquid request failed: {payload}: {last}")


def _hl_candles(coin: str, interval: str, start_ms: int, end_ms: int) -> list[dict]:
    cache_name = f"{coin.replace('@', 'spot')}-{interval}-{start_ms}-{end_ms}.json"
    path = CACHE / "hyperliquid" / cache_name
    if path.exists():
        data = json.loads(path.read_text())
    else:
        data = _hl_post({
            "type": "candleSnapshot",
            "req": {"coin": coin, "interval": interval, "startTime": start_ms, "endTime": end_ms},
        })
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    for c in data:
        if int(c["t"]) < START_MS or int(c["t"]) > END_MS:
            raise ValueError(f"Hyperliquid {coin} candle outside 2022-2024: {c['t']}")
    return data


def _hl_funding_all(coin: str, start_ms: int, end_ms: int) -> list[dict]:
    path = CACHE / "hyperliquid" / f"{coin}-funding-{start_ms}-{end_ms}.json"
    if path.exists():
        data = json.loads(path.read_text())
    else:
        merged = {}
        cursor = start_ms
        while cursor <= end_ms:
            chunk_end = min(cursor + 400 * HOUR_MS - 1, end_ms)
            part = _hl_post({
                "type": "fundingHistory",
                "coin": coin,
                "startTime": cursor,
                "endTime": chunk_end,
            })
            for item in part:
                merged[int(item["time"])] = item
            if not part:
                cursor = chunk_end + 1
            else:
                cursor = max(int(item["time"]) for item in part) + 1
        data = [merged[k] for k in sorted(merged)]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    for item in data:
        if int(item["time"]) < START_MS or int(item["time"]) > END_MS:
            raise ValueError(f"Hyperliquid {coin} funding outside 2022-2024: {item['time']}")
    return data


def load_hype() -> dict:
    perp = _hl_candles(HYPE_COIN, "4h", HYPE_START_MS, END_MS)
    spot = _hl_candles(HYPE_SPOT, "4h", HYPE_START_MS, END_MS)
    fund = _hl_funding_all(HYPE_COIN, HYPE_START_MS, END_MS)
    out = {
        "symbol": "HYPE",
        "venue": "Hyperliquid",
        "spot": [(int(c["t"]), float(c["o"]), float(c["h"]), float(c["l"]), float(c["c"])) for c in spot],
        "perp": [(int(c["t"]), float(c["o"]), float(c["h"]), float(c["l"]), float(c["c"])) for c in perp],
        "mark": [(int(c["t"]), float(c["o"]), float(c["h"]), float(c["l"]), float(c["c"])) for c in perp],
        "fund": [(int(f["time"]), float(f["fundingRate"])) for f in fund],
        "bar_ms": 4 * HOUR_MS,
    }
    for key in ("spot", "perp", "mark", "fund"):
        out[key].sort()
    return out


# ---------------------------------------------------------------------------
# backtest
# ---------------------------------------------------------------------------

def _floor_hour(ts: int) -> int:
    return (ts // HOUR_MS) * HOUR_MS


def _rolling_mean(history: deque, ts: int, lookback_days: float, fixed_n: int | None = None):
    if fixed_n is not None:
        while len(history) > fixed_n:
            history.popleft()
        if len(history) < fixed_n:
            return None
        return statistics.fmean(rate for _, rate in history)
    if not history:
        return None
    cutoff = ts - lookback_days * DAY_MS
    oldest = history[0][0]
    # require a full lookback window before the first signal; do not trade on
    # the first few funding prints after a listing or at the start of the file
    if oldest > cutoff:
        return None
    while history and history[0][0] <= cutoff:
        history.popleft()
    if not history:
        return None
    return statistics.fmean(rate for _, rate in history)


def backtest(
    data: dict,
    *,
    lookback_days: float = MAIN_LOOKBACK_DAYS,
    entry_thr: float = MAIN_ENTRY_THR,
    exit_thr: float = MAIN_EXIT_THR,
    target_notional: float = 1200.0,
    budget: float = 2450.0,
    fee: float = FEE,
    signal_mode: str = "mean",
    fixed_n: int | None = None,
    z_window: int | None = None,
    z_thr: float | None = None,
    basis_filter: bool = False,
    bar_ms: int | None = None,
) -> dict:
    """One delta-neutral sleeve.  Decisions on funding timestamps, fills on
    the next available bar open (1h Binance, 4h HYPE in this replay)."""
    bar = bar_ms or data.get("bar_ms", HOUR_MS)
    spot_o = {r[0]: r[1] for r in data["spot"]}
    spot_c = {r[0]: r[4] for r in data["spot"]}
    perp_o = {r[0]: r[1] for r in data["perp"]}
    perp_c = {r[0]: r[4] for r in data["perp"]}
    mark_o = {r[0]: r[1] for r in data["mark"]}
    mark_ts = sorted(mark_o)
    common_open = sorted(set(spot_o) & set(perp_o))
    common_close = sorted(set(spot_c) & set(perp_c))
    if not common_open or not common_close:
        raise ValueError(f"{data['symbol']}: empty price data")

    def next_open(ts: int):
        i = bisect.bisect_left(common_open, ts)
        return common_open[i] if i < len(common_open) else None

    def last_close(ts: int):
        i = bisect.bisect_right(common_close, ts) - 1
        return common_close[i] if i >= 0 else None

    def mark_at(ts: int):
        i = bisect.bisect_right(mark_ts, ts) - 1
        if i >= 0:
            return mark_o[mark_ts[i]]
        return perp_o.get(ts)

    def basis_at(ts: int):
        ct = last_close(ts - 1)
        if ct is None:
            return 0.0
        return perp_c[ct] / spot_c[ct] - 1.0

    fmap = {}
    for ts, rate in data["fund"]:
        fmap[_floor_hour(ts)] = rate
    fund_times = sorted(fmap)
    if not fund_times:
        raise ValueError(f"{data['symbol']}: no funding data")

    day_end = {}
    d = START
    while d <= END:
        ts = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000) + DAY_MS - 1
        day_end[ts] = d
        d += dt.timedelta(days=1)

    events = set(fund_times)
    for ts in fund_times:
        nxt = next_open((ts // bar) * bar + bar)
        if nxt is not None:
            events.add(nxt)
    events.update(day_end)
    events = sorted(events)

    pos = None
    pending = None
    cash = 0.0
    fees_paid = 0.0
    trades = []
    daily = {}
    daily_capital = {}
    history = deque()
    z_hist = deque(maxlen=z_window or 0)

    def execute(ts: int):
        nonlocal pos, pending, cash, fees_paid
        if pending is None:
            return
        action, exec_ts = pending
        if exec_ts > ts:
            return
        fill_ts = next_open(exec_ts)
        if fill_ts is None:
            pending = None
            return
        if action == "enter" and pos is None:
            sp, pp = spot_o[fill_ts], perp_o[fill_ts]
            q = min(target_notional / sp, budget / ((sp + pp) * (1 + fee)))
            entry_fee = fee * q * (sp + pp)
            pos = {
                "entry_t": fill_ts,
                "q": q,
                "spot": sp,
                "perp": pp,
                "funding": 0.0,
                "entry_fee": entry_fee,
                "capital": q * (sp + pp) + entry_fee,
            }
            cash -= entry_fee
            fees_paid += entry_fee
            trades.append({
                "event_id": f"q035-{data['symbol']}-{fill_ts}",
                "side": "long_spot_short_perp",
                "entry_time": fill_ts,
                "exit_time": None,
                "entry_spot": sp,
                "entry_perp": pp,
                "exit_spot": None,
                "exit_perp": None,
                "qty": q,
                "notional": q * sp,
                "capital": pos["capital"],
                "funding": 0.0,
                "fees": entry_fee,
                "pnl": None,
                "exit_reason": None,
            })
        elif action == "exit" and pos is not None:
            sp, pp = spot_o[fill_ts], perp_o[fill_ts]
            exit_fee = fee * pos["q"] * (sp + pp)
            gross = pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp))
            cash += gross + pos["funding"] - exit_fee
            fees_paid += exit_fee
            trade = trades[-1]
            trade.update({
                "exit_time": fill_ts,
                "exit_spot": sp,
                "exit_perp": pp,
                "funding": pos["funding"],
                "fees": trade["fees"] + exit_fee,
                "pnl": gross + pos["funding"] - pos["entry_fee"] - exit_fee,
                "exit_reason": "signal",
            })
            pos = None
        pending = None

    for ts in events:
        execute(ts)

        if ts in fmap:
            if pos is not None and pos["entry_t"] < ts:
                mk = mark_at(ts)
                if mk is not None:
                    pos["funding"] += pos["q"] * mk * fmap[ts]
            rate = fmap[ts]
            history.append((ts, rate))
            mean = _rolling_mean(history, ts, lookback_days, fixed_n)
            z_hist.append(rate)
            z = None
            if z_window and len(z_hist) == z_window:
                xs = list(z_hist)
                sd = statistics.pstdev(xs)
                z = (xs[-1] - statistics.fmean(xs)) / sd if sd > 0 else 0.0
            allow_entry = True
            if basis_filter and basis_at(ts) <= 0:
                allow_entry = False

            if signal_mode == "current":
                want_enter = rate > entry_thr
                want_exit = rate < exit_thr
            elif signal_mode == "zscore":
                want_enter = z is not None and z > (z_thr if z_thr is not None else 0.5) and rate > 0
                want_exit = z is not None and (z <= (z_thr if z_thr is not None else 0.5) or rate <= 0)
            else:
                want_enter = mean is not None and mean > entry_thr and allow_entry
                want_exit = mean is not None and mean < exit_thr
                if basis_filter and basis_at(ts) < 0:
                    want_exit = True

            if pos is None and pending is None and want_enter:
                pending = ("enter", (ts // bar) * bar + bar)
            elif pos is not None and pending is None and want_exit:
                pending = ("exit", (ts // bar) * bar + bar)

        if ts in day_end:
            d = day_end[ts]
            val = cash
            cap = 0.0
            if pos is not None:
                ct = last_close(ts)
                if ct is not None:
                    sp, pp = spot_c[ct], perp_c[ct]
                    val += pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp)) + pos["funding"]
                    cap = pos["capital"]
            daily[d] = val
            daily_capital[d] = cap

    if pos is not None:
        ct = common_close[-1]
        sp, pp = spot_c[ct], perp_c[ct]
        exit_fee = fee * pos["q"] * (sp + pp)
        gross = pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp))
        cash += gross + pos["funding"] - exit_fee
        fees_paid += exit_fee
        trade = trades[-1]
        trade.update({
            "exit_time": ct,
            "exit_spot": sp,
            "exit_perp": pp,
            "funding": pos["funding"],
            "fees": trade["fees"] + exit_fee,
            "pnl": gross + pos["funding"] - pos["entry_fee"] - exit_fee,
            "exit_reason": "window_end",
        })
        pos = None
        daily[END] = cash
        daily_capital[END] = 0.0

    # ensure the daily series starts at START and carries the final cash
    days = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]
    series = []
    last = 0.0
    for day in days:
        last = daily.get(day, last)
        series.append((day, last, daily_capital.get(day, 0.0)))

    equity = [(day, TOTAL_CAPITAL + pnl) for day, pnl, _ in series]
    peak = equity[0][1]
    max_dd = 0.0
    for _, value in equity:
        peak = max(peak, value)
        max_dd = max(max_dd, (peak - value) / peak)
    years = len(days) / 365.25
    contribution = cash / TOTAL_CAPITAL / years * 100.0
    max_cap = max(cap for _, _, cap in series)
    return {
        "symbol": data["symbol"],
        "venue": data["venue"],
        "net": cash,
        "contribution": contribution,
        "max_dd": max_dd * 100.0,
        "episodes": len(trades),
        "fees": fees_paid,
        "max_capital": max_cap,
        "daily": series,
        "trades": trades,
        "years": years,
    }


def run_portfolio(
    data_by_symbol: dict,
    *,
    lookback_days: float,
    entry_thr: float,
    exit_thr: float,
    target_notional: float,
    budget: float,
    bar_ms: int = HOUR_MS,
) -> dict:
    """One Binance slot: choose the eligible coin with the highest 14-day mean;
    hold until its mean turns negative.  Used only as a diagnostic variant."""
    coins = {}
    for symbol, data in data_by_symbol.items():
        fmap = {_floor_hour(t): r for t, r in data["fund"]}
        times = sorted(fmap)
        hist = deque()
        sig = []
        for t in times:
            hist.append((t, fmap[t]))
            while hist and hist[0][0] <= t - lookback_days * DAY_MS:
                hist.popleft()
            sig.append((t, statistics.fmean(r for _, r in hist) if hist else None))
        coins[symbol] = {
            "data": data,
            "fmap": fmap,
            "sig": sig,
            "sig_t": [x[0] for x in sig],
            "spot_o": {r[0]: r[1] for r in data["spot"]},
            "spot_c": {r[0]: r[4] for r in data["spot"]},
            "perp_o": {r[0]: r[1] for r in data["perp"]},
            "perp_c": {r[0]: r[4] for r in data["perp"]},
            "mark_o": {r[0]: r[1] for r in data["mark"]},
        }
    all_times = sorted(set(t for c in coins.values() for t, _ in c["sig"]))
    events = set(all_times)
    for t in all_times:
        events.add((t // bar_ms) * bar_ms + bar_ms)
    d = START
    while d <= END:
        events.add(int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000) + DAY_MS - 1)
        d += dt.timedelta(days=1)
    events = sorted(events)

    def sig_at(coin, ts):
        i = bisect.bisect_right(coin["sig_t"], ts) - 1
        return coin["sig"][i][1] if i >= 0 else None

    pos = None
    pending = None
    cash = 0.0
    fees = 0.0
    trades = []
    daily = {}
    for ts in events:
        if pending and pending[0] <= ts:
            action, symbol = pending[1], pending[2]
            fill = None
            c = coins[symbol]
            # next common open
            opens = sorted(set(c["spot_o"]) & set(c["perp_o"]))
            i = bisect.bisect_left(opens, pending[0])
            if i < len(opens):
                fill = opens[i]
            if fill is not None:
                sp, pp = c["spot_o"][fill], c["perp_o"][fill]
                if action == "enter" and pos is None:
                    q = min(target_notional / sp, budget / ((sp + pp) * (1 + FEE)))
                    f = FEE * q * (sp + pp)
                    pos = {"symbol": symbol, "entry_t": fill, "q": q, "spot": sp, "perp": pp, "funding": 0.0}
                    cash -= f
                    fees += f
                    trades.append({"symbol": symbol, "entry_time": fill, "exit_time": None,
                                   "entry_spot": sp, "entry_perp": pp, "qty": q,
                                   "funding": 0.0, "fees": f, "pnl": None})
                elif action == "exit" and pos and pos["symbol"] == symbol:
                    f = FEE * pos["q"] * (sp + pp)
                    pnl = pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp)) + pos["funding"] - f
                    cash += pnl
                    fees += f
                    trades[-1].update({"exit_time": fill, "exit_spot": sp, "exit_perp": pp,
                                       "funding": pos["funding"], "fees": trades[-1]["fees"] + f,
                                       "pnl": pnl})
                    pos = None
            pending = None
        if pos:
            c = coins[pos["symbol"]]
            if ts in c["fmap"] and pos["entry_t"] < ts:
                mk = c["mark_o"].get(ts)
                if mk:
                    pos["funding"] += pos["q"] * mk * c["fmap"][ts]
        if ts in all_times:
            if pos is None and not pending:
                best = None
                for symbol, c in coins.items():
                    m = sig_at(c, ts)
                    if m is not None and m > entry_thr and (best is None or m > best[1]):
                        best = (symbol, m)
                if best:
                    pending = ((ts // bar_ms) * bar_ms + bar_ms, "enter", best[0])
            elif pos is not None and not pending:
                m = sig_at(coins[pos["symbol"]], ts)
                if m is not None and m < exit_thr:
                    pending = ((ts // bar_ms) * bar_ms + bar_ms, "exit", pos["symbol"])
        day = dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).date()
        if ts == int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp() * 1000) + DAY_MS - 1:
            val = cash
            if pos:
                c = coins[pos["symbol"]]
                closes = sorted(set(c["spot_c"]) & set(c["perp_c"]))
                i = bisect.bisect_right(closes, ts) - 1
                if i >= 0:
                    ct = closes[i]
                    sp, pp = c["spot_c"][ct], c["perp_c"][ct]
                    val += pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp)) + pos["funding"]
            daily[day] = val
    if pos:
        c = coins[pos["symbol"]]
        closes = sorted(set(c["spot_c"]) & set(c["perp_c"]))
        ct = closes[-1]
        sp, pp = c["spot_c"][ct], c["perp_c"][ct]
        f = FEE * pos["q"] * (sp + pp)
        pnl = pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp)) + pos["funding"] - f
        cash += pnl
        fees += f
        trades[-1].update({"exit_time": ct, "exit_spot": sp, "exit_perp": pp,
                           "funding": pos["funding"], "fees": trades[-1]["fees"] + f,
                           "pnl": pnl})
        daily[END] = cash
    days = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]
    series = []
    last = 0.0
    for day in days:
        last = daily.get(day, last)
        series.append((day, last))
    equity = [TOTAL_CAPITAL + pnl for _, pnl in series]
    peak = equity[0]
    mdd = 0.0
    for v in equity:
        peak = max(peak, v)
        mdd = max(mdd, (peak - v) / peak)
    years = len(days) / 365.25
    return {
        "net": cash,
        "contribution": cash / TOTAL_CAPITAL / years * 100,
        "max_dd": mdd * 100,
        "episodes": len(trades),
        "fees": fees,
        "trades": trades,
        "daily": [(d, p, 0.0) for d, p in series],
    }


def combine(sleeves: list[dict], label: str) -> dict:
    days = [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]
    pnl_by_day = defaultdict(float)
    cap_by_day = defaultdict(float)
    for sleeve in sleeves:
        for day, pnl, cap in sleeve["daily"]:
            pnl_by_day[day] += pnl
            cap_by_day[day] += cap
    equity = [TOTAL_CAPITAL + pnl_by_day[d] for d in days]
    peak = equity[0]
    mdd = 0.0
    for v in equity:
        peak = max(peak, v)
        mdd = max(mdd, (peak - v) / peak)
    net = sum(s["net"] for s in sleeves)
    years = len(days) / 365.25
    entries = []
    for sleeve in sleeves:
        for trade in sleeve["trades"]:
            if trade.get("entry_time") is not None:
                entries.append(trade["entry_time"])
    return {
        "label": label,
        "net": net,
        "contribution": net / TOTAL_CAPITAL / years * 100,
        "max_dd": mdd * 100,
        "episodes": sum(s["episodes"] for s in sleeves),
        "unique_entry_times": len(set(entries)),
        "unique_entry_days": len(set(dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).date() for t in entries)),
        "fees": sum(s["fees"] for s in sleeves),
        "max_capital": max(cap_by_day.values()) if cap_by_day else 0.0,
        "daily": [(d, pnl_by_day[d], cap_by_day[d]) for d in days],
        "trades": [t for s in sleeves for t in s["trades"]],
        "years": years,
    }


def beta_to_spot(basket: dict, data_by_symbol: dict) -> float:
    """Daily beta of the basket PnL to an equal-weight spot basket."""
    spot_series = {}
    for symbol, data in data_by_symbol.items():
        closes = {r[0]: r[4] for r in data["spot"]}
        days = {}
        for day in [START + dt.timedelta(days=i) for i in range((END - START).days + 1)]:
            ts = int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp() * 1000) + DAY_MS - 1
            keys = [k for k in closes if k <= ts]
            if keys:
                days[day] = closes[max(keys)]
        spot_series[symbol] = days
    strategy = {d: pnl for d, pnl, _ in basket["daily"]}
    xs, ys = [], []
    prev_s = prev_b = None
    for day in sorted(strategy):
        if day not in spot_series[BINANCE_SYMBOLS[0]]:
            continue
        vals = [spot_series[s].get(day) for s in BINANCE_SYMBOLS]
        if any(v is None for v in vals):
            continue
        b = sum(vals) / len(vals)
        s = strategy[day]
        if prev_s is not None and prev_b:
            xs.append(b / prev_b - 1.0)
            ys.append((s - prev_s) / TOTAL_CAPITAL)
        prev_s, prev_b = s, b
    if len(xs) < 30:
        return float("nan")
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    var = sum((x - mx) ** 2 for x in xs)
    return cov / var if var else float("nan")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    print("loading Binance 2022-2024 monthly archives ...", flush=True)
    binance = {s: load_binance(s) for s in BINANCE_SYMBOLS}
    print("loading Hyperliquid HYPE December 2024 ...", flush=True)
    hype = load_hype()

    print("running main basket ...", flush=True)
    binance_sleeves = [
        backtest(binance[s], lookback_days=MAIN_LOOKBACK_DAYS, entry_thr=MAIN_ENTRY_THR,
                 exit_thr=MAIN_EXIT_THR, target_notional=BINANCE_SLEEVE_NOTIONAL,
                 budget=BINANCE_SLEEVE_BUDGET)
        for s in BINANCE_SYMBOLS
    ]
    hype_sleeve = backtest(hype, lookback_days=MAIN_LOOKBACK_DAYS, entry_thr=MAIN_ENTRY_THR,
                           exit_thr=MAIN_EXIT_THR, target_notional=HYPE_NOTIONAL,
                           budget=HYPE_BUDGET, bar_ms=4 * HOUR_MS)
    main_basket = combine(binance_sleeves + [hype_sleeve], "main_basket")
    main_basket["beta"] = beta_to_spot(main_basket, binance)

    # venue capital check
    binance_cap = 0.0
    hype_cap = 0.0
    for day, _, cap in main_basket["daily"]:
        b = sum(s["daily"][[x[0] for x in s["daily"]].index(day)][2] for s in binance_sleeves)
        h = [x for x in hype_sleeve["daily"] if x[0] == day]
        binance_cap = max(binance_cap, b)
        hype_cap = max(hype_cap, h[0][2] if h else 0.0)
    main_basket["max_capital_binance"] = binance_cap
    main_basket["max_capital_hype"] = hype_cap

    variants = []

    def add_variant(vid, family, symbol, venue, lookback, entry_thr, exit_thr, notional,
                    budget, result, notes=""):
        variants.append({
            "id": vid,
            "family": family,
            "symbol": symbol,
            "venue": venue,
            "lookback_days": lookback,
            "entry_thr": entry_thr,
            "exit_thr": exit_thr,
            "notional": notional,
            "budget": budget,
            "net": round(result["net"], 4),
            "contribution": round(result["contribution"], 4),
            "max_dd": round(result["max_dd"], 4),
            "episodes": result["episodes"],
            "fees": round(result["fees"], 4),
            "notes": notes,
        })

    add_variant("main_basket", "main", "SOL,XRP,ADA,AVAX,HYPE", "Binance+Hyperliquid",
                MAIN_LOOKBACK_DAYS, MAIN_ENTRY_THR, MAIN_EXIT_THR, "300x4+1200", "600x4+2450",
                main_basket, "4x300 Binance sleeves + 1200 HYPE; 14-day mean >0")

    # per-coin lookback and threshold variants (1,200 notional each)
    for symbol, data in list(binance.items()) + [("HYPE", hype)]:
        venue = data["venue"]
        bar = 4 * HOUR_MS if symbol == "HYPE" else HOUR_MS
        for lookback in LOOKBACK_VARIANTS:
            r = backtest(data, lookback_days=lookback, entry_thr=0.0, exit_thr=0.0,
                         target_notional=1200.0, budget=2450.0, bar_ms=bar)
            add_variant(f"coin_{symbol}_{lookback}d", "per_coin", symbol, venue,
                        lookback, 0.0, 0.0, 1200.0, 2450.0, r, "per-coin sleeve")
        r = backtest(data, lookback_days=14, entry_thr=0.00005, exit_thr=0.0,
                     target_notional=1200.0, budget=2450.0, bar_ms=bar)
        add_variant(f"coin_{symbol}_14d_5bp", "per_coin", symbol, venue,
                    14, 0.00005, 0.0, 1200.0, 2450.0, r, "entry only above 5bp/8h-equivalent")
        r = backtest(data, lookback_days=21, entry_thr=0.00005, exit_thr=0.0,
                     target_notional=1200.0, budget=2450.0, bar_ms=bar)
        add_variant(f"coin_{symbol}_21d_5bp", "per_coin", symbol, venue,
                    21, 0.00005, 0.0, 1200.0, 2450.0, r, "21-day mean >5bp")
        r = backtest(data, lookback_days=21, entry_thr=0.0001, exit_thr=0.0,
                     target_notional=1200.0, budget=2450.0, bar_ms=bar)
        add_variant(f"coin_{symbol}_21d_10bp", "per_coin", symbol, venue,
                    21, 0.0001, 0.0, 1200.0, 2450.0, r, "21-day mean >10bp")
        r = backtest(data, lookback_days=14, entry_thr=0.0, exit_thr=0.0,
                     target_notional=1200.0, budget=2450.0, signal_mode="current", bar_ms=bar)
        add_variant(f"coin_{symbol}_always", "per_coin", symbol, venue,
                    0, 0.0, 0.0, 1200.0, 2450.0, r, "hold while current funding >0")

    # basket lookback variants
    for lookback in (7, 21, 28):
        sleeves = [
            backtest(binance[s], lookback_days=lookback, entry_thr=0.0, exit_thr=0.0,
                     target_notional=BINANCE_SLEEVE_NOTIONAL, budget=BINANCE_SLEEVE_BUDGET)
            for s in BINANCE_SYMBOLS
        ]
        sleeves.append(backtest(hype, lookback_days=lookback, entry_thr=0.0, exit_thr=0.0,
                                target_notional=HYPE_NOTIONAL, budget=HYPE_BUDGET, bar_ms=4 * HOUR_MS))
        r = combine(sleeves, f"basket_{lookback}d")
        add_variant(f"basket_{lookback}d", "basket", "SOL,XRP,ADA,AVAX,HYPE", "Binance+Hyperliquid",
                    lookback, 0.0, 0.0, "300x4+1200", "600x4+2450", r, "same basket, other lookback")

    # one-slot selection variants
    for lookback in (14, 21, 42, 63, 189):
        r = run_portfolio(binance, lookback_days=lookback, entry_thr=0.0, exit_thr=0.0,
                          target_notional=1200.0, budget=2450.0)
        add_variant(f"one_slot_{lookback}d", "one_slot", "SOL,XRP,ADA,AVAX", "Binance",
                    lookback, 0.0, 0.0, 1200.0, 2450.0, r, "one coin at a time, highest mean")

    # HYPE extra lookbacks (hourly funding, 4h bars)
    for lookback in (1, 2, 3, 5, 7, 21, 28, 42):
        r = backtest(hype, lookback_days=lookback, entry_thr=0.0, exit_thr=0.0,
                     target_notional=1200.0, budget=2450.0, bar_ms=4 * HOUR_MS)
        add_variant(f"HYPE_{lookback}d", "hype_extra", "HYPE", "Hyperliquid",
                    lookback, 0.0, 0.0, 1200.0, 2450.0, r, "short-history sensitivity")
    # HYPE fixed event-count variants, matching the exploratory runs
    for n in (42, 63, 84, 168, 336, 504):
        for thr in (0.0, 0.00005):
            r = backtest(hype, lookback_days=n / 24.0, entry_thr=thr, exit_thr=0.0,
                         target_notional=1200.0, budget=2450.0, fixed_n=n,
                         bar_ms=4 * HOUR_MS)
            add_variant(f"HYPE_N{n}_{'5bp' if thr else '0'}", "hype_events", "HYPE",
                        "Hyperliquid", n / 24.0, thr, 0.0, 1200.0, 2450.0, r,
                        f"fixed {n} hourly funding observations")

    # z-score diagnostic on SOL
    r = backtest(binance["SOLUSDT"], lookback_days=30, entry_thr=0.0, exit_thr=0.0,
                 target_notional=1200.0, budget=2450.0, signal_mode="zscore",
                 z_window=30, z_thr=0.5)
    add_variant("SOL_z30_0.5", "zscore", "SOLUSDT", "Binance", 0, 0.0, 0.0,
                1200.0, 2450.0, r, "composer-003-style 30-event z>0.5")
    r = backtest(binance["SOLUSDT"], lookback_days=30, entry_thr=0.0, exit_thr=0.0,
                 target_notional=1200.0, budget=2450.0, signal_mode="zscore",
                 z_window=30, z_thr=1.0)
    add_variant("SOL_z30_1.0", "zscore", "SOLUSDT", "Binance", 0, 0.0, 0.0,
                1200.0, 2450.0, r, "z>1.0")

    # basis-filter diagnostic on SOL
    r = backtest(binance["SOLUSDT"], lookback_days=14, entry_thr=0.0, exit_thr=0.0,
                 target_notional=1200.0, budget=2450.0, basis_filter=True)
    add_variant("SOL_14d_basis", "basis", "SOLUSDT", "Binance", 14, 0.0, 0.0,
                1200.0, 2450.0, r, "require perp premium >0 at entry")
    for lookback, thr in ((63, 0.0), (63, 0.00005), (63, 0.0001), (189, 0.0), (189, 0.00005)):
        r = backtest(binance["SOLUSDT"], lookback_days=lookback, entry_thr=thr, exit_thr=0.0,
                     target_notional=1200.0, budget=2450.0)
        add_variant(f"SOL_{lookback}d_{'0' if thr == 0 else str(int(thr * 1e5)) + 'bp'}",
                    "sol_extra", "SOLUSDT", "Binance", lookback, thr, 0.0, 1200.0, 2450.0, r,
                    "SOL-only long-lookback sensitivity")
    # long-lookback per-coin variants for the other three Binance coins
    for symbol in ("XRPUSDT", "ADAUSDT", "AVAXUSDT"):
        for lookback in (63, 189):
            for thr in (0.0, 0.00005):
                r = backtest(binance[symbol], lookback_days=lookback, entry_thr=thr, exit_thr=0.0,
                             target_notional=1200.0, budget=2450.0)
                add_variant(f"coin_{symbol}_{lookback}d_{'0' if thr == 0 else '5bp'}",
                            "per_coin_long", symbol, "Binance", lookback, thr, 0.0,
                            1200.0, 2450.0, r, "long-lookback per-coin sensitivity")

    # write result files
    def json_safe(obj):
        if isinstance(obj, dict):
            return {k: json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [json_safe(v) for v in obj]
        if isinstance(obj, dt.date):
            return obj.isoformat()
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj

    results = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window": "2022-01-01..2024-12-31",
        "main": {k: v for k, v in main_basket.items() if k not in ("daily", "trades")},
        "sleeves": [
            {k: v for k, v in s.items() if k not in ("daily", "trades")}
            for s in binance_sleeves + [hype_sleeve]
        ],
        "variants": variants,
    }
    (OUT / "results.json").write_text(json.dumps(json_safe(results), indent=2, ensure_ascii=False))

    with (OUT / "trades.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "sleeve", "event_id", "side", "entry_time_utc", "exit_time_utc",
            "entry_spot", "entry_perp", "exit_spot", "exit_perp", "qty",
            "notional_usdt", "capital_usdt", "funding_usdt", "fees_usdt",
            "pnl_usdt", "hold_days", "exit_reason",
        ])
        for sleeve in binance_sleeves + [hype_sleeve]:
            for t in sleeve["trades"]:
                et = dt.datetime.fromtimestamp(t["entry_time"] / 1000, dt.timezone.utc)
                xt = dt.datetime.fromtimestamp(t["exit_time"] / 1000, dt.timezone.utc)
                writer.writerow([
                    sleeve["symbol"], t["event_id"], t["side"],
                    et.strftime("%Y-%m-%dT%H:%M:%SZ"), xt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    f"{t['entry_spot']:.8f}", f"{t['entry_perp']:.8f}",
                    f"{t['exit_spot']:.8f}", f"{t['exit_perp']:.8f}",
                    f"{t['qty']:.8f}", f"{t['notional']:.4f}", f"{t['capital']:.4f}",
                    f"{t['funding']:.6f}", f"{t['fees']:.6f}",
                    f"{t['pnl']:.6f}",
                    f"{(t['exit_time'] - t['entry_time']) / DAY_MS:.4f}",
                    t["exit_reason"],
                ])

    with (OUT / "equity.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "equity_5k", "pnl_cum", "capital_open", "equity_incl_unrealised"])
        for day, pnl, cap in main_basket["daily"]:
            writer.writerow([day.isoformat(), f"{TOTAL_CAPITAL + pnl:.4f}", f"{pnl:.4f}",
                             f"{cap:.4f}", f"{TOTAL_CAPITAL + pnl:.4f}"])

    with (OUT / "variants.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(variants[0].keys()))
        writer.writeheader()
        writer.writerows(variants)

    print(json.dumps(json_safe({
        "main": {k: v for k, v in main_basket.items() if k not in ("daily", "trades")},
        "variants": len(variants),
    }), indent=2, ensure_ascii=False))
    print(f"wrote {OUT / 'results.json'}, {OUT / 'trades.csv'}, {OUT / 'equity.csv'}, {OUT / 'variants.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
