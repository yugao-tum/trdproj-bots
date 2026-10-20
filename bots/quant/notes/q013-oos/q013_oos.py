#!/usr/bin/env python3
"""
quant-013 true out-of-sample backtest.

Frozen rules (copied from bots/quant/entries/quant-013-coinbase-premium-signal.md):
  p_t = (CB_t / (BN_t * U_t) - 1) * 10000
  z_t = (p_t - mean(p_{t-30..t-1})) / pstdev(p_{t-30..t-1})
  enter next UTC open when z_t >= +1.0; exit next UTC open when z_t < 0,
  or after 10 held trading days; skip new entries when |U_t - 1| > 0.01
  (USDT depeg > 100 bp); 0.30% cost per side.

Event-count convention (matches the entry's own 29-event in-sample run):
  signal days with index difference <= 3 trading days are merged into one event.
Event-return convention (matches the entry's reported event stats):
  enter at open of signal+1, exit at close of signal+4 (three days after the
  entry date), subtract 0.60% round-trip cost.  The same convention is used
  for the unconditional 3-day baseline.

Only keyless public endpoints:
  Coinbase Exchange candles (BTC-USD, USDT-USD)
  data.binance.vision monthly 1d klines (BTCUSDT, SOLUSDT)

Raw downloads live in ./_cache/ (gitignored).  Re-runs read the cache and
never need the network.  Run: python3 q013_oos.py
"""

import csv
import datetime as dt
import io
import json
import math
import os
import sys
import time
import zipfile
from collections import OrderedDict

import numpy as np
import pandas as pd
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_cache")
OUT_CSV = os.path.join(HERE, "results.csv")

CB_BASE = "https://api.exchange.coinbase.com/products/{}/candles"
BN_MONTHLY = "https://data.binance.vision/data/spot/monthly/klines/{}/1d/{}-1d-{}.zip"
BN_DAILY = "https://data.binance.vision/data/spot/daily/klines/{}/1d/{}-1d-{}.zip"

COST_SIDE = 0.0030
COST_ROUND = 2 * COST_SIDE
Z_WINDOW = 30
Z_ENTRY = 1.0
Z_EXIT = 0.0
MAX_HOLD = 10
DEPEG_BP = 100.0

DATA_START = dt.date(2021, 5, 1)
CB_END = dt.date(2026, 10, 20)
BN_FIRST_MONTH = (2021, 5)
BN_LAST_MONTH = (2026, 9)

OOS_START = None  # filled from the first aligned date
OOS_END = dt.date(2025, 8, 14)
IS_START = dt.date(2025, 8, 15)
IS_END = dt.date(2026, 9, 30)

UA = "Mozilla/5.0 (compatible; quant-013-oos/1.0)"

SUMMARY_FIELDS = [
    "table", "period", "asset", "year", "events", "events_blocked",
    "event_n", "event_mean_pct", "event_median_pct", "event_win_pct",
    "uncond_n", "uncond_mean_pct", "uncond_median_pct",
    "trades", "trade_mean_pct", "trade_hit_pct",
    "rule_return_pct", "rule_maxdd_pct", "exposure_pct",
    "bh_return_pct", "bh_maxdd_pct", "verdict",
]


def log(msg=""):
    print(msg, flush=True)


def date_list(start, end):
    out = []
    d = start
    while d <= end:
        out.append(d)
        d += dt.timedelta(days=1)
    return out


def load_json_cache(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            rows = json.load(f)
        return {dt.datetime.fromtimestamp(r[0], dt.timezone.utc).date(): r for r in rows}
    except Exception as exc:
        log(f"[warn] cannot read {path}: {exc!r}")
        return {}


def save_json_cache(path, rows):
    ordered = [rows[k] for k in sorted(rows)]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, separators=(",", ":"))


