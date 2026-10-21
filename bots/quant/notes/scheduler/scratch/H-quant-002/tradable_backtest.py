#!/usr/bin/env python3
"""quant-002 hardening: calendar windows on BTC/ETH at TRADABLE prices.

The old evidence (bots/quant/notes/xqt-migration/results.csv) fills at the daily
close.  This script re-runs the same frozen calendar rules with fills at the VWAP
of the first hourly bar (00:00-01:00 UTC) -- an actual traded price -- and at the
last hourly bar (23:00-24:00 UTC) as a fill-timing sensitivity.

Rules (no parameters fitted, calendar known in advance):
  TOM exact : last calendar day of month + days 1..3 of next month (contiguous).
  TOM shift : the original x-quant-trials off-by-one version -> days 1..4.
  Monday exact: Monday 00:00 UTC to Tuesday 00:00 UTC.
  Monday shift: Tuesday (the original off-by-one version).
Entry = first-bar VWAP on the first held day; exit = first-bar VWAP on the day
after the last held day.  Cost = fee per side on notional: net = (1+gross)*(1-fee)^2-1.
4 walk-forward OOS folds exactly as xqt-migration: 2022-12-31..2026-10-13.
No keys, no trading.  Reads only local public-data caches.

Outputs: tradable_results.csv, windows.csv, placebo.csv, tradable_stdout.txt
Run: python3 tradable_backtest.py
"""
import math, pathlib
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
SYMS = ["BTC", "ETH"]
FOLDS = [("2022-12-31", "2023-12-30"), ("2023-12-31", "2024-12-29"),
         ("2024-12-30", "2025-12-29"), ("2025-12-30", "2026-10-13")]
FEES = [0.0010, 0.0030]
FILL_COLS = {"first_vwap": "first-hour VWAP", "last_vwap": "last-hour VWAP"}


def load(sym):
    f = pd.read_csv(HERE / f"fills_{sym}.csv", index_col=0, parse_dates=True)
    return f.sort_index()


def hold_mask(index, kind, shift):
    if kind == "tom":
        m = (index.day == index.days_in_month) | (index.day <= 3)
    else:
        m = index.dayofweek == 0
    m = pd.Series(np.asarray(m, dtype=bool), index=index)
    if shift:
        m = m.shift(1, fill_value=False)
    return m


def block_frame(mask, fill_arr, index, fee):
    """Contiguous True runs -> one entry/exit round trip per run."""
    v = np.asarray(mask, dtype=bool)
    d = np.diff(np.concatenate(([0], v.view(np.int8), [0])))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0] - 1
    ok = ends + 1 < len(v)
    starts, ends = starts[ok], ends[ok]
    p0 = fill_arr[starts]
    p1 = fill_arr[ends + 1]
    good = np.isfinite(p0) & np.isfinite(p1) & (p0 > 0)
    starts, ends = starts[good], ends[good]
    p0, p1 = p0[good], p1[good]
    gross = p1 / p0 - 1.0
    net = (1.0 + gross) * (1.0 - fee) ** 2 - 1.0
    out = pd.DataFrame({"entry": index[starts], "exit": index[ends + 1],
                        "gross": gross, "net": net})
    return out.set_index("exit")


def daily_close_frame(mask, close, fee):
    """Old close-fill accounting, kept only to validate against results.csv."""
    m = mask.astype(float)
    r = close.pct_change().fillna(0.0)
    turn = m.diff().abs().fillna(m.abs())
    net = m * r - turn * fee
    return net


def metrics(ret, mask, index, folds):
    rets, dds, shs, path, expo, ns = [], [], [], [], [], []
    for a, b in folds:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        r = ret.loc[a:b]
        eq = (1 + r).cumprod()
        rets.append(eq.iloc[-1] - 1 if len(eq) else np.nan)
        dds.append((eq / eq.cummax() - 1).min() if len(eq) else np.nan)
        shs.append(r.mean() / r.std() * np.sqrt(365) if len(r) > 1 and r.std() > 0 else np.nan)
        path.append(r)
        expo.append(mask.loc[a:b].mean())
        ns.append(len(r))
    p = (1 + pd.concat(path)).cumprod()
    years = sum((pd.Timestamp(b) - pd.Timestamp(a)).days + 1 for a, b in folds) / 365.0
    comp = np.prod([1 + r for r in rets]) - 1
    return {"compound_pct": comp * 100,
            "cagr_pct": ((1 + comp) ** (1 / years) - 1) * 100,
            "worst_fold_dd_pct": np.nanmin(dds) * 100,
            "path_dd_pct": (p / p.cummax() - 1).min() * 100,
            "mean_sharpe": float(np.nanmean(shs)),
            "folds_pos": int(sum(r > 0 for r in rets)),
            "avg_exposure": float(np.mean(expo)),
            "n_windows": int(sum(ns)),
            "fold_rets_pct": [round(r * 100, 1) for r in rets]}


def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delt = d * c
        h *= delt
        if abs(delt - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1 - x) / b


