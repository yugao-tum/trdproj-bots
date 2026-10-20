#!/usr/bin/env python3
"""quant-020 pre-registered FORWARD check.

PRE-DECLARED DESIGN (written before the window resolves)
=======================================================
Reuse, do not modify, ../q020-oos/q020_oos.py logic:
  * same frozen rule: 0.40 <= p_24h <= 0.55, buy YES;
  * p_24h = last data-api YES trade in [endDate-72h, endDate-24h];
  * entry ask = p_24h + 0.01 (1 cent half-spread);
  * fee/share = 0.05 * ask * (1 - ask);
  * net P&L/share = payout(1 or 0) - ask - fee;
  * one Gamma event = one company-quarter = one independent result.

Window
  * ONLY events with endDate in [2026-10-21T00:00:00Z, 2026-10-26T00:00:00Z).
  * Both open and closed Gamma earnings events are enumerated; same company+date
    (GAAP vs non-GAAP) is collapsed to one result, as in q020_oos.py.

When to run
  * Until every window event is resolved, this script prints counts and PENDING
    and never prints a PASS/FAIL verdict.
  * After all resolve it applies the entry's frozen holdout criterion:
    n < 30 -> INSUFFICIENT; median net <= 0 or YES rate <= mean entry -> FAIL;
    otherwise PASS.

All endpoints are free and keyless. Downloads are cached under _cache/ (gitignored).
"""

import argparse
import datetime as dt
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OOS_DIR = HERE.parent / "q020-oos"
SPEC = importlib.util.spec_from_file_location("q020_oos", OOS_DIR / "q020_oos.py")
OOS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OOS)

OOS.CACHE = HERE / "_cache"
OOS.REFRESH = False

GAMMA = OOS.GAMMA
WINDOW_START = dt.datetime(2026, 10, 21, 0, 0, tzinfo=dt.timezone.utc)
WINDOW_END = dt.datetime(2026, 10, 26, 0, 0, tzinfo=dt.timezone.utc)
MIN_EVENTS = 30


def parse_iso(value):
    return OOS.parse_iso(value)


def in_window(value):
    return WINDOW_START <= parse_iso(value) < WINDOW_END


def fetch_events(closed):
    """Ascending endDate; stop at WINDOW_END. Keep only window events."""
    events, offset = [], 0
    while True:
        page = OOS.get_json(
            GAMMA + "/events",
            {
                "tag_slug": "earnings",
                "limit": 100,
                "offset": offset,
                "closed": "true" if closed else "false",
                "order": "endDate",
                "ascending": "true",
            },
        )
        if not isinstance(page, list) or not page:
            break
        for event in page:
            if not OOS.is_earnings_event(event):
                continue
            end = parse_iso(event["endDate"])
            if end >= WINDOW_END:
                return events
            if end >= WINDOW_START:
                events.append(event)
        offset += 100
        if len(page) < 100:
            break
    return events


def dedupe(events):
    events.sort(key=lambda e: (e["endDate"], e["slug"]))
    seen, out, dropped = set(), [], []
    for event in events:
        parts = event["slug"].split("-")
        company = parts[1] if parts[0] == "will" and len(parts) > 1 else parts[0]
        key = (company, event["endDate"][:10])
        if key in seen:
            dropped.append(event["slug"])
            continue
        seen.add(key)
        out.append(event)
    return out, dropped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    OOS.REFRESH = args.refresh

    print("quant-020 pre-registered forward check")
    print("window: [%s, %s)  frozen band=[%.2f,%.2f] fee_rate=%.2f half_spread=%.2f"
          % (WINDOW_START.isoformat().replace("+00:00", "Z"),
             WINDOW_END.isoformat().replace("+00:00", "Z"),
             OOS.BAND_LO, OOS.BAND_HI, OOS.FEE_RATE, OOS.HALF_SPREAD))

    raw = fetch_events(closed=True) + fetch_events(closed=False)
    events, dropped = dedupe(raw)
    print("window events after dedupe: %d" % len(events))
    if dropped:
        print("dropped same company+date duplicates: %s" % ", ".join(dropped))
    if not events:
        print("resolved: 0/%d; unresolved: 0" % len(events))
        print("PENDING (no window events found; nothing to evaluate)")
        return

    rows, unresolved = [], []
    for event in events:
        market = event["markets"][0]
        end_dt = parse_iso(event["endDate"])
        outcome = OOS.market_outcome(market)
        condition_id = market.get("conditionId") or ""

        row = {
            "slug": event["slug"],
            "endDate": event["endDate"],
            "week": "%04d-W%02d" % end_dt.isocalendar()[:2],
            "split": "forward",
            "y": outcome,
            "p24": None,
            "ask": None,
            "fee": None,
            "net": None,
            "in_band": False,
            "capital_days": None,
        }
        if condition_id:
            trades = OOS.fetch_window_trades(condition_id, end_dt).get("trades", [])
            p24, ts24 = OOS.last_yes_price(
                trades,
                OOS.epoch(end_dt - dt.timedelta(hours=24)),
                OOS.epoch(end_dt - dt.timedelta(hours=72)),
            )
            if p24 is not None:
                ask = min(1.0, p24 + OOS.HALF_SPREAD)
                fee = OOS.trade_cost(ask)
                row.update(
                    p24=p24,
                    ask=ask,
                    fee=fee,
                    net=outcome - ask - fee if outcome is not None else None,
                    in_band=(OOS.BAND_LO <= p24 <= OOS.BAND_HI),
                    capital_days=(
                        end_dt
                        - dt.datetime.fromtimestamp(ts24, dt.timezone.utc)
                    ).total_seconds() / 86400.0,
                )
        if outcome is None:
            unresolved.append(event["slug"])
        rows.append(row)
        print("  %s | %s | y=%s | p24=%s | in_band=%s"
              % (event["slug"], event["endDate"],
                 "?" if outcome is None else outcome,
                 "NA" if row["p24"] is None else "%.4f" % row["p24"],
                 row["in_band"]))

    resolved = [r for r in rows if r["y"] is not None]
    priced = [r for r in rows if r["p24"] is not None]
    band_all = [r for r in rows if r["in_band"]]
    band_resolved = [r for r in rows if r["in_band"] and r["y"] is not None]
    print("\ncounts: window=%d resolved=%d unresolved=%d priced=%d in_band=%d in_band_resolved=%d"
          % (len(rows), len(resolved), len(rows) - len(resolved), len(priced),
             len(band_all), len(band_resolved)))

    if unresolved:
        print("PENDING (%d/%d window events unresolved; no verdict until all resolve)"
              % (len(unresolved), len(rows)))
        return

    if len(band_resolved) < MIN_EVENTS:
        print("INSUFFICIENT (in-band resolved events %d < %d)"
              % (len(band_resolved), MIN_EVENTS))
        return

    metrics = OOS.metrics(band_resolved)
    lo, hi = OOS.bootstrap_mean_ci(band_resolved)
    print("RESULT: %s" % OOS.fmt_m(metrics))
    print("bootstrap 95%% CI mean net/share: [%+.4f, %+.4f]" % (lo, hi))
    cond_median = metrics["median_net"] <= 0
    cond_yes = metrics["yes_rate"] <= metrics["mean_ask"]
    verdict = "FAIL" if (cond_median or cond_yes) else "PASS"
    print("VERDICT: %s (median net/share %+.4f %s 0; YES rate %.4f %s mean entry price %.4f)"
          % (verdict, metrics["median_net"], "<=" if cond_median else ">",
             metrics["yes_rate"], "<=" if cond_yes else ">", metrics["mean_ask"]))


if __name__ == "__main__":
    main()