def http_get(url, tries=4, timeout=30, sleep=0.0):
    last = None
    for attempt in range(tries):
        if sleep:
            time.sleep(sleep)
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
            if r.status_code == 404:
                return None
            if r.status_code in (400, 401, 403):
                return None
            time.sleep(1.5 * (attempt + 1))
        except Exception as exc:
            last = repr(exc)
            time.sleep(1.5 * (attempt + 1))
    log(f"[warn] GET failed after {tries} tries: {url} ({last})")
    return None


def fetch_coinbase(product):
    path = os.path.join(CACHE, f"coinbase_{product}.json")
    cached = load_json_cache(path)
    if cached:
        first, last = min(cached), max(cached)
        if first <= DATA_START + dt.timedelta(days=7) and last >= CB_END - dt.timedelta(days=2):
            log(f"[data] Coinbase {product}: cache hit rows={len(cached)} first={first} last={last}")
            return cached
    rows = dict(cached)
    start = DATA_START
    requests_made = 0
    while start <= CB_END:
        end = min(start + dt.timedelta(days=249), CB_END)
        url = CB_BASE.format(product) + (
            f"?granularity=86400&start={start.isoformat()}T00:00:00Z"
            f"&end={end.isoformat()}T00:00:00Z"
        )
        r = http_get(url, timeout=30)
        requests_made += 1
        if r is not None:
            try:
                payload = r.json()
            except Exception:
                payload = []
            for item in payload:
                if isinstance(item, list) and len(item) >= 6:
                    d = dt.datetime.fromtimestamp(int(item[0]), dt.timezone.utc).date()
                    rows[d] = [int(item[0]), item[1], item[2], item[3], item[4], item[5]]
        time.sleep(0.40)
        start = end + dt.timedelta(days=1)
    if not rows:
        log(f"[error] Coinbase {product}: no rows fetched and no cache")
        sys.exit(1)
    save_json_cache(path, rows)
    first, last = min(rows), max(rows)
    log(f"[data] Coinbase {product}: fetched requests={requests_made} rows={len(rows)} first={first} last={last}")
    return rows


def parse_binance_csv(text):
    out = {}
    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if not row or len(row) < 5:
            continue
        try:
            ts = int(row[0])
        except ValueError:
            continue
        if ts > 10**14:
            ts //= 1000
        d = dt.datetime.fromtimestamp(ts / 1000.0, dt.timezone.utc).date()
        try:
            out[d] = (float(row[1]), float(row[4]))
        except ValueError:
            continue
    return out


def month_seq(first, last):
    y, m = first
    while (y, m) <= last:
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch_binance_symbol(symbol):
    path = os.path.join(CACHE, f"binance_{symbol}_1d.csv")
    cached = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    d = dt.date.fromisoformat(row["date"])
                    cached[d] = (float(row["open"]), float(row["close"]))
        except Exception as exc:
            log(f"[warn] cannot read {path}: {exc!r}")
    if cached:
        first, last = min(cached), max(cached)
        if first <= dt.date(BN_FIRST_MONTH[0], BN_FIRST_MONTH[1], 5) and last >= dt.date(2026, 9, 25):
            log(f"[data] Binance {symbol}: cache hit rows={len(cached)} first={first} last={last}")
            return cached
    rows = dict(cached)
    monthly_ok = 0
    monthly_missing = []
    daily_used = 0
    for y, m in month_seq(BN_FIRST_MONTH, BN_LAST_MONTH):
        tag = f"{y:04d}-{m:02d}"
        url = BN_MONTHLY.format(symbol, symbol, tag)
        r = http_get(url, timeout=40)
        if r is None:
            monthly_missing.append(tag)
            # Fallback: daily zips for every day of that month.
            d = dt.date(y, m, 1)
            while d.month == m:
                url_d = BN_DAILY.format(symbol, symbol, d.isoformat())
                rd = http_get(url_d, timeout=40)
                if rd is not None:
                    try:
                        with zipfile.ZipFile(io.BytesIO(rd.content)) as zf:
                            for name in zf.namelist():
                                rows.update(parse_binance_csv(zf.read(name).decode("utf-8")))
                    except Exception as exc:
                        log(f"[warn] bad daily zip {symbol} {d}: {exc!r}")
                    daily_used += 1
                d += dt.timedelta(days=1)
            time.sleep(0.05)
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                for name in zf.namelist():
                    rows.update(parse_binance_csv(zf.read(name).decode("utf-8")))
            monthly_ok += 1
        except Exception as exc:
            log(f"[warn] bad monthly zip {symbol} {tag}: {exc!r}")
            monthly_missing.append(tag)
        time.sleep(0.06)
    if not rows:
        log(f"[error] Binance {symbol}: no rows fetched and no cache")
        sys.exit(1)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "close"])
        for d in sorted(rows):
            w.writerow([d.isoformat(), rows[d][0], rows[d][1]])
    first, last = min(rows), max(rows)
    log(
        f"[data] Binance {symbol}: fetched monthly_ok={monthly_ok} "
        f"monthly_missing={monthly_missing or '-'} daily_fallback={daily_used} "
        f"rows={len(rows)} first={first} last={last}"
    )
    return rows


