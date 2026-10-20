#!/usr/bin/env python3
"""Reproduce quant's migrated x-quant-trials results from public Binance data (no keys).

Data: https://data.binance.vision/ spot daily klines (BTCUSDT, ETHUSDT, SOLUSDT), 2020-12-31 .. 2026-10-13.
Downloads into ./_data (not committed). Requires: pandas, numpy.
Run:  python3 reproduce.py           -> prints tables and writes results.csv / folds.csv

Protocol (frozen from x-quant-trials, see RULES.md):
  4 walk-forward OOS test folds: 2022-12-31..2023-12-30, 2023-12-31..2024-12-29,
  2024-12-30..2025-12-29, 2025-12-30..2026-10-13. Each fold: strategy recomputed on data
  starting 250 days before the fold (warm-up), metrics on the test days only.
  "compound" = product of the 4 fold returns - 1; "worst_fold_dd" = worst intra-fold drawdown;
  "path_dd" = max drawdown of the concatenated 4-fold OOS equity path (stricter, added here).
  Costs: fee per side on |delta weight|: 0.10% base and 0.30% (GUIDE's per-side cost, "harsh").
  Lag-1: weights decided on close t-1 earn return of day t. Spot, long-only, no leverage.
"""
import io, zipfile, urllib.request, pathlib, sys
import numpy as np, pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "_data"
START, END = "2020-12-31", "2026-10-13"
SYMS = ["BTC", "ETH", "SOL"]
REBAL = 5
FOLDS = [("2022-12-31", "2023-12-30"), ("2023-12-31", "2024-12-29"),
         ("2024-12-30", "2025-12-29"), ("2025-12-30", "2026-10-13")]
LOOK = 250


