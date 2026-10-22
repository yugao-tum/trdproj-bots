#!/usr/bin/env python3
"""quant-002 replay self-check: recompute the numbers quoted in the entry.

Checks, all from files produced by fetch_data.py + backtest.py:
  1. results_variants.csv has exactly 16 rows (8 frozen rules x 2 fill prices).
  2. every one of the 16 net compound returns is < 0 at 0.30%/side.
  3. the 8 primary (next_open) compounds can be rebuilt from trades.csv alone.
  4. every fill price p0/p1 lies inside that day's [low, high] (tradable range).
  5. sleeve-level and 5,000-USDT account-level max drawdowns (daily mark).
  6. the entry's round-2 front-matter fields agree with the CSV.

Reads only local files; no network, no keys, no trading.
Run: python3 verify_results.py
"""
import pathlib
import re
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ENTRY = HERE.parents[1] / "entries" / "quant-002-tom-monday-oos-counterevidence.md"
FEE = 0.0030
FILL_NAMES = {"next_open": "next bar open", "first_hour_vwap": "first-hour VWAP"}

fails = []


def check(cond, msg):
    print(("OK   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


def sleeve_equity(sym, trades, fee=FEE):
    """Rebuild the single-coin sleeve equity, daily close mark, from trades.csv."""
    d = pd.read_csv(HERE / "_cache" / f"daily_{sym}.csv", parse_dates=["date"],
                    index_col="date").sort_index()
    idx = d.index
    close = d["close"].to_numpy(float)
    eq = np.full(len(idx), np.nan)
    cash, units = 1.0, 0.0
    def key(x):
        k = pd.Timestamp(x)
        return k.tz_localize("UTC") if k.tzinfo is None else k.tz_convert("UTC")
    entries = {key(t.entry): float(t.p0) for t in trades.itertuples()}
    exits = {key(t.exit): float(t.p1) for t in trades.itertuples()}
    for i, t in enumerate(idx):
        if t in exits and units > 0:
            cash = units * exits[t] * (1.0 - fee)
            units = 0.0
        if t in entries and units == 0:
            cash *= (1.0 - fee)
            units = cash / entries[t]
            cash = 0.0
        eq[i] = units * close[i] if units > 0 else cash
    s = pd.Series(eq, index=idx)
    return s


def max_dd(s, invest_share=1.0):
    """Max drawdown. invest_share=1 -> sleeve; 0.5 -> 2,500 sleeve + 2,500 cash."""
    e = (1.0 - invest_share) + invest_share * s
    return float((e / e.cummax() - 1.0).min())


def main():
    res = pd.read_csv(HERE / "results_variants.csv")
    tr = pd.read_csv(HERE / "trades.csv", parse_dates=["entry", "exit"])
    print(f"results rows={len(res)}  trades rows={len(tr)}")

    check(len(res) == 16, "16 results = 8 frozen rules x 2 fill conventions")
    check((res["compound_pct"] < 0).all(),
          f"all 16 net compounds < 0 (worst {res['compound_pct'].min():.2f}%, "
          f"best {res['compound_pct'].max():.2f}%)")

    primary = res[res.fill == "next_open"].set_index("version")
    check(len(primary) == 8, "8 primary next-open variants")
    for v, g in tr.groupby("version"):
        comp = (1.0 + g["net"]).prod() - 1.0
        stated = float(primary.loc[v, "compound_pct"]) / 100.0
        check(abs(comp - stated) < 1e-5,
              f"{v}: trades.csv recompound {comp*100:.4f}% == "
              f"results_variants {stated*100:.4f}%")

    # Calendar integrity: entry weekday / holding length must follow the frozen rule,
    # computed here independently of backtest.py's mask code.
    cal_bad = []
    for t in tr.itertuples():
        days = (pd.Timestamp(t.exit) - pd.Timestamp(t.entry)).days
        wd = pd.Timestamp(t.entry).dayofweek
        if t.version.endswith("mon_calendar_exact"):
            ok = wd == 0 and days == 1
        elif t.version.endswith("mon_orig_shift"):
            ok = wd == 1 and days == 1
        elif t.version.endswith("tom_calendar_exact"):
            ok = days == 4
        elif t.version.endswith("tom_orig_shift"):
            ok = days == 4
        else:
            ok = False
        if not ok:
            cal_bad.append((t.version, str(t.entry.date()), str(t.exit.date()), wd, days))
    check(not cal_bad, "calendar integrity: Monday trades span 1 day (Mon->Tue) or "
                       "Tue->Wed (off-by-one); TOM trades span 4 days"
                       + (f" (bad: {cal_bad[:3]})" if cal_bad else ""))
    check(tr["entry"].min() >= pd.Timestamp("2022-01-01")
          and tr["exit"].max() <= pd.Timestamp("2024-12-31"),
          f"all trades inside 2022-01-01..2024-12-31 "
          f"({tr['entry'].min().date()}..{tr['exit'].max().date()})")

    counts = tr.groupby("version").size()
    for v, n in counts.items():
        check(n >= 30, f"{v}: {n} independent windows >= 30")

    # Every quoted entry/exit price must be inside that day's low..high.
    bad = []
    for sym in ("BTC", "ETH"):
        d = pd.read_csv(HERE / "_cache" / f"daily_{sym}.csv", parse_dates=["date"],
                        index_col="date")
        sub = tr[tr.symbol == sym]
        for t in sub.itertuples():
            for px, day in ((t.p0, t.entry), (t.p1, t.exit)):
                key = pd.Timestamp(day)
                if key.tzinfo is None:
                    key = key.tz_localize("UTC")
                lo, hi = d.loc[key, "low"], d.loc[key, "high"]
                if not (lo - 1e-6 <= px <= hi + 1e-6):
                    bad.append((sym, day.date(), px, lo, hi))
    check(not bad, f"all {2*len(tr)} fill prices inside the daily [low, high] range"
                   + (f" (bad: {bad[:3]})" if bad else ""))

    # Drawdowns: sleeve (=field) and 5,000-account with a 2,500 sleeve.
    dd_rows = []
    for v, g in tr.groupby("version"):
        sym = "BTC" if v.startswith("BTC") else "ETH"
        s = sleeve_equity(sym, g)
        dd_rows.append({"version": v, "sleeve_dd_pct": max_dd(s, 1.0) * 100,
                        "account_dd_pct": max_dd(s, 0.5) * 100})
    ddf = pd.DataFrame(dd_rows).set_index("version")
    print("\n=== max drawdown (daily mark, 2022-2024, next-open, 0.30%/side) ===")
    print(ddf.round(2).to_string())
    for v, row in ddf.iterrows():
        stated = float(primary.loc[v, "max_dd_pct"])
        check(abs(row["sleeve_dd_pct"] - stated) < 0.01,
              f"{v}: rebuilt sleeve max DD {row['sleeve_dd_pct']:.2f}% == field {stated:.2f}%")

    # Entry front-matter must agree with the artefacts.
    text = ENTRY.read_text()
    fm = dict(re.findall(r"^([a-z_]+):\s*(.+)$", text.split("---")[1], flags=re.M))
    check(fm["id"] == "quant-002", "id unchanged: quant-002")
    check(fm["date"] == "2026-10-20", "date unchanged: 2026-10-20")
    check(fm["evidence"] == "回放", f"evidence={fm['evidence']}")
    check(fm["result"] == "负", f"result={fm['result']}")
    check(fm["window"] == "2022-01-01..2024-12-31", f"window={fm['window']}")
    check(int(fm["variants"]) == 16, f"variants={fm['variants']} == 16 results")
    check(fm["variants_ext"] == "0", f"variants_ext={fm['variants_ext']}")
    best = primary.loc["BTC_mon_calendar_exact"]
    check(abs(float(fm["contribution"].rstrip("%")) - best["contribution_pct"]) < 0.1,
          f"contribution {fm['contribution']} == {best['contribution_pct']:.2f}%")
    m = re.match(r"([0-9.]+)%", fm["max_dd"])
    check(m is not None and abs(float(m.group(1)) - abs(best["max_dd_pct"])) < 0.1,
          f"max_dd {fm['max_dd']} == |{best['max_dd_pct']:.2f}%| sleeve")

    print("\n=== account-level view (2,500 USDT sleeve + 2,500 cash) ===")
    print(f"BTC Monday exact: sleeve DD {ddf.loc['BTC_mon_calendar_exact','sleeve_dd_pct']:.2f}%, "
          f"account DD {ddf.loc['BTC_mon_calendar_exact','account_dd_pct']:.2f}%")
    print(f"worst account DD: {ddf['account_dd_pct'].min():.2f}% "
          f"({ddf['account_dd_pct'].idxmin()})")

    print(f"\n{'PASS' if not fails else 'FAIL'}: {len(fails)} failed checks")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