def t_p_one_sided(t, df):
    if df <= 0 or not np.isfinite(t):
        return float("nan")
    x = df / (df + t * t)
    p2 = betai(df / 2, 0.5, x)
    return p2 / 2 if t > 0 else 1 - p2 / 2


def window_stats(frame):
    x = np.asarray(frame["net"])
    g = np.asarray(frame["gross"])
    n = len(x)
    if n < 2:
        return {"n": n}
    t = x.mean() / (x.std(ddof=1) / math.sqrt(n))
    tg = g.mean() / (g.std(ddof=1) / math.sqrt(n))
    rng = np.random.default_rng(42)
    bm = np.array([rng.choice(x, n, replace=True).mean() for _ in range(10000)])
    return {"n": n, "mean_net_pct": x.mean() * 100, "median_net_pct": np.median(x) * 100,
            "win_rate_pct": (x > 0).mean() * 100, "t_net": t,
            "p_one_sided_net": t_p_one_sided(t, n - 1),
            "ci95_net_pct": (np.percentile(bm, 2.5) * 100, np.percentile(bm, 97.5) * 100),
            "mean_gross_pct": g.mean() * 100, "t_gross": tg,
            "p_one_sided_gross": t_p_one_sided(tg, n - 1),
            "breakeven_fee_per_side_pct": max(g.mean(), -1) * 100 / 2}


def compound_mask(mask, fill_arr, index, fee):
    fr = block_frame(mask, fill_arr, index, fee)
    return (1 + fr["gross"]).prod() - 1, (1 + fr["net"]).prod() - 1


def oos_index(index):
    m = np.zeros(len(index), dtype=bool)
    for a, b in FOLDS:
        m |= (index >= pd.Timestamp(a)) & (index <= pd.Timestamp(b))
    return m


def placebo_monday(index, rng, weekdays_only=False):
    mask = np.zeros(len(index), dtype=bool)
    cal = index.isocalendar()
    keys = list(zip(cal["year"].values, cal["week"].values))
    groups = {}
    for pos, k in enumerate(keys):
        groups.setdefault(k, []).append(pos)
    dow = index.dayofweek.values
    for pos in groups.values():
        pos = np.asarray(pos)
        if weekdays_only:
            pos = pos[dow[pos] <= 4]
        if len(pos):
            mask[pos[rng.integers(0, len(pos))]] = True
    return pd.Series(mask, index=index)


def placebo_tom(index, rng):
    mask = np.zeros(len(index), dtype=bool)
    groups = {}
    for pos, (y, m) in enumerate(zip(index.year, index.month)):
        groups.setdefault((y, m), []).append(pos)
    for pos in groups.values():
        if len(pos) >= 4:
            s = rng.integers(0, len(pos) - 3)
            mask[pos[s:s + 4]] = True
    return pd.Series(mask, index=index)


def placebo_test(kind, idx, fill_arr, fee, actual_gross, actual_net, B=1000,
                 weekdays_only=False):
    rng = np.random.default_rng(20261021)
    oos = oos_index(idx)
    gs, ns = [], []
    for _ in range(B):
        m = placebo_monday(idx, rng, weekdays_only) if kind == "mon" else placebo_tom(idx, rng)
        m = pd.Series(np.asarray(m) & oos, index=idx)
        g, n = compound_mask(m, fill_arr, idx, fee)
        gs.append(g)
        ns.append(n)
    gs, ns = np.array(gs), np.array(ns)
    return {"n_placebo": B,
            "actual_gross_pct": actual_gross * 100,
            "placebo_gross_p50_pct": np.median(gs) * 100,
            "placebo_gross_p5_pct": np.percentile(gs, 5) * 100,
            "placebo_gross_p95_pct": np.percentile(gs, 95) * 100,
            "p_placebo_gross_ge_actual": float((gs >= actual_gross).mean()),
            "actual_net_pct": actual_net * 100,
            "placebo_net_p50_pct": np.median(ns) * 100,
            "p_placebo_net_ge_actual": float((ns >= actual_net).mean())}


