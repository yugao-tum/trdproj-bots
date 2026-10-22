#!/usr/bin/env python3
"""Build the quant-005 replay dataset from cached public data.

For every closed Elon 48h event:
  - final post count in the market window (from xtracker createdAt)
  - early post count at decision fractions 20/30/50% of the window
  - first YES trade at/after each decision time and its delay (data-api fills)

Outputs (CSV, small):
  _cache/events.csv    one row per event
  _cache/trades.csv    one row per event x bracket x decision fraction
"""
import csv
import datetime as dt
import json
import os
import pathlib
import re

HERE = pathlib.Path(__file__).resolve()
CACHE = pathlib.Path(os.environ.get("Q005_CACHE", HERE.parents[2]
                                     / "notes/scheduler/scratch/H-quant-005/_cache"))
FRACS = (0.20, 0.30, 0.50)
MAX_DELAY_H = 4.0


def bracket_bounds(title):
    s = title.strip()
    m = re.fullmatch(r"<(\d+)", s)
    if m:
        return 0, int(m.group(1)) - 1
    m = re.fullmatch(r"(\d+)\+", s)
    if m:
        return int(m.group(1)), 10**9
    m = re.fullmatch(r"(\d+)-(\d+)", s)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"unparsed bracket {title!r}")


def iso(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def main():
    events = json.load(open(CACHE / "events.json", encoding="utf-8"))
    posts = [iso(p["createdAt"]) for p in json.load(open(CACHE / "posts.json", encoding="utf-8"))]
    posts.sort()

    ev_rows, tr_rows = [], []
    for e in events:
        start, end = iso(e["startTime"]), iso(e["endDate"])
        seconds = (end - start).total_seconds()
        assert 46 * 3600 <= seconds <= 50 * 3600, (e["slug"], seconds)  # 47h across DST
        n_final = sum(1 for t in posts if start <= t < end)

        # winner bracket(s)
        winners = []
        for m in e["markets"]:
            if json.loads(m["outcomePrices"])[0] == "1":
                winners.append(m["groupItemTitle"])
        if len(winners) != 1:
            raise ValueError(f"{e['slug']} winners={winners}")

        row = {
            "event_id": e["slug"],
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "n_final": n_final,
            "winner": winners[0],
            "n_brackets": len(e["markets"]),
        }
        for f in FRACS:
            d = start + dt.timedelta(seconds=seconds * f)
            early = sum(1 for t in posts if start <= t < d)
            row[f"early_{int(f*100)}"] = early
            row[f"decision_{int(f*100)}"] = d.isoformat()
        ev_rows.append(row)

        for m in e["markets"]:
            lo, hi = bracket_bounds(m["groupItemTitle"])
            path = CACHE / "trades" / f"{m['conditionId']}.json"
            trades = json.load(open(path, encoding="utf-8")) if path.exists() else []
            yes = sorted(((int(t["timestamp"]), t) for t in trades
                          if t.get("outcome") == "Yes" and t.get("price") is not None),
                         key=lambda x: x[0])
            for f in FRACS:
                d = start + dt.timedelta(seconds=seconds * f)
                ts = int(d.timestamp())
                nxt = next(((tt, t) for tt, t in yes if tt >= ts), None)
                rec = {
                    "event_id": e["slug"],
                    "window_start": start.isoformat(),
                    "window_end": end.isoformat(),
                    "frac": f"{int(f*100)}%",
                    "decision_ts": ts,
                    "bracket": m["groupItemTitle"],
                    "lo": lo,
                    "hi": hi,
                    "n_final": n_final,
                    "won": int(lo <= n_final <= hi),
                }
                if nxt and (nxt[0] - ts) <= MAX_DELAY_H * 3600:
                    rec.update({
                        "fill_ts": nxt[0],
                        "delay_h": round((nxt[0] - ts) / 3600, 3),
                        "price": float(nxt[1]["price"]),
                        "size": float(nxt[1].get("size") or 0),
                        "side": nxt[1].get("side", ""),
                    })
                tr_rows.append(rec)

    with open(CACHE / "events.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(ev_rows[0]))
        w.writeheader()
        w.writerows(ev_rows)
    fields = ["event_id", "window_start", "window_end", "frac", "decision_ts", "bracket", "lo", "hi",
              "n_final", "won", "fill_ts", "delay_h", "price", "size", "side"]
    with open(CACHE / "trades.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(tr_rows)
    print(f"events={len(ev_rows)} rows={len(tr_rows)}")
    for f in FRACS:
        k = int(f * 100)
        have = sum(1 for r in tr_rows if r["frac"] == f"{k}%" and "price" in r)
        print(f"{k}%: fills within {MAX_DELAY_H}h = {have}/{len(ev_rows)*10}")


if __name__ == "__main__":
    main()