def build_panel():
    cb_btc = fetch_coinbase("BTC-USD")
    cb_usdt = fetch_coinbase("USDT-USD")
    bn_btc = fetch_binance_symbol("BTCUSDT")
    bn_sol = fetch_binance_symbol("SOLUSDT")

    common = sorted(set(cb_btc) & set(cb_usdt) & set(bn_btc))
    if not common:
        log("[error] no common dates")
        sys.exit(1)
    first, last = common[0], common[-1]
    span_days = (last - first).days + 1
    log(
        f"[data] aligned (CB BTC-USD & CB USDT-USD & BN BTCUSDT): rows={len(common)} "
        f"first={first} last={last} calendar_days={span_days} missing={span_days - len(common)}"
    )
    missing_cb = [d for d in date_list(first, last) if d not in set(cb_btc) or d not in set(cb_usdt)]
    log(f"[data] dates missing from either Coinbase series in aligned span: {len(missing_cb)}")
    sol_missing = [d for d in common if d not in bn_sol]
    log(f"[data] aligned dates with no Binance SOLUSDT row: {len(sol_missing)}")

    idx = pd.to_datetime([d.isoformat() for d in common], utc=True)
    df = pd.DataFrame(index=idx)
    df["cb_btc"] = [float(cb_btc[d][4]) for d in common]
    df["cb_usdt"] = [float(cb_usdt[d][4]) for d in common]
    df["bn_btc_open"] = [float(bn_btc[d][0]) for d in common]
    df["bn_btc_close"] = [float(bn_btc[d][1]) for d in common]
    df["bn_sol_open"] = [float(bn_sol[d][0]) if d in bn_sol else np.nan for d in common]
    df["bn_sol_close"] = [float(bn_sol[d][1]) if d in bn_sol else np.nan for d in common]
    df["premium_bp"] = (df["cb_btc"] / (df["bn_btc_close"] * df["cb_usdt"]) - 1.0) * 1e4
    p = df["premium_bp"].to_numpy(dtype=float)
    z = np.full(len(p), np.nan)
    for i in range(Z_WINDOW, len(p)):
        w = p[i - Z_WINDOW:i]
        if np.isnan(w).any():
            continue
        sd = float(np.std(w, ddof=0))
        if sd > 0:
            z[i] = (p[i] - float(np.mean(w))) / sd
    df["z"] = z
    df["depeg"] = (df["cb_usdt"] - 1.0).abs() > (DEPEG_BP / 1e4)
    df["depeg_bp"] = (df["cb_usdt"] - 1.0).abs() * 1e4
    return df


