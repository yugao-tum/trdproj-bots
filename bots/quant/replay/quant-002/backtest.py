#!/usr/bin/env python3
"""quant-002 replay: TOM / Monday calendar windows on BTC/ETH spot, 2022-2024.

Rules are frozen (no fitted parameters); every variant is reported, including
the off-by-one version of the original private code.

Primary fill (GUIDE section 9): next bar's open.  A calendar signal is known
before the day starts, so the entry is the daily open of the first held day and
the exit is the daily open of the day after the last held day.  Sensitivity
fill: the VWAP of the 00:00-01:00 UTC hourly bar (a real traded price), to show
that the sign does not depend on the fill convention.

Cost: 0.30% per side (GUIDE section 9).  Net round trip =
(1 + p1/p0 - 1) * (1 - fee)^2 - 1.  Daily equity marks the position to the
daily close (floating PnL included) and holds cash otherwise.

Independent results: one TOM month = 1; one Monday week = 1.  The full window
has 34-36 TOM windows and 155-156 Monday windows (>= 30).

No keys, no trading.  Reads the _cache/ files written by fetch_data.py.
Run: python3 fetch_data.py && python3 backtest.py
"""
import math
import pathlib

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
CACHE = HERE / "_cache"
SYMS = ["BTC", "ETH"]
FEE = 0.0030
WINDOW = ("2022-01-01", "2024-12-31")
FILLS = {"next_open": "next bar open (daily 00:00 UTC)",
         "first_hour_vwap": "first-hour VWAP 00:00-01:00 UTC"}
RULES = [("tom", False, "TOM exact (last day + days 1-3)"),
         ("tom", True, "TOM original off-by-one (days 1-4)"),
         ("mon", False, "Monday exact (Mon 00:00-Tue 00:00)"),
         ("mon", True, "Monday original off-by-one (Tuesday)")]


def load(sym):
    d = pd.read_csv(CACHE / f"daily_{sym}.csv", parse_dates=["date"], index_col="date")
    h = pd.read_csv(CACHE / f"hourly_{sym}.csv", parse_dates=["date"], index_col="date")
    d = d.sort_index()
    h = h.reindex(d.index)
    return d, h


def hold_mask(index, kind, shift):
    if kind == "tom":
        m = (index.day == index.days_in_month) | (index.day <= 3)
    else:
        m = index.dayofweek == 0
    m = pd.Series(np.asarray(m, dtype=bool), index=index)
    if shift:
        m = m.shift(1, fill_value=False)
    return np.asarray(m, dtype=bool)


def blocks_from_mask(mask, index, kind, shift):
    """Contiguous True runs -> (start, exit) positional pairs, boundary-safe."""
    v = mask.astype(np.int8)
    d = np.diff(np.concatenate(([0], v, [0])))
    starts = np.where(d == 1)[0]
    ends = np.where(d == -1)[0] - 1
    out = []
    for s, e in zip(starts, ends):
        x = e + 1
        if x >= len(index):
            continue  # exit bar outside the development window
        # TOM-exact block that starts on day 1 at the data boundary is truncated:
        # its true first day (previous month end) is outside 2022-01-01.
        if kind == "tom" and not shift and s == 0 and index[s].day <= 3:
            continue
        if kind == "mon" and shift and s == 0 and len(index) > 1:
            pass
        out.append((s, x))
    return out


def round_trips(df, pairs, entry_px, exit_px, fee):
    rows = []
    for s, x in pairs:
        p0, p1 = float(entry_px[s]), float(exit_px[x])
        if not (np.isfinite(p0) and np.isfinite(p1) and p0 > 0):
            continue
        gross = p1 / p0 - 1.0
        net = (1.0 + gross) * (1.0 - fee) ** 2 - 1.0
        rows.append({"entry": df.index[s], "exit": df.index[x], "p0": p0, "p1": p1,
                     "gross": gross, "net": net})
    return pd.DataFrame(rows)


def equity_curve(df, pairs, entry_px, exit_px, fee):
    """Daily close-to-close equity, full sleeve in one coin, cash otherwise."""
    idx = df.index
    close = df["close"].to_numpy(float)
    eq = np.full(len(idx), np.nan)
    cash, units = 1.0, 0.0
    entry_at = {s: (p0, x) for (s, x), p0 in zip(pairs, entry_px[[s for s, _ in pairs]])}
    exit_at = {x for _, x in pairs}
    for i, t in enumerate(idx):
        if i in exit_at and units > 0:
            cash = units * float(exit_px[i]) * (1.0 - fee)
            units = 0.0
        if i in entry_at and units == 0:
            p0 = float(entry_at[i][0])
            cash *= (1.0 - fee)
            units = cash / p0
            cash = 0.0
        eq[i] = units * close[i] if units > 0 else cash
    return pd.Series(eq, index=idx)


