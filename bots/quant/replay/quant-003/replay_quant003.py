#!/usr/bin/env python3
"""Round-2 replay for quant-003: breadth-gated spot momentum, frozen top-10
USDT universe, Binance spot daily klines.

Tradable-price rule (GUIDE section 9): a signal computed on close(t) is filled
at open(t+1).  Portfolio returns are therefore measured open-to-open:
    r(t) = open(t+1)/open(t) - 1,  weight effective at open(t)
Cost 0.30% per side on the traded notional |w(t) - w(t-1)| at open(t).
Development window: 2022-01-01..2024-12-31 only (no 2021, no 2025+).
No keys, no trading; public data only.

Data: https://data.binance.vision/data/spot/monthly/klines/<SYM>/1d/<SYM>-1d-<YYYY-MM>.zip
Universe: frozen ex-ante top-10 by 2020-12 quote volume, list carried over from
bots/quant/notes/r2prep-verification/quant-003.md (PRESPEC_R003).  Only OHLC
2022-2024 is downloaded here.
"""
import argparse
import io
import pathlib
import urllib.request
import zipfile
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

SYMS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "LTCUSDT", "GRTUSDT",
        "BCHUSDT", "LINKUSDT", "BNBUSDT", "ADAUSDT", "XLMUSDT"]
BASE = "https://data.binance.vision/data/spot/monthly/klines"
MONTHS = pd.period_range("2022-01", "2024-12", freq="M")
START, END = "2022-01-01", "2024-12-31"
FEE = 0.003
REBAL = 5
FOLDS = [("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-12-31"),
         ("2024-01-01", "2024-12-31")]


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


def load(sym, cache):
    path = cache / f"{sym}_1d_2022_2024.csv"
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)
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
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    return df


