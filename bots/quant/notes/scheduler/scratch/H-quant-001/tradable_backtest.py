#!/usr/bin/env python3
"""quant-001 hardening: historical TRADABLE-price backtest.

Signal: daily close (from Binance 1h klines, UTC), same frozen VM + BTC gate rules
as bots/quant/notes/xqt-migration/reproduce.py.
Fill: VWAP of the first hourly bar (00:00-01:00 UTC) of the *next* day after the
signal close. That is an actual traded price, not the same-bar close. Cost per side
on |target weight change|. Long-only spot, no leverage, 4 walk-forward OOS folds
(2022-12-31..2026-10-13) plus a 2022 stress fold that is NOT strict OOS.

No API keys, no trading. Reads only cached public klines under _cache/.
Run: python3 tradable_backtest.py
"""
import gzip, pathlib
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "_cache" / "klines1h"
SYMS = ["BTC", "ETH", "SOL"]
REBAL = 5
FOLDS = [("2022-12-31", "2023-12-30"), ("2023-12-31", "2024-12-29"),
         ("2024-12-30", "2025-12-29"), ("2025-12-30", "2026-10-13")]
EXT = [("2021-12-31", "2022-12-30")] + FOLDS


def load_daily(sym):
    parts = []
    for p in sorted(CACHE.glob(f"{sym}-*.csv.gz")):
        parts.append(pd.read_csv(p, parse_dates=["open_time"]))
    h = pd.concat(parts).drop_duplicates("open_time").sort_values("open_time")
    h = h[(h.open_time >= pd.Timestamp("2020-12-31", tz="UTC")) &
          (h.open_time < pd.Timestamp("2026-10-14", tz="UTC"))]
    h["date"] = h.open_time.dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None)
    first = h[h.open_time.dt.hour == 0].set_index("date")
    g = h.groupby("date")
    d = pd.DataFrame({
        "open": g["open"].first(), "high": g["high"].max(),
        "low": g["low"].min(), "close": g["close"].last(),
        "volume": g["volume"].sum(), "quote": g["quote_volume"].sum(),
    })
    d["fill_vwap"] = first["quote_volume"] / first["volume"]
    return d.dropna()


def freeze(w):
    return w.reindex(w.index[::REBAL]).reindex(w.index, method="ffill")