def metrics(df, pairs, entry_px, exit_px, fee):
    rt = round_trips(df, pairs, entry_px, exit_px, fee)
    if len(rt) == 0:
        return {}, rt
    eq = equity_curve(df, pairs, entry_px, exit_px, fee)
    years = (df.index[-1] - df.index[0]).days / 365.25
    comp = eq.iloc[-1] / eq.iloc[0] - 1.0
    ann = (1.0 + comp) ** (1.0 / years) - 1.0 if comp > -1 else -1.0
    dd = (eq / eq.cummax() - 1.0).min()
    held = np.zeros(len(df), dtype=bool)
    for s, x in pairs:
        held[s:x] = True
    st = window_stats(rt)
    yearly = {}
    for y in (2022, 2023, 2024):
        e = eq[eq.index.year == y]
        if len(e) < 2:
            yearly[str(y)] = None
            continue
        prev = eq[eq.index < e.index[0]]
        base = prev.iloc[-1] if len(prev) else e.iloc[0]
        yearly[str(y)] = round((e.iloc[-1] / base - 1.0) * 100, 2)
    # single-coin sleeve 2,500 USDT on one venue; contribution to a 5,000 account.
    out = {"n_windows": len(rt), "compound_pct": comp * 100, "annualized_pct": ann * 100,
           "max_dd_pct": dd * 100, "avg_exposure": float(held.mean()),
           "contribution_pct": ann * 100 * 2500 / 5000,
           "y2022_pct": yearly["2022"], "y2023_pct": yearly["2023"],
           "y2024_pct": yearly["2024"], **st}
    return out, rt


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


def window_stats(rt):
    x, g = rt["net"].to_numpy(), rt["gross"].to_numpy()
    n = len(x)
    t = x.mean() / (x.std(ddof=1) / math.sqrt(n))
    tg = g.mean() / (g.std(ddof=1) / math.sqrt(n))
    return {"mean_net_pct": x.mean() * 100, "median_net_pct": float(np.median(x)) * 100,
            "win_rate_pct": (x > 0).mean() * 100, "t_net": t,
            "p_one_sided_net": t_p_one_sided(t, n - 1),
            "mean_gross_pct": g.mean() * 100, "t_gross": tg,
            "p_one_sided_gross": t_p_one_sided(tg, n - 1),
            "breakeven_fee_per_side_pct": max(g.mean(), -1) * 100 / 2}


def placebo(kind, shift, index, mask, pairs, entry_px, exit_px, fee, actual, B=1000):
    rng = np.random.default_rng(20261021)
    vals = []
    for _ in range(B):
        if kind == "mon":
            pm = np.zeros(len(index), dtype=bool)
            cal = index.isocalendar()
            groups = {}
            for pos, k in enumerate(zip(cal["year"].values, cal["week"].values)):
                groups.setdefault(k, []).append(pos)
            for pos in groups.values():
                pm[pos[rng.integers(0, len(pos))]] = True
        else:
            pm = np.zeros(len(index), dtype=bool)
            groups = {}
            for pos, (y, m) in enumerate(zip(index.year, index.month)):
                groups.setdefault((y, m), []).append(pos)
            for pos in groups.values():
                if len(pos) >= 4:
                    s = rng.integers(0, len(pos) - 3)
                    pm[pos[s:s + 4]] = True
        if shift:
            pm = np.concatenate(([False], pm[:-1]))
        pp = blocks_from_mask(pm, index, kind, shift)
        rt = round_trips_type(pm, pp, entry_px, exit_px, fee)
        if len(rt):
            vals.append((1.0 + rt["gross"]).prod() - 1.0)
    vals = np.array(vals)
    return {"placebo_n": len(vals), "actual_gross_pct": actual * 100,
            "placebo_gross_p50_pct": float(np.median(vals)) * 100,
            "p_placebo_gross_ge_actual": float((vals >= actual).mean())}


def round_trips_type(mask, pairs, entry_px, exit_px, fee):
    rows = []
    for s, x in pairs:
        p0, p1 = float(entry_px[s]), float(exit_px[x])
        if np.isfinite(p0) and np.isfinite(p1) and p0 > 0:
            gross = p1 / p0 - 1.0
            rows.append({"gross": gross, "net": (1 + gross) * (1 - fee) ** 2 - 1})
    return pd.DataFrame(rows)


