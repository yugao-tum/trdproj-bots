#!/usr/bin/env python3
"""Deterministic, idempotent paper recorder for quant-035.

Rule: delta-neutral spot-long / 1x perp-short funding carry on
SOL/XRP/ADA/AVAX (Binance) and HYPE (Hyperliquid).  Entry when the 14-day
mean funding rate is > 0; exit when it is < 0.  Decisions are made at each
funding timestamp; fills are paper-filled at the next 1h bar open.

Run hourly from the repository root:
    python3 bots/quant/forward/quant-035/record.py

Dry run (pretend the start is now; prints rows, writes nothing):
    FORWARD_DRY_RUN=1 python3 bots/quant/forward/quant-035/record.py

Only public, keyless endpoints are used.  No orders, wallets or accounts.
Network errors exit 0 so the operator can retry; nothing is fabricated.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import sys
import time
import zipfile
from bisect import bisect_left, bisect_right
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "ledger.csv"
STATE = HERE / "state.json"
HEADER = ["time_utc", "event_id", "market", "action", "side", "price",
          "price_source", "size", "fee", "pnl", "note"]

UTC = dt.timezone.utc
HOUR_MS = 3_600_000
DAY_MS = 86_400_000
LOOKBACK_DAYS = 14
FEE = 0.003
START = dt.datetime(2026, 10, 22, 0, 0, 0, tzinfo=UTC)
END = dt.datetime(2026, 11, 5, 0, 0, 0, tzinfo=UTC)
WARMUP_START = START - dt.timedelta(days=LOOKBACK_DAYS + 1)

BINANCE = {
    "SOLUSDT": {"target": 300.0, "budget": 600.0},
    "XRPUSDT": {"target": 300.0, "budget": 600.0},
    "ADAUSDT": {"target": 300.0, "budget": 600.0},
    "AVAXUSDT": {"target": 300.0, "budget": 600.0},
}
HYPE = {"target": 1200.0, "budget": 2450.0}
HYPE_SPOT = "@107"


class NetworkError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# small HTTP helpers
# ---------------------------------------------------------------------------

def _get(url: str, params: dict | None = None, tries: int = 3):
    last = None
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r
        except Exception as exc:  # noqa: BLE001 - network retry
            last = exc
            time.sleep(0.5 + attempt)
    raise NetworkError(f"GET {url}: {last}")


def _post(payload: dict, tries: int = 3):
    last = None
    for attempt in range(tries):
        try:
            r = requests.post("https://api.hyperliquid.xyz/info", json=payload, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - network retry
            last = exc
            time.sleep(0.5 + attempt)
    raise NetworkError(f"Hyperliquid {payload}: {last}")


def _ms(value: dt.datetime) -> int:
    return int(value.timestamp() * 1000)


def _iso(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Binance
# ---------------------------------------------------------------------------

def binance_spot_klines(symbol: str, start_ms: int, end_ms: int) -> list[tuple[int, float, float]]:
    out = []
    cursor = start_ms
    while cursor <= end_ms:
        r = _get("https://data-api.binance.vision/api/v3/klines", {
            "symbol": symbol, "interval": "1h", "startTime": cursor,
            "endTime": end_ms, "limit": 1000,
        })
        rows = r.json()
        if not rows:
            break
        for row in rows:
            out.append((int(row[0]), float(row[1]), float(row[4])))
        cursor = int(rows[-1][0]) + HOUR_MS
        if len(rows) < 1000:
            break
    return out


def binance_futures_klines(symbol: str, start_ms: int, end_ms: int) -> list[tuple[int, float, float]]:
    try:
        out = []
        cursor = start_ms
        while cursor <= end_ms:
            r = _get("https://fapi.binance.com/fapi/v1/klines", {
                "symbol": symbol, "interval": "1h", "startTime": cursor,
                "endTime": end_ms, "limit": 1000,
            })
            rows = r.json()
            if not rows:
                break
            for row in rows:
                out.append((int(row[0]), float(row[1]), float(row[4])))
            cursor = int(rows[-1][0]) + HOUR_MS
            if len(rows) < 1000:
                break
        return out
    except NetworkError:
        return _bdv_daily_klines(symbol, "klines", start_ms, end_ms)


def _bdv_daily_klines(symbol: str, kind: str, start_ms: int, end_ms: int) -> list[tuple[int, float, float]]:
    out = []
    day = dt.datetime.fromtimestamp(start_ms / 1000, UTC).date()
    last = dt.datetime.fromtimestamp(end_ms / 1000, UTC).date()
    while day <= last:
        url = (f"https://data.binance.vision/data/futures/um/daily/{kind}/"
               f"{symbol}/1h/{symbol}-1h-{day.isoformat()}.zip")
        try:
            r = _get(url)
            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                name = zf.namelist()[0]
                with zf.open(name) as fh:
                    text = io.TextIOWrapper(fh, encoding="utf-8", newline="")
                    rows = list(csv.reader(text))
            if rows and not rows[0][0].lstrip("\ufeff").lstrip("-").isdigit():
                rows = rows[1:]
            for row in rows:
                ts = int(row[0].lstrip("\ufeff"))
                if start_ms <= ts <= end_ms:
                    out.append((ts, float(row[1]), float(row[4])))
        except NetworkError:
            pass
        day += dt.timedelta(days=1)
    return out


def binance_futures_funding(symbol: str, start_ms: int, end_ms: int) -> list[tuple[int, float]]:
    out = []
    cursor = start_ms
    while cursor <= end_ms:
        r = _get("https://fapi.binance.com/fapi/v1/fundingRate", {
            "symbol": symbol, "startTime": cursor, "endTime": end_ms, "limit": 1000,
        })
        rows = r.json()
        if not rows:
            break
        for row in rows:
            out.append((int(row["fundingTime"]), float(row["fundingRate"])))
        cursor = int(rows[-1]["fundingTime"]) + 1
        if len(rows) < 1000:
            break
    return out


def binance_mark_klines(symbol: str, start_ms: int, end_ms: int) -> list[tuple[int, float]]:
    try:
        out = []
        cursor = start_ms
        while cursor <= end_ms:
            r = _get("https://fapi.binance.com/fapi/v1/markPriceKlines", {
                "symbol": symbol, "interval": "1h", "startTime": cursor,
                "endTime": end_ms, "limit": 1000,
            })
            rows = r.json()
            if not rows:
                break
            for row in rows:
                out.append((int(row[0]), float(row[1])))
            cursor = int(rows[-1][0]) + HOUR_MS
            if len(rows) < 1000:
                break
        return out
    except NetworkError:
        return [(ts, price) for ts, price, _ in _bdv_daily_klines(symbol, "markPriceKlines", start_ms, end_ms)]


def binance_trade(symbol: str, market: str, start_ms: int):
    """First public trade in [start_ms, start_ms+120s]; else None."""
    try:
        if market == "spot":
            r = _get("https://data-api.binance.vision/api/v3/aggTrades", {
                "symbol": symbol, "startTime": start_ms, "limit": 1,
            })
        else:
            r = _get("https://fapi.binance.com/fapi/v1/aggTrades", {
                "symbol": symbol, "startTime": start_ms, "limit": 1,
            })
        rows = r.json()
        if rows and int(rows[0]["T"]) <= start_ms + 120_000:
            row = rows[0]
            return float(row["p"]), f"trade:{row['a']}:{row['T']}", int(row["T"])
    except NetworkError:
        pass
    return None


# ---------------------------------------------------------------------------
# Hyperliquid
# ---------------------------------------------------------------------------

def hl_funding(coin: str, start_ms: int, end_ms: int) -> list[tuple[int, float]]:
    merged = {}
    cursor = start_ms
    while cursor <= end_ms:
        chunk_end = min(cursor + 400 * HOUR_MS - 1, end_ms)
        part = _post({"type": "fundingHistory", "coin": coin,
                      "startTime": cursor, "endTime": chunk_end})
        for item in part:
            merged[int(item["time"])] = float(item["fundingRate"])
        if not part:
            cursor = chunk_end + 1
        else:
            cursor = max(int(item["time"]) for item in part) + 1
        if len(part) < 400:
            break
    return sorted(merged.items())


def hl_candles(coin: str, start_ms: int, end_ms: int) -> list[tuple[int, float, float]]:
    data = _post({"type": "candleSnapshot", "req": {
        "coin": coin, "interval": "1h", "startTime": start_ms, "endTime": end_ms,
    }})
    return [(int(c["t"]), float(c["o"]), float(c["c"])) for c in data]


def hl_trade(coin: str, start_ms: int):
    """Recent-trades endpoint is a rolling window, not a historical query.
    Accept only a trade in [start_ms, start_ms+120s]; otherwise None."""
    try:
        rows = _post({"type": "recentTrades", "coin": coin})
    except NetworkError:
        return None
    for row in rows:
        t = int(row["time"])
        if t >= start_ms:
            if t <= start_ms + 120_000:
                return float(row["px"]), f"trade:{row['tid']}:{t}", t
            return None
    return None


# ---------------------------------------------------------------------------
# data assembly and signal simulation
# ---------------------------------------------------------------------------

def load_symbol_data(symbol: str, start_ms: int, end_ms: int) -> dict | None:
    try:
        if symbol == "HYPE":
            spot = hl_candles(HYPE_SPOT, start_ms, end_ms)
            perp = hl_candles("HYPE", start_ms, end_ms)
            funding = hl_funding("HYPE", start_ms, end_ms)
            mark = [(t, o) for t, o, _ in perp]
            return {"symbol": symbol, "venue": "Hyperliquid", "spot": spot, "perp": perp,
                    "funding": funding, "mark": mark, "target": HYPE["target"],
                    "budget": HYPE["budget"], "spot_coin": HYPE_SPOT, "perp_coin": "HYPE"}
        spot = binance_spot_klines(symbol, start_ms, end_ms)
        perp = binance_futures_klines(symbol, start_ms, end_ms)
        funding = binance_futures_funding(symbol, start_ms, end_ms)
        mark = binance_mark_klines(symbol, start_ms, end_ms)
        if not spot or not perp or not funding:
            return None
        return {"symbol": symbol, "venue": "Binance", "spot": spot, "perp": perp,
                "funding": funding, "mark": mark, "target": BINANCE[symbol]["target"],
                "budget": BINANCE[symbol]["budget"], "spot_coin": symbol, "perp_coin": symbol}
    except NetworkError as exc:
        print(f"skip {symbol}: {exc}", flush=True)
        return None


def _next_hour(ms: int) -> int:
    return (ms // HOUR_MS) * HOUR_MS + HOUR_MS


def _price_at(rows: list[tuple[int, float, float]], ts: int):
    """First bar open at or after ts; returns (open_time, open)."""
    keys = [r[0] for r in rows]
    i = bisect_left(keys, ts)
    if i >= len(rows):
        return None
    return rows[i][0], rows[i][1]


def _mark_at(rows: list[tuple[int, float]], ts: int):
    keys = [r[0] for r in rows]
    i = bisect_right(keys, ts) - 1
    if i < 0:
        return None
    return rows[i][0], rows[i][1]


def _signal_series(funding: list[tuple[int, float]]) -> list[tuple[int, float | None]]:
    out = []
    hist = []
    for t, rate in sorted(funding):
        hist.append((t, rate))
        cutoff = t - LOOKBACK_DAYS * DAY_MS
        oldest = hist[0][0]
        while hist and hist[0][0] <= cutoff:
            hist.pop(0)
        valid = oldest <= cutoff and bool(hist)
        mean = sum(r for _, r in hist) / len(hist) if valid else None
        out.append((t, mean))
    return out


def simulate(data: dict, start_ms: int, end_ms: int, now_ms: int) -> list[dict]:
    """Recompute the expected ledger rows for [start_ms, min(end_ms, now_ms)]."""
    spot = sorted(data["spot"])
    perp = sorted(data["perp"])
    funding = sorted(data["funding"])
    mark = sorted(data["mark"])
    signals = dict(_signal_series(funding))
    funding_times = [t for t, _ in funding if start_ms <= t <= min(end_ms, now_ms - 120_000)]

    events = set(funding_times)
    for t in funding_times:
        events.add(_next_hour(t))
    window_end_ms = _ms(END)
    if window_end_ms <= now_ms:
        events.add(window_end_ms)
    events = sorted(t for t in events if t <= now_ms)

    pos = None
    pending = None
    rows = []

    def fill_prices(ts: int):
        sp = _price_at(spot, ts)
        pp = _price_at(perp, ts)
        if sp is None or pp is None:
            return None
        spot_ts, spot_px = sp
        perp_ts, perp_px = pp
        spot_src = f"kline_open:{spot_ts}"
        perp_src = f"kline_open:{perp_ts}"
        if data["venue"] == "Binance":
            st = binance_trade(data["spot_coin"], "spot", ts)
            pt = binance_trade(data["perp_coin"], "futures", ts)
            if st:
                spot_px, spot_src = st[0], st[1]
            if pt:
                perp_px, perp_src = pt[0], pt[1]
        else:
            st = hl_trade(data["spot_coin"], ts)
            pt = hl_trade(data["perp_coin"], ts)
            if st:
                spot_px, spot_src = st[0], st[1]
            if pt:
                perp_px, perp_src = pt[0], pt[1]
        return spot_px, perp_px, spot_src, perp_src

    for ts in events:
        if ts == _ms(END) and pos is not None:
            # force-close any position still open at the end of the forward window
            prices = fill_prices(ts)
            if prices:
                sp, pp, ssrc, psrc = prices
                gross = pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp))
                exit_fee = FEE * pos["q"] * (sp + pp)
                pnl = gross + pos["funding"] - pos["entry_fee"] - exit_fee
                rows.append({
                    "time_utc": _iso(ts),
                    "event_id": f"q035-{data['symbol']}-{pos['entry_t']}",
                    "market": f"{data['venue']}:{data['symbol']}",
                    "action": "平", "side": "对冲", "price": f"{sp:.8f}",
                    "price_source": ssrc,
                    "size": f"{pos['q']:.8f}", "fee": f"{exit_fee:.6f}", "pnl": f"{pnl:.6f}",
                    "note": (f"perp={pp:.8f};qty={pos['q']:.8f};entry={_iso(pos['entry_t'])};"
                             f"entry_fee={pos['entry_fee']:.6f};exit_fee={exit_fee:.6f};"
                             f"funding={pos['funding']:.6f};reason=window_end;perp_source={psrc}"),
                })
                pos = None
                pending = None
        if pending is not None and pending["exec"] <= ts:
            action = pending["action"]
            if action == "enter" and pos is None:
                prices = fill_prices(pending["exec"])
                if prices:
                    sp, pp, ssrc, psrc = prices
                    q = min(data["target"] / sp, data["budget"] / ((sp + pp) * (1 + FEE)))
                    fee = FEE * q * (sp + pp)
                    pos = {
                        "entry_t": pending["exec"], "q": q, "spot": sp, "perp": pp,
                        "entry_fee": fee, "funding": 0.0,
                        "spot_src": ssrc, "perp_src": psrc,
                    }
                    rows.append({
                        "time_utc": _iso(pending["exec"]),
                        "event_id": f"q035-{data['symbol']}-{pending['exec']}",
                        "market": f"{data['venue']}:{data['symbol']}",
                        "action": "开", "side": "对冲", "price": f"{sp:.8f}",
                        "price_source": ssrc,
                        "size": f"{q:.8f}", "fee": f"{fee:.6f}", "pnl": "0",
                        "note": (f"perp={pp:.8f};qty={q:.8f};notional={q * sp:.4f};"
                                 f"capital={q * (sp + pp) + fee:.4f};target={data['target']:.0f};"
                                 f"budget={data['budget']:.0f};perp_source={psrc}"),
                    })
            elif action == "exit" and pos is not None:
                prices = fill_prices(pending["exec"])
                if prices:
                    sp, pp, ssrc, psrc = prices
                    gross = pos["q"] * ((sp - pos["spot"]) + (pos["perp"] - pp))
                    exit_fee = FEE * pos["q"] * (sp + pp)
                    pnl = gross + pos["funding"] - pos["entry_fee"] - exit_fee
                    rows.append({
                        "time_utc": _iso(pending["exec"]),
                        "event_id": f"q035-{data['symbol']}-{pos['entry_t']}",
                        "market": f"{data['venue']}:{data['symbol']}",
                        "action": "平", "side": "对冲", "price": f"{sp:.8f}",
                        "price_source": ssrc,
                        "size": f"{pos['q']:.8f}", "fee": f"{exit_fee:.6f}", "pnl": f"{pnl:.6f}",
                        "note": (f"perp={pp:.8f};qty={pos['q']:.8f};entry={_iso(pos['entry_t'])};"
                                 f"entry_fee={pos['entry_fee']:.6f};exit_fee={exit_fee:.6f};"
                                 f"funding={pos['funding']:.6f};reason=signal;perp_source={psrc}"),
                    })
                    pos = None
            pending = None

        if ts in signals and pos is not None and pos["entry_t"] < ts:
            mk = _mark_at(mark, ts)
            rate = next(r for t, r in funding if t == ts)
            if mk:
                cash = pos["q"] * mk[1] * rate
                pos["funding"] += cash
                rows.append({
                    "time_utc": _iso(ts),
                    "event_id": f"q035-{data['symbol']}-{pos['entry_t']}-F{ts}",
                    "market": f"{data['venue']}:{data['symbol']}",
                    "action": "结算", "side": "空", "price": f"{mk[1]:.8f}",
                    "price_source": f"mark_open:{mk[0]}",
                    "size": f"{pos['q'] * mk[1]:.6f}", "fee": "0", "pnl": f"{cash:.6f}",
                    "note": (f"rate={rate:.12f};mark={mk[1]:.8f};qty={pos['q']:.8f};"
                             f"episode=q035-{data['symbol']}-{pos['entry_t']}"),
                })

        if ts in signals:
            mean = signals[ts]
            exec_ts = _next_hour(ts)
            if mean is not None and exec_ts < _ms(END):
                if pos is None and pending is None and mean > 0:
                    pending = {"action": "enter", "exec": exec_ts}
                elif pos is not None and pending is None and mean < 0:
                    pending = {"action": "exit", "exec": exec_ts}
    return rows


# ---------------------------------------------------------------------------
# ledger I/O
# ---------------------------------------------------------------------------

def read_ledger() -> list[dict]:
    if not LEDGER.exists():
        return []
    with LEDGER.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != HEADER:
            raise ValueError(f"ledger header mismatch: {reader.fieldnames}")
        return list(reader)


def append_rows(rows: list[dict]) -> int:
    if not rows:
        return 0
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in HEADER})
        fh.flush()
        os.fsync(fh.fileno())
    return len(rows)


def _same(a: dict, b: dict) -> bool:
    for key in ("price", "size", "fee", "pnl"):
        try:
            if abs(float(a[key]) - float(b[key])) > 1e-6:
                return False
        except (ValueError, KeyError):
            if str(a.get(key)) != str(b.get(key)):
                return False
    return True


def reconcile(expected: list[dict]) -> tuple[list[dict], list[dict]]:
    existing = read_ledger()
    by_key = {(r["time_utc"], r["event_id"], r["action"]): r for r in existing}
    correction_keys = {(r["note"].split(";")[0], r["event_id"]) for r in existing if r["action"] == "更正"}
    new_rows, corrections = [], []
    for row in expected:
        key = (row["time_utc"], row["event_id"], row["action"])
        if key not in by_key:
            new_rows.append(row)
        elif not _same(by_key[key], row):
            ckey = (f"corrects={row['time_utc']}|{row['action']}|{row['event_id']}", row["event_id"])
            if ckey not in correction_keys:
                corrections.append({
                    "time_utc": dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "event_id": row["event_id"],
                    "market": row["market"],
                    "action": "更正",
                    "side": row["side"],
                    "price": row["price"],
                    "price_source": row["price_source"],
                    "size": row["size"],
                    "fee": row["fee"],
                    "pnl": row["pnl"],
                    "note": (f"corrects={row['time_utc']}|{row['action']}|{row['event_id']};"
                             f"reason=recomputed;original_pnl={by_key[key].get('pnl', '')}"),
                })
                correction_keys.add(ckey)
    return new_rows, corrections


def _write_state(payload: dict) -> None:
    tmp = STATE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    tmp.replace(STATE)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    dry = os.environ.get("FORWARD_DRY_RUN") == "1"
    now = dt.datetime.now(UTC)
    if dry:
        effective_start = now - dt.timedelta(days=1)
        effective_end = now
    else:
        if now < START:
            print(f"before start ({START.isoformat()}); nothing written")
            return 0
        effective_start = START
        effective_end = min(now, END)

    fetch_start = effective_start - dt.timedelta(days=LOOKBACK_DAYS + 1)
    start_ms, end_ms = _ms(effective_start), _ms(effective_end)
    fetch_ms = _ms(fetch_start)

    expected = []
    for symbol in list(BINANCE) + ["HYPE"]:
        data = load_symbol_data(symbol, fetch_ms, end_ms)
        if data is None:
            continue
        try:
            rows = simulate(data, start_ms, end_ms, _ms(now))
        except Exception as exc:  # noqa: BLE001 - one bad symbol must not stop others
            print(f"skip {symbol}: simulation error: {exc}", flush=True)
            continue
        expected.extend(rows)
        print(f"{symbol}: {len(rows)} expected rows", flush=True)

    expected.sort(key=lambda r: (r["time_utc"], r["event_id"], r["action"]))

    if dry:
        print("DRY RUN: no files written")
        for row in expected:
            print(json.dumps(row, ensure_ascii=False))
        return 0

    if not LEDGER.exists():
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("w", encoding="utf-8", newline="") as fh:
            csv.DictWriter(fh, fieldnames=HEADER).writeheader()

    new_rows, corrections = reconcile(expected)
    n1 = append_rows(new_rows)
    n2 = append_rows(corrections)
    _write_state({
        "start": START.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": END.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_run_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_through_utc": _iso(_ms(effective_end)),
        "expected_rows": len(expected),
        "appended": n1,
        "corrections": n2,
    })
    print(f"appended {n1} rows, {n2} corrections", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except NetworkError as exc:
        print(f"network error: {exc}", flush=True)
        raise SystemExit(0)