def event_groups(df, merge_diff=3):
    sig = np.where(df["z"].to_numpy(dtype=float) >= Z_ENTRY)[0]
    groups = []
    for i in sig:
        i = int(i)
        if groups and i - groups[-1][-1] <= merge_diff:
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def event_table(df, groups, asset, start, end):
    o = df[f"bn_{asset}_open"].to_numpy(dtype=float)
    c = df[f"bn_{asset}_close"].to_numpy(dtype=float)
    dates = df.index
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    out = []
    for g in groups:
        s = g[0]
        if dates[s] < start_ts or dates[s] > end_ts:
            continue
        if s + 4 >= len(df):
            out.append({"start": dates[s].date(), "ret": None, "blocked": bool(df["depeg"].iloc[s])})
            continue
        if dates[s + 4] > end_ts:
            out.append({"start": dates[s].date(), "ret": None, "blocked": bool(df["depeg"].iloc[s])})
            continue
        entry, exit_ = o[s + 1], c[s + 4]
        if not np.isfinite(entry) or not np.isfinite(exit_) or entry <= 0:
            ret = None
        else:
            ret = exit_ / entry - 1.0 - COST_ROUND
        out.append({"start": dates[s].date(), "ret": ret, "blocked": bool(df["depeg"].iloc[s])})
    return out


def stats(vals):
    vals = [v for v in vals if v is not None and np.isfinite(v)]
    if not vals:
        return {"n": 0, "mean": None, "median": None, "win": None}
    a = np.array(vals, dtype=float)
    return {
        "n": len(a),
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "win": float(np.mean(a > 0)),
    }


def unconditional(df, asset, start, end):
    o = df[f"bn_{asset}_open"].to_numpy(dtype=float)
    c = df[f"bn_{asset}_close"].to_numpy(dtype=float)
    dates = df.index
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    vals = []
    for i in range(len(df)):
        if dates[i] < start_ts or dates[i] > end_ts:
            continue
        if i + 4 >= len(df) or dates[i + 4] > end_ts:
            continue
        entry, exit_ = o[i + 1], c[i + 4]
        if np.isfinite(entry) and np.isfinite(exit_) and entry > 0:
            vals.append(exit_ / entry - 1.0 - COST_ROUND)
    return stats(vals)


def max_drawdown(series):
    a = np.asarray(series, dtype=float)
    if len(a) == 0:
        return None
    peak = np.maximum.accumulate(a)
    dd = a / peak - 1.0
    return float(np.min(dd))


def backtest(df, asset, start, end):
    o = df[f"bn_{asset}_open"].to_numpy(dtype=float)
    c = df[f"bn_{asset}_close"].to_numpy(dtype=float)
    z = df["z"].to_numpy(dtype=float)
    depeg = df["depeg"].to_numpy(dtype=bool)
    dates = df.index
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    idxs = [i for i in range(len(df)) if start_ts <= dates[i] <= end_ts]
    if not idxs:
        return None
    i0, i1 = idxs[0], idxs[-1]

    cash = 1.0
    units = 0.0
    pending = None
    held = 0
    trades = 0
    trade_rets = []
    entry_cash = None
    equity = []
    pos_flag = []
    forced_close = False

    for i in range(i0, i1 + 1):
        if pending == "entry":
            px = o[i]
            if np.isfinite(px) and px > 0:
                entry_cash = cash
                units = cash * (1.0 - COST_SIDE) / px
                cash = 0.0
                trades += 1
                held = 0
            pending = None
        elif pending == "exit":
            px = o[i]
            if np.isfinite(px) and px > 0 and units > 0:
                cash = units * px * (1.0 - COST_SIDE)
                if entry_cash and entry_cash > 0:
                    trade_rets.append(cash / entry_cash - 1.0)
                units = 0.0
                entry_cash = None
                held = 0
            pending = None

        eq = cash + units * c[i] if np.isfinite(c[i]) else cash
        equity.append(eq)
        pos_flag.append(1 if units > 0 else 0)

        if i < i1:
            if units > 0:
                held += 1
                if (np.isfinite(z[i]) and z[i] < Z_EXIT) or held >= MAX_HOLD:
                    pending = "exit"
            else:
                if np.isfinite(z[i]) and z[i] >= Z_ENTRY and not depeg[i]:
                    pending = "entry"

    if units > 0:
        px = c[i1]
        cash = units * px * (1.0 - COST_SIDE)
        if entry_cash and entry_cash > 0:
            trade_rets.append(cash / entry_cash - 1.0)
        units = 0.0
        equity[-1] = cash
        forced_close = True

    eq = np.array(equity, dtype=float)
    return {
        "start": dates[i0].date(),
        "end": dates[i1].date(),
        "equity": eq,
        "pos": np.array(pos_flag, dtype=float),
        "trades": trades,
        "trade_rets": trade_rets,
        "total": float(eq[-1] - 1.0),
        "maxdd": max_drawdown(eq),
        "exposure": float(np.mean(np.array(pos_flag, dtype=float))),
        "forced_close": forced_close,
    }