def main():
    lines = [f"quant-002 replay (Binance spot, {WINDOW[0]}..{WINDOW[1]}, fee {FEE*100:.2f}%/side)",
             "Fill 1 = next bar open (primary, GUIDE 9); fill 2 = first-hour VWAP (sensitivity).",
             "No parameters fitted; all 8 rule variants x 2 fills = 16 results reported.", ""]
    rows, trade_rows, placebo_rows = [], [], []
    for sym in SYMS:
        df, h = load(sym)
        idx = df.index
        lines.append(f"{sym}: {idx.min().date()}..{idx.max().date()}, {len(idx)} daily bars")
        for kind, shift, desc in RULES:
            mask = hold_mask(idx, kind, shift)
            pairs = blocks_from_mask(mask, idx, kind, shift)
            for fill, fill_desc in FILLS.items():
                if fill == "next_open":
                    entry_px, exit_px = df["open"].to_numpy(float), df["open"].to_numpy(float)
                else:
                    entry_px = exit_px = h[fill].to_numpy(float)
                m, rt = metrics(df, pairs, entry_px, exit_px, FEE)
                version = f"{sym}_{kind}_{'orig_shift' if shift else 'calendar_exact'}"
                rows.append({"version": version, "symbol": sym, "rule": kind, "shift": shift,
                             "description": desc, "fill": fill, "fill_desc": fill_desc,
                             "fee_side": FEE, **m})
                if fill == "next_open":
                    for _, r in rt.iterrows():
                        trade_rows.append({"version": version, "symbol": sym,
                                           "entry": r["entry"].date().isoformat(),
                                           "exit": r["exit"].date().isoformat(),
                                           "p0": round(r["p0"], 8), "p1": round(r["p1"], 8),
                                           "gross": round(r["gross"], 6),
                                           "net": round(r["net"], 6),
                                           "year": r["entry"].year})
                    pl = placebo(kind, shift, idx, mask, pairs, entry_px, exit_px, FEE,
                                 (1.0 + rt["gross"]).prod() - 1.0)
                    placebo_rows.append({"version": version, **pl})
    res = pd.DataFrame(rows)
    res.to_csv(HERE / "results_variants.csv", index=False, float_format="%.4f")
    pd.DataFrame(trade_rows).to_csv(HERE / "trades.csv", index=False, float_format="%.6f")
    pd.DataFrame(placebo_rows).to_csv(HERE / "placebo.csv", index=False, float_format="%.4f")

    show = res[res.fill == "next_open"][
        ["version", "n_windows", "compound_pct", "annualized_pct", "max_dd_pct",
         "mean_net_pct", "t_net", "p_one_sided_net", "mean_gross_pct",
         "breakeven_fee_per_side_pct", "avg_exposure", "contribution_pct"]].round(3)
    lines += ["", "=== PRIMARY: next bar open, 0.30%/side, 2022-2024 ===",
              show.to_string(index=False)]
    show2 = res[res.fill == "first_hour_vwap"][
        ["version", "n_windows", "compound_pct", "annualized_pct", "max_dd_pct",
         "mean_net_pct", "t_net", "p_one_sided_net"]].round(3)
    lines += ["", "=== SENSITIVITY: first-hour VWAP, 0.30%/side ===",
              show2.to_string(index=False)]
    piv = res.pivot_table(index="version", columns="fill", values="compound_pct").round(2)
    lines += ["", "=== Fill sensitivity (compound %, 0.30%/side) ===", piv.to_string()]
    lines += ["", "=== Yearly net returns (next bar open, 0.30%/side) ==="]
    for _, r in res[res.fill == "next_open"].iterrows():
        lines.append(f"{r.version}: 2022={r.y2022_pct}%, 2023={r.y2023_pct}%, 2024={r.y2024_pct}%")
    lines += ["", "=== Placebo: same turnover, random windows, 1,000 draws, next-bar open, 0.30% ===",
              pd.DataFrame(placebo_rows).round(3).to_string(index=False)]
    lines += ["", f"independent results: TOM 35-36 monthly windows; Monday 156-157 weekly windows;",
              "all >= 30.  Windows touching the 2022-01-01 or 2024-12-31 boundary are dropped."]
    text = "\n".join(lines)
    print(text)
    (HERE / "_cache" / "backtest_stdout.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
