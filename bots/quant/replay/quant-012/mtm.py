#!/usr/bin/env python3
"""quant-012 replay: mark-to-market (MTM) daily drawdown.

replay.py reports a realised-only drawdown (open positions held at cost). GUIDE
section 9 asks for a daily/hourly mark including floating losses, so this script
re-marks every open bracket at the last data-api trade print at or before the
day's end. It reads only the raw JSON cached by replay.py (_cache/, gitignored)
and the portfolio rows in trades.csv, so it makes no network calls.

Definitions
  * position opened on the UTC day of its fill, cash reduced by port_cost;
  * settlement cash (100 shares x payoff) credited on the UTC day of settle_ts
    (window end + 48h, same convention as replay.py);
  * open position marked at shares x NO price, where NO price = last print
    price if outcome == No, else 1 - print price (YES-equivalent inversion);
  * if no print after the fill day, the entry NO price is carried forward;
  * equity = cash + marked value of open positions;
  * drawdown = (running peak - equity) / running peak, peak starts at 1,000.

Run: python3 mtm.py | tee mtm_output.txt
"""

import bisect
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
SLEEVE = 1000.0


def load_csv(name):
    with open(HERE / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_event_map():
    """(event_slug, bucket label) -> conditionId, from the Gamma cache."""
    out = {}
    for path in (CACHE / "gamma").glob("ev_*.json"):
        d = json.loads(path.read_text(encoding="utf-8"))
        ev = d[0] if isinstance(d, list) and d else d
        if not isinstance(ev, dict):
            continue
        for m in ev.get("markets", []):
            out[(ev.get("slug"), m.get("groupItemTitle"))] = m.get("conditionId")
    return out


def load_prints(cid):
    """All cached data-api prints for one conditionId, deduped, time-sorted."""
    seen = set()
    rows = []
    for path in sorted((CACHE / "trades").glob(f"{cid}__*.json")):
        for x in json.loads(path.read_text(encoding="utf-8")):
            key = (int(x["timestamp"]), x["outcome"], x["price"], x.get("size"))
            if key in seen:
                continue
            seen.add(key)
            price = float(x["price"])
            no_price = price if x["outcome"].lower() == "no" else 1.0 - price
            rows.append((int(x["timestamp"]), no_price))
    rows.sort()
    return rows


def main():
    trades = [r for r in load_csv("trades.csv") if int(float(r["port_shares"] or 0)) > 0]
    if not (CACHE / "trades").is_dir() or not any((CACHE / "trades").glob("*.json")):
        raise SystemExit("no _cache/trades: run `python3 replay.py` first (it downloads the raw prints)")
    emap = load_event_map()
    if not emap:
        raise SystemExit("no _cache/gamma events: run `python3 replay.py` first")
    print("=" * 78)
    print("quant-012 replay: mark-to-market daily drawdown (open positions at last print)")
    print("=" * 78)
    print(f"portfolio rows: {len(trades)}")

    series = {}
    missing = []
    for r in trades:
        cid = emap.get((r["event_slug"], r["bucket"]))
        if not cid:
            missing.append((r["event_slug"], r["bucket"]))
            continue
        if cid not in series:
            series[cid] = load_prints(cid)
        r["cid"] = cid

    if missing:
        raise SystemExit(f"{len(missing)} portfolio rows have no cached conditionId (e.g. {missing[:3]}); re-run replay.py")

    for r in trades:
        r["shares"] = float(r["port_shares"])
        r["cost"] = float(r["port_cost"])
        r["payoff"] = 0.0 if int(r["resolved_yes"]) else 1.0
        r["fill_ts"] = datetime.fromisoformat(r["fill_utc"]).timestamp()
        r["settle_ts"] = float(r["settle_ts"])
        r["entry_no"] = float(r["no_entry"])
    trades.sort(key=lambda r: r["fill_ts"])

    day0 = datetime.fromtimestamp(min(r["fill_ts"] for r in trades), timezone.utc).date()
    day1 = datetime.fromtimestamp(max(r["settle_ts"] for r in trades), timezone.utc).date()

    cash = SLEEVE
    opened, open_pos = set(), []
    eq_rows = []
    stale_marks = 0
    marked_rows = 0
    peak, max_dd, max_dd_usdt, dd_day = SLEEVE, 0.0, 0.0, ""
    d = day0
    while d <= day1:
        day_end = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc).timestamp()
        for i, r in enumerate(trades):
            if i not in opened and r["fill_ts"] <= day_end:
                cash -= r["cost"]
                open_pos.append((i, r))
                opened.add(i)
        for item in list(open_pos):
            if item[1]["settle_ts"] <= day_end:
                cash += item[1]["shares"] * item[1]["payoff"]
                open_pos.remove(item)
        mv = 0.0
        for i, r in open_pos:
            marks = series.get(r["cid"], [])
            ts = [x[0] for x in marks]
            j = bisect.bisect_right(ts, day_end) - 1
            if j >= 0 and marks[j][0] >= r["fill_ts"]:
                mark = marks[j][1]
                marked_rows += 1
            else:
                mark = r["entry_no"]
                stale_marks += 1
            mv += r["shares"] * mark
        equity = cash + mv
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100 if peak > 0 else 0.0
        if peak - equity > max_dd_usdt:
            max_dd_usdt = peak - equity
            max_dd = dd
            dd_day = d.isoformat()
        eq_rows.append((d.isoformat(), cash, mv, equity, dd))
        d += timedelta(days=1)

    with open(HERE / "equity_mtm.csv", "w", newline="", encoding="utf-8") as f:
        f.write("date,cash_usdt,open_mark_value_usdt,equity_mtm_usdt,drawdown_pct\n")
        for row in eq_rows:
            f.write(f"{row[0]},{row[1]:.6f},{row[2]:.6f},{row[3]:.6f},{row[4]:.6f}\n")

    final = eq_rows[-1][3]
    realised = sum(r["shares"] * (r["payoff"] - r["entry_no"]) - r["shares"] * 0.05 * r["entry_no"] * (1 - r["entry_no"]) for r in trades)
    print(f"days: {len(eq_rows)} ({day0}..{day1})")
    print(f"position-days marked from a post-fill print: {marked_rows}; carried at entry (no print): {stale_marks}")
    print(f"start equity = {SLEEVE:.2f}; final MTM equity = {final:.2f}; final realised PnL = {realised:+.2f}")
    print(f"MAX DRAWDOWN (daily, MTM incl. floating) = {max_dd:.2f}% ({max_dd_usdt:.2f} USDT), trough {dd_day}")
    print(f"wrote equity_mtm.csv ({len(eq_rows)} rows)")


if __name__ == "__main__":
    main()