def vm_weights(px):
    mom = px.shift(1) / px.shift(31) - 1.0
    sel = (mom > 0).astype(float)
    w0 = sel.div(sel.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    sleeve = (freeze(w0).shift(1).fillna(0.0) * px.pct_change().fillna(0.0)).sum(axis=1)
    wvol = (sleeve.resample("W-FRI").sum().rolling(4).std() * np.sqrt(52)).shift(1)
    scale = (0.15 / wvol.reindex(px.index, method="ffill").replace(0, np.nan)).clip(0, 1).fillna(0.0)
    return freeze(w0.mul(scale, axis=0)).shift(1).fillna(0.0)


def sma_gate(btc_close, n):
    return (btc_close >= btc_close.rolling(n).mean())


def net_close(w, px, fee):
    r = px.pct_change().fillna(0.0)
    turn = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    return (w * r).sum(axis=1) - turn * fee


def net_fill(w, fill, fee):
    # enter at first-hour VWAP of day t, value at first-hour VWAP of day t+1;
    # attribute the return to the exit date so fold slicing has no look-ahead.
    r = fill.shift(-1) / fill - 1.0
    r.index = r.index + pd.Timedelta(days=1)
    turn = w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
    turn.index = turn.index + pd.Timedelta(days=1)
    w_exit = w.copy()
    w_exit.index = w_exit.index + pd.Timedelta(days=1)
    net = (w_exit * r).sum(axis=1) - turn * fee
    return net.dropna()


def metrics(net, w, folds):
    rets, dds, shs, path, expo = [], [], [], [], []
    for a, b in folds:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        te = net.loc[a:b]
        eq = (1 + te).cumprod()
        rets.append(eq.iloc[-1] - 1)
        dds.append((eq / eq.cummax() - 1).min())
        shs.append(te.mean() / te.std() * np.sqrt(365) if te.std() > 0 else np.nan)
        path.append(te)
        expo.append(w.loc[a:b].sum(axis=1).mean())
    p = (1 + pd.concat(path)).cumprod()
    years = len(p) / 365.0
    comp = np.prod([1 + r for r in rets]) - 1
    return {"compound_pct": comp * 100, "cagr_pct": ((1 + comp) ** (1 / years) - 1) * 100,
            "worst_fold_dd_pct": min(dds) * 100, "path_dd_pct": (p / p.cummax() - 1).min() * 100,
            "mean_sharpe": float(np.nanmean(shs)), "folds_pos": sum(r > 0 for r in rets),
            "avg_exposure": float(np.mean(expo)), "fold_rets_pct": [round(r * 100, 1) for r in rets]}


def episodes(keep_eff, net_base, btc_ret, start="2021-01-01", end="2026-10-13"):
    off = keep_eff.loc[start:end].fillna(1).eq(0).values
    idx = keep_eff.loc[start:end].index
    runs, i = [], 0
    while i < len(off):
        if off[i]:
            j = i
            while j + 1 < len(off) and off[j + 1]:
                j += 1
            runs.append((idx[i], idx[j]))
            i = j + 1
        else:
            i += 1
    rows = []
    for a, b in runs:
        sub = net_base.loc[a:b]
        br = btc_ret.loc[a:b]
        rows.append({"start": a.date(), "end": b.date(), "days": len(sub),
                     "vm_ret_pct": ((1 + sub).prod() - 1) * 100,
                     "btc_ret_pct": ((1 + br).prod() - 1) * 100})
    ep = pd.DataFrame(rows)
    return ep


def main():
    panels = {s: load_daily(s) for s in SYMS}
    px = pd.DataFrame({s: panels[s]["close"] for s in SYMS}).dropna()
    fill = pd.DataFrame({s: panels[s]["fill_vwap"] for s in SYMS}).reindex(px.index)
    w = vm_weights(px)
    btc = panels["BTC"].reindex(px.index)
    base_net = net_close(w, px, 0.003)
    lines = []
    lines.append("data: daily close from Binance 1h klines (UTC), "
                 f"{px.index.min().date()}..{px.index.max().date()}, {len(px)} days")
    for s in SYMS:
        d = panels[s]
        dev = (d["fill_vwap"] / d["open"] - 1).abs()
        lines.append(f"{s}: median|first-hour VWAP/open-1|={dev.median()*1e4:.1f}bp, "
                     f"p95={dev.quantile(.95)*1e4:.1f}bp")
    lines.append("")

    # validation against the earlier close-fill reproduce.py results
    v = metrics(base_net, w, FOLDS)
    lines.append("=== VALIDATION: close-fill VM baseline should match reproduce.py ===")
    lines.append("close-fill VM 0.30%: " + str({k: (round(x, 4) if isinstance(x, float) else x)
                                               for k, x in v.items()}))
    lines.append("reproduce.py results.csv: compound 237.1525, cagr 37.8172, "
                 "worst_fold_dd -15.8209, path_dd -22.1166, avg_exposure 0.2886")
    lines.append("")

    variants = {"VM": None, "VM_x_SMA50": 50, "VM_x_SMA100": 100, "VM_x_SMA200": 200}
    rows = []
    for name, n in variants.items():
        if n is None:
            ww = w
        else:
            keep = sma_gate(btc["close"], n)
            ww = w.mul(keep.shift(1).fillna(1.0), axis=0)
        for fee in (0.001, 0.003, 0.005, 0.010):
            for mode in ("close", "fill"):
                net = net_close(ww, px, fee) if mode == "close" else net_fill(ww, fill, fee)
                r = metrics(net, ww, FOLDS)
                re = metrics(net, ww, EXT)
                rows.append({"variant": name, "fill": mode, "fee_side": fee,
                             **{f"oos_{k}": v for k, v in r.items()},
                             "ext_compound_pct": re["compound_pct"],
                             "ext_cagr_pct": re["cagr_pct"],
                             "ext_path_dd_pct": re["path_dd_pct"],
                             "ext_avg_exposure": re["avg_exposure"]})
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "tradable_results.csv", index=False, float_format="%.4f")
    show = out[out.fee_side.isin([0.003, 0.010])][[
        "variant", "fill", "fee_side", "oos_compound_pct", "oos_cagr_pct",
        "oos_worst_fold_dd_pct", "oos_path_dd_pct", "oos_avg_exposure",
        "ext_compound_pct", "ext_path_dd_pct"]].round(2)
    lines.append("=== 4 OOS folds (2022-12-31..2026-10-13), close-fill vs first-hour-VWAP fill ===")
    lines.append(show.to_string(index=False))
    lines.append("")
    lines.append("(ext_* = 5 folds incl. 2021-12-31..2022-12-30 stress fold; NOT strict OOS)")
    lines.append("")

    lines.append("=== closed-market episodes (BTC gate off; independent results) ===")
    base_for_ep = base_net
    btc_ret = btc["close"].pct_change().fillna(0.0)
    for name, n in [("SMA50", 50), ("SMA100", 100), ("SMA200", 200)]:
        keep = sma_gate(btc["close"], n)
        keep_eff = keep.shift(1).fillna(1.0)
        ep = episodes(keep_eff, base_for_ep, btc_ret)
        switches = int(((keep_eff.diff() == 1) | (keep_eff.diff() == -1)).sum())
        line = (f"{name}: off-episodes={len(ep)}, on/off switches={switches}, "
                f"off-days={int((keep_eff.loc['2021-01-01':'2026-10-13']==0).sum())}, "
                f"episode days median={ep.days.median():.0f} max={ep.days.max()}, "
                f"VM ret in off-episodes: mean={ep.vm_ret_pct.mean():.2f}% "
                f"median={ep.vm_ret_pct.median():.2f}% "
                f"negative={int((ep.vm_ret_pct<0).sum())}/{len(ep)}; "
                f"BTC ret: mean={ep.btc_ret_pct.mean():.2f}%")
        lines.append(line)
        ep.to_csv(HERE / f"episodes_{name}.csv", index=False, float_format="%.4f")
    lines.append("")
    lines.append("(base_for_ep = VM close-to-close 0.30%/side; episode return = what VM would have "
                 "earned while the gate was off. Negative mean => gate avoided losses.)")
    lines.append("")

    # same-exposure constant-leverage diagnostic: does the gate add timing value,
    # or is it just a smaller position?
    lines.append("=== same-exposure diagnostic (fill, 0.30%/side, 4 OOS folds) ===")
    base_exp = metrics(net_fill(w, fill, 0.003), w, FOLDS)["avg_exposure"]
    sed = []
    for name, n in [("SMA50", 50), ("SMA100", 100), ("SMA200", 200)]:
        keep = sma_gate(btc["close"], n)
        wg = w.mul(keep.shift(1).fillna(1.0), axis=0)
        g = metrics(net_fill(wg, fill, 0.003), wg, FOLDS)
        ge = metrics(net_fill(wg, fill, 0.003), wg, EXT)
        k = g["avg_exposure"] / base_exp
        wc = w * k
        c = metrics(net_fill(wc, fill, 0.003), wc, FOLDS)
        ce = metrics(net_fill(wc, fill, 0.003), wc, EXT)
        sed.append({"variant": name, "const_scale_k": k,
                    "gate_compound": g["compound_pct"], "const_compound": c["compound_pct"],
                    "gate_path_dd": g["path_dd_pct"], "const_path_dd": c["path_dd_pct"],
                    "gate_worst_fold_dd": g["worst_fold_dd_pct"],
                    "const_worst_fold_dd": c["worst_fold_dd_pct"],
                    "gate_ext_compound": ge["compound_pct"], "const_ext_compound": ce["compound_pct"],
                    "gate_ext_path_dd": ge["path_dd_pct"], "const_ext_path_dd": ce["path_dd_pct"]})
    sedf = pd.DataFrame(sed).round(2)
    sedf.to_csv(HERE / "same_exposure.csv", index=False)
    lines.append(sedf.to_string(index=False))
    lines.append("(const_scale_k = gate OOS avg exposure / VM OOS avg exposure; "
                 "constant-scaled VM has the same average exposure but no BTC timing.)")
    lines.append("")

    # turnover / cost drag for SMA50 fill
    keep = sma_gate(btc["close"], 50)
    ww = w.mul(keep.shift(1).fillna(1.0), axis=0)
    turn = ww.diff().abs().sum(axis=1)
    oos_turn = turn.loc["2022-12-31":"2026-10-13"]
    lines.append("=== turnover (SMA50, OOS) ===")
    lines.append(f"rebalance/trade days with turnover>0: {int((oos_turn>1e-9).sum())} of {len(oos_turn)}; "
                 f"mean turnover on those days={oos_turn[oos_turn>1e-9].mean():.4f}; "
                 f"sum turnover={oos_turn.sum():.2f}; total fee at 0.30%/side={oos_turn.sum()*0.003*100:.1f}% "
                 f"(arithmetic sum of per-trade cost, not annualised)")
    lines.append("")

    text = "\n".join(lines)
    print(text)
    (HERE / "tradable_stdout.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