def main():
    lines = []
    lines.append("quant-002 tradable-price backtest (Binance 1h first/last-bar VWAP)")
    lines.append("No parameters fitted; 4 chronological OOS folds; long-only spot, no leverage.")
    lines.append("")
    panels = {s: load(s) for s in SYMS}
    idx = panels["BTC"].index.intersection(panels["ETH"].index)
    panels = {s: panels[s].reindex(idx) for s in SYMS}
    lines.append(f"data: {idx.min().date()}..{idx.max().date()}, {len(idx)} daily rows, "
                 f"BTC/ETH")
    lines.append("")

    # ---- 1. validate daily close from 1h bars against the old results.csv ----
    old = pd.read_csv(HERE.parent.parent.parent / "xqt-migration" / "results.csv")
    lines.append("=== VALIDATION: close-fill from 1h-derived daily close vs xqt-migration/results.csv ===")
    lines.append("(this proves the new 1h data reproduces the old daily-close evidence)")
    val_rows = []
    for sym in SYMS:
        close = panels[sym]["day_close"]
        for kind in ("tom", "mon"):
            for sh in (True, False):
                name = f"M3_{sym}_{kind}_{'orig_shift' if sh else 'calendar_exact'}"
                mask = hold_mask(idx, kind, sh)
                for fee in FEES:
                    net = daily_close_frame(mask, close, fee)
                    r = metrics(net, mask, idx, FOLDS)
                    row = old[(old.name == name) & (np.isclose(old.fee_side, fee))].iloc[0]
                    val_rows.append({"name": name, "fee_side": fee,
                                     "new_compound_pct": round(r["compound_pct"], 4),
                                     "old_compound_pct": round(row.compound_pct, 4),
                                     "new_path_dd_pct": round(r["path_dd_pct"], 4),
                                     "old_path_dd_pct": round(row.path_dd_pct, 4),
                                     "match": (abs(r["compound_pct"] - row.compound_pct) < 0.02
                                               and abs(r["path_dd_pct"] - row.path_dd_pct) < 0.02)})
    val = pd.DataFrame(val_rows)
    lines.append(val.to_string(index=False))
    lines.append(f"all match: {bool(val['match'].all())}")

    # ---- 2. tradable fills ----
    rows, win_rows, placebo_rows = [], [], []
    for sym in SYMS:
        for kind in ("tom", "mon"):
            for sh in (True, False):
                version = "tom" if kind == "tom" else "mon"
                label = f"{sym}_{version}_{'orig_shift' if sh else 'calendar_exact'}"
                mask = hold_mask(idx, kind, sh)
                for fill_col in ("first_vwap", "last_vwap"):
                    fill_arr = panels[sym][fill_col].values
                    for fee in FEES:
                        fr = block_frame(mask, fill_arr, idx, fee)
                        r = metrics(fr["net"], mask, idx, FOLDS)
                        rows.append({"version": label, "fill": fill_col,
                                     "fill_desc": FILL_COLS[fill_col], "fee_side": fee, **r})
                # window stats + placebo only at 0.30% and first-hour VWAP
                fr = block_frame(mask, panels[sym]["first_vwap"].values, idx, 0.0030)
                fr_oos = fr[(fr.index >= pd.Timestamp(FOLDS[0][0])) &
                            (fr.index <= pd.Timestamp(FOLDS[-1][1]))]
                ws = window_stats(fr_oos)
                win_rows.append({"version": label, **ws})
                g, n = compound_mask(mask & pd.Series(oos_index(idx), index=idx),
                                     panels[sym]["first_vwap"].values, idx, 0.0030)
                if kind == "mon":
                    for setname, wd in (("all7", False), ("monfri", True)):
                        pl = placebo_test(kind, idx, panels[sym]["first_vwap"].values,
                                          0.0030, g, n, weekdays_only=wd)
                        placebo_rows.append({"version": label, "kind": kind,
                                             "placebo_set": setname, **pl})
                else:
                    pl = placebo_test(kind, idx, panels[sym]["first_vwap"].values, 0.0030, g, n)
                    placebo_rows.append({"version": label, "kind": kind,
                                         "placebo_set": "rand4d", **pl})
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "tradable_results.csv", index=False, float_format="%.4f")
    win = pd.DataFrame(win_rows)
    win.to_csv(HERE / "windows.csv", index=False, float_format="%.4f")
    pla = pd.DataFrame(placebo_rows)
    pla.to_csv(HERE / "placebo.csv", index=False, float_format="%.4f")

    lines.append("")
    lines.append("=== TRADABLE FILLS, 4 OOS folds, 0.30%/side (first-hour VWAP) ===")
    show = res[(res.fee_side == 0.0030) & (res.fill == "first_vwap")][
        ["version", "n_windows", "compound_pct", "cagr_pct", "worst_fold_dd_pct",
         "path_dd_pct", "avg_exposure", "folds_pos", "fold_rets_pct"]].round(2)
    lines.append(show.to_string(index=False))
    lines.append("")
    lines.append("=== TRADABLE FILLS, 4 OOS folds, 0.10%/side (first-hour VWAP) ===")
    show1 = res[(res.fee_side == 0.0010) & (res.fill == "first_vwap")][
        ["version", "n_windows", "compound_pct", "cagr_pct", "worst_fold_dd_pct",
         "path_dd_pct", "avg_exposure", "folds_pos"]].round(2)
    lines.append(show1.to_string(index=False))
    lines.append("")
    lines.append("=== FILL-TIMING SENSITIVITY at 0.30%/side (first vs last hourly VWAP) ===")
    piv = res[res.fee_side == 0.0030].pivot_table(
        index="version", columns="fill", values="compound_pct").round(2)
    lines.append(piv.to_string())
    lines.append("")
    lines.append("=== PER-WINDOW STATS (first-hour VWAP, 0.30%/side, OOS) ===")
    wshow = win.round(3).to_string(index=False)
    lines.append(wshow)
    lines.append("")
    lines.append("=== PLACEBO (same exposure/turnover, random window; 1,000 draws, first-hour VWAP, 0.30%) ===")
    ps = pla.round(3).to_string(index=False)
    lines.append(ps)

    text = "\n".join(lines)
    print(text)
    (HERE / "tradable_stdout.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