def buy_hold(df, asset, start, end):
    c = df[f"bn_{asset}_close"].to_numpy(dtype=float)
    dates = df.index
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    idxs = [i for i in range(len(df)) if start_ts <= dates[i] <= end_ts]
    if not idxs:
        return None
    vals = c[idxs[0]:idxs[-1] + 1]
    norm = vals / vals[0]
    return {
        "start": dates[idxs[0]].date(),
        "end": dates[idxs[-1]].date(),
        "total": float(norm[-1] - 1.0),
        "maxdd": max_drawdown(norm),
        "series": norm,
    }


def yearly(eq, bh, dates):
    rows = []
    years = sorted(set(d.year for d in dates))
    prev_eq = 1.0
    prev_bh = 1.0
    date_arr = np.array([d.year for d in dates])
    for y in years:
        mask = date_arr == y
        if not mask.any():
            continue
        end_eq = float(eq[mask][-1])
        end_bh = float(bh[mask][-1])
        rows.append({
            "year": y,
            "rule": end_eq / prev_eq - 1.0,
            "bh": end_bh / prev_bh - 1.0,
        })
        prev_eq = end_eq
        prev_bh = end_bh
    return rows


def pct(x):
    if x is None:
        return "NA"
    return f"{x * 100:+.2f}%"


def entry_window_replication(df):
    """Reproduce the entry's in-sample run: z is computed only inside 2025-08-15..2026-09-30.

    The entry did not use pre-2025-08-15 premium observations for the z warmup.
    That discards the first 30 days and is why its event count is 29, not 31.
    """
    sub = df[(df.index >= pd.Timestamp(IS_START, tz="UTC")) & (df.index <= pd.Timestamp(IS_END, tz="UTC"))].copy()
    p = sub["premium_bp"].to_numpy(dtype=float)
    z = np.full(len(p), np.nan)
    for i in range(Z_WINDOW, len(p)):
        w = p[i - Z_WINDOW:i]
        if np.isnan(w).any():
            continue
        sd = float(np.std(w, ddof=0))
        if sd > 0:
            z[i] = (p[i] - float(np.mean(w))) / sd
    sub["z"] = z
    groups = event_groups(sub, merge_diff=3)
    out = {"rows": len(sub), "events": len(groups), "z_first": sub.index[np.where(~np.isnan(z))[0][0]].date() if np.any(~np.isnan(z)) else None, "assets": {}}
    for asset in ("btc", "sol"):
        et = event_table(sub, groups, asset, IS_START, IS_END)
        es = stats([e["ret"] for e in et if e["ret"] is not None and not e["blocked"]])
        bt = backtest(sub, asset, IS_START, IS_END)
        bh = buy_hold(sub, asset, IS_START, IS_END)
        ts = stats(bt["trade_rets"])
        out["assets"][asset] = {"et": et, "es": es, "bt": bt, "bh": bh, "ts": ts}
    return sub, groups, out