def target_weights(close, open_, lb, k, vol_target=True):
    """Weights decided on close(t); caller shifts them to open(t+1) via eff()."""
    mom = close / close.shift(lb) - 1.0
    pos = (mom > 0).astype(float)
    sel = pos.mul((pos.sum(axis=1) >= k).astype(float), axis=0)
    w = sel.div(sel.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    if vol_target:
        vols = close.pct_change().rolling(60).std() * np.sqrt(365)
        avg = (w * vols).sum(axis=1) / w.sum(axis=1).replace(0, np.nan)
        w = w.mul((0.30 / avg.replace(0, np.nan)).clip(0, 1), axis=0)
    w = w.reindex(w.index[::REBAL]).reindex(close.index, method="ffill")
    return w


def run(w_target, close, open_):
    """Shift target weights one bar forward and settle at the next open."""
    dates = close.index
    w = w_target.shift(1)              # effective at open(t); decided at close(t-1)
    w = w.loc[dates].fillna(0.0)
    r = open_.shift(-1) / open_ - 1.0  # open(t) -> open(t+1)
    gross = (w * r).sum(axis=1)
    turn = (w - w.shift(1).fillna(0.0)).abs().sum(axis=1)
    net = (gross - turn * FEE).iloc[:-1]  # last bar has no next open
    return net, w, turn


def metrics(net, w):
    eq = (1 + net).cumprod()
    return {
        "net_pct": (eq.iloc[-1] - 1) * 100,
        "cagr_pct": (eq.iloc[-1] ** (365 / len(net)) - 1) * 100,
        "mdd_pct": (eq / eq.cummax() - 1).min() * 100,
        "sharpe": net.mean() / net.std() * np.sqrt(365) if net.std() > 0 else np.nan,
        "expo": w.loc[net.index].sum(axis=1).mean(),
    }


def segments(mask):
    n, prev = 0, 0
    for v in mask.astype(int).values:
        if v == 1 and prev == 0:
            n += 1
        prev = v
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(pathlib.Path(__file__).resolve().parent / "_cache"))
    args = ap.parse_args()
    cache = pathlib.Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)

    bars = {s: load(s, cache) for s in SYMS}
    close = pd.DataFrame({s: bars[s]["close"] for s in SYMS}).dropna()
    open_ = pd.DataFrame({s: bars[s]["open"] for s in SYMS}).reindex(close.index)
    print("common panel:", close.index[0].date(), close.index[-1].date(), len(close))

    variants = {}
    for k in range(1, 11):
        variants[f"GATE_k{k}"] = (target_weights(close, open_, 60, k), True)
    variants["B1_tsmom30_basket"] = (target_weights(close, open_, 30, 1), True)
    variants["B2_tsmom60_basket"] = (target_weights(close, open_, 60, 1), True)
    ew = pd.DataFrame(1 / len(SYMS), index=close.index, columns=close.columns)
    variants["B4_EW_hold"] = (ew.reindex(ew.index[::REBAL]).reindex(close.index, method="ffill"), False)
    variants["POSTHOC_gate30_k6"] = (target_weights(close, open_, 30, 6), True)

    rows, nets, ws = [], {}, {}
    for name, (wt, _) in variants.items():
        net, w, _ = run(wt, close, open_)
        m = metrics(net, w)
        rec = {"variant": name, "net_pct": m["net_pct"], "cagr_pct": m["cagr_pct"],
               "mdd_pct": m["mdd_pct"], "sharpe": m["sharpe"], "expo": m["expo"]}
        for i, (a, b) in enumerate(FOLDS, 1):
            te = net.loc[a:b]
            rec[f"y{i}_ret"] = (1 + te).prod() * 100 - 100
            rec[f"y{i}_sh"] = te.mean() / te.std() * np.sqrt(365) if te.std() > 0 else np.nan
        rows.append(rec)
        nets[name], ws[name] = net, w

    # per-coin plain 30d long/flat, same 5-day rebalance, no vol target
    per = []
    for s in SYMS:
        c = close[[s]]
        o = open_[[s]]
        wt = ((c / c.shift(30) - 1) > 0).astype(float).reindex(close.index[::REBAL]).reindex(close.index, method="ffill")
        net, w, _ = run(wt, c, o)
        m = metrics(net, w)
        per.append({"coin": s, "net_pct": m["net_pct"], "cagr_pct": m["cagr_pct"],
                    "mdd_pct": m["mdd_pct"], "sharpe": m["sharpe"]})
    per_df = pd.DataFrame(per)

    res = pd.DataFrame(rows)
    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)
    print("\n=== portfolio variants (next-open fills, 0.30%/side, 2022-2024) ===")
    print(res.round(2).to_string(index=False))
    print("\n=== per-coin plain 30d long/flat (next-open fills, 0.30%/side) ===")
    print(per_df.round(2).to_string(index=False))

    mom = close / close.shift(60) - 1
    valid = mom.notna().any(axis=1)
    off = ((mom > 0).sum(axis=1) < 6) & valid
    print(f"\nGATE_k6: valid days={int(valid.sum())}, risk-off days={int(off.sum())}, "
          f"risk-off segments={segments(off)}")

    out = pathlib.Path(__file__).resolve().parent
    res.to_csv(out / "results_replay.csv", index=False, float_format="%.4f")
    per_df.to_csv(out / "results_percoin.csv", index=False, float_format="%.4f")
    k6 = nets["GATE_k6"]
    eq = pd.DataFrame({"GATE_k6_net": k6,
                       "GATE_k6_equity": (1 + k6).cumprod(),
                       "B1_net": nets["B1_tsmom30_basket"],
                       "B1_equity": (1 + nets["B1_tsmom30_basket"]).cumprod()})
    eq.to_csv(out / "equity_curve.csv", float_format="%.6f")
    reb = ws["GATE_k6"].loc[k6.index]
    reb["turnover"] = reb.diff().abs().sum(axis=1)
    reb.to_csv(out / "k6_weights.csv", float_format="%.6f")
    print("\nwrote results_replay.csv, results_percoin.csv, equity_curve.csv, k6_weights.csv")


if __name__ == "__main__":
    main()