def _get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def load(sym):
    DATA.mkdir(exist_ok=True)
    cache = DATA / f"{sym}USDT_1d.csv"
    if cache.exists():
        df = pd.read_csv(cache, index_col=0, parse_dates=True)
        return df
    frames = []
    months = pd.period_range("2020-12", "2026-09", freq="M")
    base = "https://data.binance.vision/data/spot"
    urls = [f"{base}/monthly/klines/{sym}USDT/1d/{sym}USDT-1d-{m}.zip" for m in months]
    urls += [f"{base}/daily/klines/{sym}USDT/1d/{sym}USDT-1d-{d.date()}.zip"
             for d in pd.date_range("2026-10-01", END)]
    for u in urls:
        z = zipfile.ZipFile(io.BytesIO(_get(u)))
        raw = pd.read_csv(z.open(z.namelist()[0]), header=None)
        frames.append(raw.iloc[:, :6])
    raw = pd.concat(frames)
    t = raw[0].astype("int64")
    t = np.where(t > 10**14, t // 1000, t)  # Binance switched to microseconds in 2025
    df = pd.DataFrame({"open": raw[1].values, "high": raw[2].values, "low": raw[3].values,
                       "close": raw[4].values, "volume": raw[5].values},
                      index=pd.to_datetime(t, unit="ms")).sort_index()
    df = df[~df.index.duplicated()].loc[START:END].astype(float)
    df.to_csv(cache)
    return df


def freeze(w):
    return w.reindex(w.index[::REBAL]).reindex(w.index, method="ffill")


def apply(w, px, fee):
    r = px.pct_change().fillna(0.0)
    turn = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    return (w * r).sum(axis=1) - turn * fee


# ---------- M1: VM book (known T-T2-vm) and BTC-gated variants ----------
def vm_weights(px):
    mom = px.shift(1) / px.shift(31) - 1.0
    sel = (mom > 0).astype(float)
    w0 = sel.div(sel.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    sleeve = (freeze(w0).shift(1).fillna(0.0) * px.pct_change().fillna(0.0)).sum(axis=1)
    wvol = (sleeve.resample("W-FRI").sum().rolling(4).std() * np.sqrt(52)).shift(1)
    scale = (0.15 / wvol.reindex(px.index, method="ffill").replace(0, np.nan)).clip(0, 1).fillna(0.0)
    return freeze(w0.mul(scale, axis=0)).shift(1).fillna(0.0)


def sar_above(h, l, c, step=0.02, max_af=0.15):
    h, l, c = h.values, l.values, c.values
    n = len(c); sar = np.full(n, np.nan); bull = True; sar[0] = l[0]; ep = h[0]; af = step
    for i in range(1, n):
        p = sar[i - 1]
        if bull:
            cand = min(p + af * (ep - p), l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if l[i] < cand:
                bull, sar[i], ep, af = False, ep, l[i], step
            else:
                sar[i] = cand
                if h[i] > ep: ep, af = h[i], min(af + step, max_af)
        else:
            cand = max(p + af * (ep - p), h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > cand:
                bull, sar[i], ep, af = True, ep, h[i], step
            else:
                sar[i] = cand
                if l[i] < ep: ep, af = l[i], min(af + step, max_af)
    return pd.Series(c >= sar, index=range(n)).values


def gate_series(name, btc):
    c = btc["close"]
    if name == "sar":      # pool lead X487: BTC close >= Parabolic SAR(0.02, 0.15)
        return pd.Series(sar_above(btc["high"], btc["low"], c), index=c.index)
    if name == "pctb":     # pool lead X506: BTC Bollinger %B(20,2) >= 0.4
        m, s = c.rolling(20).mean(), c.rolling(20).std()
        return ((c - (m - 2 * s)) / (4 * s)) >= 0.4
    if name == "cci":      # pool lead X489: BTC CCI(20) >= 0
        tp = (btc["high"] + btc["low"] + c) / 3
        ma = tp.rolling(20).mean(); md = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        return ((tp - ma) / (0.015 * md)) >= 0
    if name.startswith("sma"):  # added here, pre-declared simple gates (not from the pool)
        n = int(name[3:])
        return c >= c.rolling(n).mean()
    raise ValueError(name)


def m1_net(panels, fee, gate=None):
    px = pd.DataFrame({s: panels[s]["close"] for s in SYMS}).dropna()
    w = vm_weights(px)
    if gate:
        keep = gate_series(gate, panels["BTC"].reindex(px.index)).astype(float)
        w = w.mul(keep.shift(1).fillna(1.0), axis=0)
    return apply(w, px, fee), w


# ---------- M2: PAA-style breadth gate (S8 lead) ----------
def m2_net(panels, fee):
    px = pd.DataFrame({s: panels[s]["close"] for s in SYMS}).dropna()
    mom = px / px.shift(60) - 1.0
    pos = (mom > 0).astype(float)
    sel = pos.mul((pos.sum(axis=1) >= 2).astype(float), axis=0)
    w = sel.div(sel.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    vols = px.pct_change().rolling(60).std() * np.sqrt(365)
    avg = (w * vols).sum(axis=1) / w.sum(axis=1).replace(0, np.nan)
    w = freeze(w.mul((0.30 / avg.replace(0, np.nan)).clip(0, 1), axis=0)).shift(1).fillna(0.0)
    return apply(w, px, fee), w


# ---------- baselines ----------
def ew_hold(panels, fee):
    px = pd.DataFrame({s: panels[s]["close"] for s in SYMS}).dropna()
    w = pd.DataFrame(1 / 3, index=px.index, columns=px.columns)
    w = freeze(w).shift(1).fillna(0.0)
    return apply(w, px, fee), w


def tsmom1(panels, fee, sym="ETH", lb=30):
    c = panels[sym]["close"]
    pos = (c / c.shift(lb) - 1 > 0).astype(float).shift(1).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())
    return pos * c.pct_change().fillna(0.0) - turn * fee, pos.to_frame()


# ---------- M3: calendar windows on single asset ----------
def cal_net(panels, fee, sym, kind, shift_mask):
    c = panels[sym]["close"]; idx = c.index
    if kind == "tom":
        mask = pd.Series((idx.day == idx.days_in_month) | (idx.day <= 3), index=idx)
    else:
        mask = pd.Series(idx.dayofweek == 0, index=idx)
    pos = mask.astype(float)
    if shift_mask:   # original x-quant-trials code: pos(t)=mask(t-1) -> earns returns of days +1..+4 / Tuesday
        pos = pos.shift(1).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())
    return pos * c.pct_change().fillna(0.0) - turn * fee, pos.to_frame()


def evaluate(fn, panels, fee):
    rets, dds, shs, path, expo = [], [], [], [], []
    for a, b in FOLDS:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        sub = {s: panels[s].loc[a - pd.Timedelta(days=LOOK):b] for s in panels}
        net, w = fn(sub, fee)
        te = net.loc[a:b]
        eq = (1 + te).cumprod()
        rets.append(eq.iloc[-1] - 1); dds.append((eq / eq.cummax() - 1).min())
        shs.append(te.mean() / te.std() * np.sqrt(365) if te.std() > 0 else np.nan)
        path.append(te); expo.append(w.loc[a:b].sum(axis=1).mean())
    p = (1 + pd.concat(path)).cumprod()
    years = len(p) / 365.0
    comp = np.prod([1 + r for r in rets]) - 1
    return {"compound_pct": comp * 100, "cagr_pct": ((1 + comp) ** (1 / years) - 1) * 100,
            "worst_fold_dd_pct": min(dds) * 100, "path_dd_pct": (p / p.cummax() - 1).min() * 100,
            "mean_sharpe": float(np.nanmean(shs)), "folds_pos": sum(r > 0 for r in rets),
            "avg_exposure": float(np.mean(expo)), "fold_rets_pct": [round(r * 100, 1) for r in rets]}


def main():
    panels = {s: load(s) for s in SYMS}
    for s in SYMS:
        print(s, panels[s].index[0].date(), panels[s].index[-1].date(), len(panels[s]))
    cfg = {
        "EW_hold_BES": ew_hold,
        "ETH_tsmom30": lambda p, f: tsmom1(p, f),
        "M1_VM_base": lambda p, f: m1_net(p, f),
        "M1_VM_x_BTC_SAR": lambda p, f: m1_net(p, f, "sar"),
        "M1_VM_x_BTC_pctB": lambda p, f: m1_net(p, f, "pctb"),
        "M1_VM_x_BTC_CCI": lambda p, f: m1_net(p, f, "cci"),
        "M1_VM_x_BTC_SMA50": lambda p, f: m1_net(p, f, "sma50"),
        "M1_VM_x_BTC_SMA100": lambda p, f: m1_net(p, f, "sma100"),
        "M1_VM_x_BTC_SMA200": lambda p, f: m1_net(p, f, "sma200"),
        "M2_PAA_breadth": m2_net,
    }
    for sym in ("BTC", "ETH"):
        for kind in ("tom", "mon"):
            for sh in (True, False):
                cfg[f"M3_{sym}_{kind}_{'orig_shift' if sh else 'calendar_exact'}"] = (
                    lambda p, f, sym=sym, kind=kind, sh=sh: cal_net(p, f, sym, kind, sh))
    rows = []
    for name, fn in cfg.items():
        for fee in (0.001, 0.003):
            r = evaluate(fn, panels, fee)
            rows.append({"name": name, "fee_side": fee, **r})
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
    print(out.round(2).to_string(index=False))
    out.to_csv(HERE / "results.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