def main():
    os.makedirs(CACHE, exist_ok=True)
    log("===== quant-013 true out-of-sample backtest =====")
    log("rules: p=(CB_BTC/(BN_BTC*CB_USDT)-1)*1e4; z=30d excl today, population sd;")
    log("       enter z>=+1 next open; exit z<0 next open or 10 held days; depeg>100bp blocks entries;")
    log("       cost 0.30%/side (0.60% round trip); no parameter tuning")
    log()

    df = build_panel()
    if df["premium_bp"].isna().any():
        log(f"[warn] premium NaN rows={int(df['premium_bp'].isna().sum())}")
    if df["z"].isna().all():
        log("[error] no z values")
        sys.exit(1)

    prem = df["premium_bp"].dropna()
    log()
    log("===== 2. Premium / signal =====")
    log(
        f"[premium] n={len(prem)} mean={prem.mean():+.2f}bp median={prem.median():+.2f}bp "
        f"sd={prem.std(ddof=0):.2f}bp min={prem.min():+.2f}bp max={prem.max():+.2f}bp"
    )
    zser = df["z"].dropna()
    log(f"[z] valid n={len(zser)} first={zser.index[0].date()} last={zser.index[-1].date()}")
    depeg_days = df.index[df["depeg"]].date.tolist()
    log(f"[depeg] days with |U-1|>100bp: n={len(depeg_days)} {depeg_days[:10]}{' ...' if len(depeg_days) > 10 else ''}")

    groups = event_groups(df, merge_diff=3)
    starts = [df.index[g[0]].date() for g in groups]
    log(f"[events] total merged events (signal-index difference<=3 trading days, whole aligned sample): {len(groups)}")
    log(f"[events] first={starts[0] if starts else None} last={starts[-1] if starts else None}")
    log("[events] event return: entry=open(signal+1), exit=close(signal+4), cost=0.60% round trip")

    oos_start = df.index[0].date()
    periods = [
        ("TRUE_OOS", oos_start, OOS_END),
        ("IN_SAMPLE", IS_START, IS_END),
        ("FULL", oos_start, IS_END),
    ]

    summary_rows = []
    yearly_rows = []
    verdicts = {}

    for pname, pstart, pend in periods:
        log()
        log(f"===== PERIOD {pname} {pstart}..{pend} =====")
        pgroups = [g for g in groups if pd.Timestamp(pstart, tz="UTC") <= df.index[g[0]] <= pd.Timestamp(pend, tz="UTC")]
        log(f"[period] aligned rows={int(((df.index >= pd.Timestamp(pstart, tz='UTC')) & (df.index <= pd.Timestamp(pend, tz='UTC'))).sum())} events_starting={len(pgroups)}")
        for asset in ("btc", "sol"):
            et = event_table(df, groups, asset, pstart, pend)
            usable_all = [e for e in et if e["ret"] is not None]
            usable = [e for e in usable_all if not e["blocked"]]
            blocked = [e for e in et if e["blocked"]]
            es = stats([e["ret"] for e in usable])
            un = unconditional(df, asset, pstart, pend)
            bt = backtest(df, asset, pstart, pend)
            bh = buy_hold(df, asset, pstart, pend)
            trade_stats = stats(bt["trade_rets"])
            log(
                f"[{asset.upper()}] events_starting={len(et)} full3d={len(usable_all)} "
                f"blocked_by_depeg={len(blocked)} tradeable_event_n={es['n']}"
            )
            log(
                f"[{asset.upper()}] event 3d net: mean={pct(es['mean'])} median={pct(es['median'])} "
                f"win={pct(es['win']) if es['win'] is not None else 'NA'}"
            )
            log(
                f"[{asset.upper()}] unconditional 3d net: n={un['n']} mean={pct(un['mean'])} "
                f"median={pct(un['median'])}"
            )
            log(
                f"[{asset.upper()}] rule: trades={bt['trades']} total={pct(bt['total'])} "
                f"maxdd={pct(bt['maxdd'])} exposure={pct(bt['exposure'])} "
                f"mean/trade={pct(trade_stats['mean'])} hit={pct(trade_stats['win']) if trade_stats['win'] is not None else 'NA'} "
                f"forced_close={bt['forced_close']}"
            )
            log(
                f"[{asset.upper()}] buy&hold: total={pct(bh['total'])} maxdd={pct(bh['maxdd'])} "
                f"({bh['start']}..{bh['end']})"
            )
            ev_ok = len(pgroups) >= 30
            med_ok = es["median"] is not None and es["median"] > 0
            bh_ok = bt["total"] > bh["total"]
            if not ev_ok:
                verdict = "FAIL(样本<30)"
            elif not med_ok:
                verdict = "FAIL(事件中位数<=0)"
            elif not bh_ok:
                verdict = "FAIL(跑不赢买入持有)"
            else:
                verdict = "PASS"
            verdicts[(pname, asset)] = verdict
            log(
                f"[{asset.upper()}] criteria: events>=30={'Y' if ev_ok else 'N'} "
                f"median>0={'Y' if med_ok else 'N'} rule>bh={'Y' if bh_ok else 'N'} -> {verdict}"
            )
            summary_rows.append({
                "table": "summary", "period": pname, "asset": asset.upper(), "year": "",
                "events": len(et), "events_blocked": len(blocked), "event_n": es["n"],
                "event_mean_pct": "" if es["mean"] is None else round(es["mean"] * 100, 4),
                "event_median_pct": "" if es["median"] is None else round(es["median"] * 100, 4),
                "event_win_pct": "" if es["win"] is None else round(es["win"] * 100, 2),
                "uncond_n": un["n"],
                "uncond_mean_pct": "" if un["mean"] is None else round(un["mean"] * 100, 4),
                "uncond_median_pct": "" if un["median"] is None else round(un["median"] * 100, 4),
                "trades": bt["trades"],
                "trade_mean_pct": "" if trade_stats["mean"] is None else round(trade_stats["mean"] * 100, 4),
                "trade_hit_pct": "" if trade_stats["win"] is None else round(trade_stats["win"] * 100, 2),
                "rule_return_pct": round(bt["total"] * 100, 4),
                "rule_maxdd_pct": round(bt["maxdd"] * 100, 4),
                "exposure_pct": round(bt["exposure"] * 100, 2),
                "bh_return_pct": round(bh["total"] * 100, 4),
                "bh_maxdd_pct": round(bh["maxdd"] * 100, 4),
                "verdict": verdict,
            })
            # Yearly rows
            yrows = yearly(bt["equity"], bh["series"], [d for d in df.index if pd.Timestamp(pstart, tz="UTC") <= d <= pd.Timestamp(pend, tz="UTC")])
            ev_by_year = {}
            for e in et:
                ev_by_year[e["start"].year] = ev_by_year.get(e["start"].year, 0) + 1
            for yr in yrows:
                yearly_rows.append({
                    "table": "yearly", "period": pname, "asset": asset.upper(), "year": yr["year"],
                    "events": ev_by_year.get(yr["year"], 0), "events_blocked": "",
                    "event_n": "", "event_mean_pct": "", "event_median_pct": "", "event_win_pct": "",
                    "uncond_n": "", "uncond_mean_pct": "", "uncond_median_pct": "",
                    "trades": "", "trade_mean_pct": "", "trade_hit_pct": "",
                    "rule_return_pct": round(yr["rule"] * 100, 4),
                    "rule_maxdd_pct": "", "exposure_pct": "",
                    "bh_return_pct": round(yr["bh"] * 100, 4),
                    "bh_maxdd_pct": "", "verdict": "",
                })

    log()
    log("===== 3. Summary table =====")
    header = (
        f"{'period':<10} {'asset':<4} {'events':>6} {'ev_n':>5} {'ev_mean':>9} {'ev_med':>9} "
        f"{'ev_win':>7} {'unc_mean':>9} {'unc_med':>9} {'trades':>6} {'rule':>9} {'ruleDD':>8} "
        f"{'expo':>7} {'B&H':>9} {'BHDD':>8} {'verdict':<18}"
    )
    log(header)
    for r in summary_rows:
        log(
            f"{r['period']:<10} {r['asset']:<4} {r['events']:>6} {r['event_n']:>5} "
            f"{str(r['event_mean_pct'])+'%':>9} {str(r['event_median_pct'])+'%':>9} "
            f"{str(r['event_win_pct'])+'%':>7} {str(r['uncond_mean_pct'])+'%':>9} {str(r['uncond_median_pct'])+'%':>9} "
            f"{r['trades']:>6} {str(r['rule_return_pct'])+'%':>9} {str(r['rule_maxdd_pct'])+'%':>8} "
            f"{str(r['exposure_pct'])+'%':>7} {str(r['bh_return_pct'])+'%':>9} {str(r['bh_maxdd_pct'])+'%':>8} "
            f"{r['verdict']:<18}"
        )

    log()
    log("===== 4. Yearly breakdown =====")
    log(f"{'period':<10} {'asset':<4} {'year':>4} {'events':>6} {'rule':>10} {'B&H':>10}")
    for r in yearly_rows:
        log(
            f"{r['period']:<10} {r['asset']:<4} {r['year']:>4} {r['events']:>6} "
            f"{str(r['rule_return_pct'])+'%':>10} {str(r['bh_return_pct'])+'%':>10}"
        )

    log()
    log("===== 5. In-sample replication of the entry's own setup =====")
    sub, rgroups, rep = entry_window_replication(df)
    log(
        f"[replication] z computed only inside {IS_START}..{IS_END}: rows={rep['rows']} "
        f"z_first={rep['z_first']} events={rep['events']}"
    )
    log("[replication] entry text (bots/quant/entries/quant-013-coinbase-premium-signal.md line 57-59):")
    log("[replication]   29 events; BTC mean=+0.79% median=-0.41% win=48%; SOL mean=+1.43% median=-0.23% win=48%")
    log("[replication]   BTC rule 39 trades +32.69%; SOL rule 39 trades +30.25%; BTC B&H -28.74%")
    replication_rows = []
    for asset in ("btc", "sol"):
        r = rep["assets"][asset]
        es, bt, bh, ts = r["es"], r["bt"], r["bh"], r["ts"]
        log(
            f"[replication] {asset.upper()} events={len(r['et'])} event_n={es['n']} "
            f"mean={pct(es['mean'])} median={pct(es['median'])} win={pct(es['win'])} | "
            f"rule trades={bt['trades']} total={pct(bt['total'])} maxdd={pct(bt['maxdd'])} | "
            f"B&H {pct(bh['total'])}"
        )
        replication_rows.append({
            "table": "replication", "period": "IN_SAMPLE_ENTRY_SETUP", "asset": asset.upper(), "year": "",
            "events": len(r["et"]), "events_blocked": sum(1 for e in r["et"] if e["blocked"]), "event_n": es["n"],
            "event_mean_pct": "" if es["mean"] is None else round(es["mean"] * 100, 4),
            "event_median_pct": "" if es["median"] is None else round(es["median"] * 100, 4),
            "event_win_pct": "" if es["win"] is None else round(es["win"] * 100, 2),
            "uncond_n": "", "uncond_mean_pct": "", "uncond_median_pct": "",
            "trades": bt["trades"],
            "trade_mean_pct": "" if ts["mean"] is None else round(ts["mean"] * 100, 4),
            "trade_hit_pct": "" if ts["win"] is None else round(ts["win"] * 100, 2),
            "rule_return_pct": round(bt["total"] * 100, 4),
            "rule_maxdd_pct": round(bt["maxdd"] * 100, 4),
            "exposure_pct": round(bt["exposure"] * 100, 2),
            "bh_return_pct": round(bh["total"] * 100, 4),
            "bh_maxdd_pct": round(bh["maxdd"] * 100, 4),
            "verdict": "-",
        })

    log()
    log("===== 6. Verdict on TRUE_OOS =====")
    for asset in ("btc", "sol"):
        log(f"[verdict] {asset.upper()}: {verdicts[('TRUE_OOS', asset)]}")

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        w.writeheader()
        for r in summary_rows + yearly_rows + replication_rows:
            w.writerow(r)
    log(f"[out] wrote results.csv rows={len(summary_rows) + len(yearly_rows) + len(replication_rows)}")


if __name__ == "__main__":
    main()
