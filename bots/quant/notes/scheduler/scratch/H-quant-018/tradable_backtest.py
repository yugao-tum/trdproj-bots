#!/usr/bin/env python3
"""quant-018 H-quant-018: historical TRADABLE-price NO backtest.

PRE-DECLARED RULE (same as the entry, no tuning here)
  * Only Bab el-Mandeb.
  * Decision time T = Monday 00:00 UTC of the event week.
  * Model p_i = Laplace((k_i+1)/(12+n)) from the last 12 complete Mon-Sun
    PortWatch weeks whose Monday is strictly before T.
  * Market entry price = last data-api trade in [T-24h, T], mapped to YES
    (YES print p, NO print 1-p).  If several prints share the last second,
    the highest YES price at that second is used (worst for a NO buyer).
    No trade in the window => no fill.
  * Buy NO only if p_yes >= p_model + half_spread + 0.01 (safety cushion).
  * Base half_spread = 0.01; stress = 0.05, and the trigger is recomputed
    under the stress cost (not applied ex post to the base fills).
  * Cost = 1 - p_yes + half_spread; fee = shares * rate * p * (1-p), with
    rate read from Gamma feesEnabled/feeSchedule (all observed 0).
  * Payoff = 1 if the bucket did NOT resolve YES, else 0.
  * One share per triggered bucket.  All P&L includes losing shares.

Inputs
  * draft-era fills and model probabilities: the merged report
    bots/quant/notes/q018-paired/buckets.csv (2026-10-20), reused verbatim.
  * one post-draft event that resolved after the 2026-10-20 snapshot:
    Bab week of October 12, slug ...-20261006t134953677z.  Fetched live on
    2026-10-21 (Gamma + data-api + PortWatch), cached under _cache/.
"""
import datetime as dt
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
CACHE = HERE / "_cache"
CACHE.mkdir(exist_ok=True)
REPO = HERE.parents[5]
PAIRED = REPO / "bots" / "quant" / "notes" / "q018-paired" / "buckets.csv"
AS_OF = "2026-10-21"
SEED = 20261021
N_BOOT = 10000
FEE_DEFAULT = 0.0
NEW_SLUG = "how-many-ships-transit-bab-el-mandeb-strait-week-of-october-12-20261006t134953677z"
NEW_T = dt.date(2026, 10, 12)
GAMMA = "https://gamma-api.polymarket.com"
TRADES = "https://data-api.polymarket.com/trades"
PW = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
      "Daily_Chokepoints_Data/FeatureServer/0/query")
S = requests.Session()
S.headers.update({"User-Agent": "quant-q018-tradable-backtest/1.0 (keyless public data)"})


def cache_path(name):
    return CACHE / (hashlib.sha1(name.encode()).hexdigest() + ".json")


def get_json(url, params=None, cache_key=None, refresh=False):
    p = cache_path(cache_key or (url + json.dumps(params or {}, sort_keys=True)))
    if p.exists() and not refresh:
        return json.loads(p.read_text(encoding="utf-8"))
    r = S.get(url, params=params, timeout=90)
    r.raise_for_status()
    d = r.json()
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def pf(x):
    return f"{x:+.4f}"


def summarize(df, label):
    if df.empty:
        return f"{label}: n=0"
    ev = df.groupby("event_key").agg(profit=("profit", "sum"), cost=("cost", "sum"), n=("profit", "size"))
    # event-cluster bootstrap of mean per-share profit and per-dollar P&L
    rng = random.Random(SEED)
    groups = [g for _, g in df.groupby("event_key")]
    means, perd = [], []
    for _ in range(N_BOOT):
        pick = [groups[rng.randrange(len(groups))] for _ in range(len(groups))]
        x = pd.concat(pick, ignore_index=True)
        means.append(float(x.profit.mean()))
        perd.append(float(x.profit.sum() / x.cost.sum()))
    means.sort(); perd.sort()
    lo_m, hi_m = means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]
    lo_d, hi_d = perd[int(0.025 * N_BOOT)], perd[int(0.975 * N_BOOT) - 1]
    return (f"{label}: shares={len(df)} events={len(ev)} wins={int((df.profit > 0).sum())} "
            f"median={pf(df.profit.median())}/sh mean={pf(df.profit.mean())}/sh "
            f"total={pf(df.profit.sum())} invested={df.cost.sum():.4f} "
            f"per$={pf(df.profit.sum()/df.cost.sum())} hit={((df.resolved_yes == 0).mean()):.4f} | "
            f"event_total={pf(ev.profit.sum())} event_median={pf(ev.profit.median())} "
            f"event_win={int((ev.profit > 0).sum())}/{len(ev)} | "
            f"boot mean95%=[{lo_m:+.3f},{hi_m:+.3f}] per$95%=[{lo_d:+.3f},{hi_d:+.3f}]")


def rng(label):
    if label.startswith("<"):
        return (-1e9, int(label[1:]) - 1)
    if label.endswith("+"):
        return (int(label[:-1]), 1e9)
    a, b = label.split("-")
    return (int(a), int(b))


def load_portwatch_bab():
    rows, off = [], 0
    while True:
        d = get_json(PW, params={
            "where": "portname = 'Bab el-Mandeb Strait'",
            "outFields": "date,n_total", "returnGeometry": "false", "f": "json",
            "resultOffset": off, "resultRecordCount": 1000,
            "orderByFields": "date ASC"}, cache_key=f"pw_bab_{off}")
        fs = d.get("features", [])
        rows += [f["attributes"] for f in fs]
        if not d.get("exceededTransferLimit"):
            break
        off += 1000
    return {r["date"][:10]: r["n_total"] for r in rows}


def prior_weeks(by_date, T, n=12):
    weeks, d = [], dt.date(2019, 1, 7)
    while d < T:
        dates = [(d + dt.timedelta(days=i)).isoformat() for i in range(7)]
        if all(x in by_date for x in dates):
            weeks.append((d.isoformat(), sum(by_date[x] for x in dates)))
        d += dt.timedelta(days=7)
    return weeks[-n:]


def market_fees(event):
    rates = []
    for m in event["markets"]:
        if m.get("feesEnabled"):
            fs = m.get("feeSchedule") or {}
            rates.append(float(fs.get("rate", 0)))
        else:
            rates.append(0.0)
    return max(rates) if rates else 0.0


def new_event():
    e = get_json(GAMMA + "/events", params={"slug": NEW_SLUG}, cache_key="gamma_" + NEW_SLUG)[0]
    by_date = load_portwatch_bab()
    prior = prior_weeks(by_date, NEW_T)
    probs = {}
    for m in e["markets"]:
        lo, hi = rng(m["groupItemTitle"])
        k = sum(1 for _, v in prior if lo <= v <= hi)
        probs[m["groupItemTitle"]] = (k + 1) / (len(prior) + len(e["markets"]))
    T = dt.datetime(NEW_T.year, NEW_T.month, NEW_T.day, tzinfo=dt.timezone.utc)
    lo, hi = T.timestamp() - 86400, T.timestamp()
    rows = []
    for m in e["markets"]:
        cond = m["conditionId"]
        trades, off = [], 0
        while True:
            d = get_json(TRADES, params={"market": cond, "limit": 500, "offset": off},
                         cache_key=f"trades_{cond}_{off}")
            if not d:
                break
            trades += d
            if min(x["timestamp"] for x in d) < lo or len(d) < 500:
                break
            off += 500
        win = [x for x in trades if lo <= x["timestamp"] <= hi]
        p_yes = None
        if win:
            # Conservative tie-break: if several prints share the last second,
            # use the HIGHEST YES price at that second (worst for a NO buyer).
            last_ts = max(x["timestamp"] for x in win)
            last_prints = [x for x in win if x["timestamp"] == last_ts]
            vals = [x["price"] if str(x.get("outcome", "")).lower() == "yes" else 1 - x["price"]
                    for x in last_prints]
            p_yes = max(vals)
        resolved_yes = 1 if m.get("outcomePrices") in ('["1", "0"]', '["1","0"]') else 0
        rows.append(dict(slug=NEW_SLUG, week_start=NEW_T.isoformat(), label=m["groupItemTitle"],
                         p_model=probs[m["groupItemTitle"]], main_p_yes=p_yes,
                         resolved_yes=resolved_yes, conditionId=cond))
    return pd.DataFrame(rows), e, prior


def main():
    print("quant-018 tradable-price NO backtest; run", AS_OF)
    print("draft history source:", PAIRED.relative_to(REPO), "sha1", hashlib.sha1(PAIRED.read_bytes()).hexdigest())
    old = pd.read_csv(PAIRED)
    old = old[old.strait.str.contains("Bab")].copy()
    old["event_key"] = old.slug
    old["sample"] = "draft_history"
    print(f"draft history: {old.slug.nunique()} Bab events, {old.main_p_yes.notna().sum()} buckets with a [T-24h,T] trade price")

    new, new_e, prior = new_event()
    new["event_key"] = new.slug
    new["sample"] = "post_draft_oos_2026_10_12"
    print(f"post-draft event: {NEW_SLUG}")
    print(f"  prior 12 complete weeks: {prior}")
    print(f"  buckets/model/entry: " + "; ".join(f"{r.label} p_m={r.p_model:.4f} p_yes={r.main_p_yes}" for r in new.itertuples()))
    print(f"  resolved: {new[new.resolved_yes==1].label.tolist()}")

    allrows = pd.concat([old, new], ignore_index=True, sort=False)

    # fee audit
    fees = {}
    for slug in allrows.slug.unique():
        e = get_json(GAMMA + "/events", params={"slug": slug}, cache_key="gamma_" + slug)[0]
        fees[slug] = market_fees(e)
    print("fee rates read from Gamma:", sorted(set(fees.values())),
          "(feesEnabled=false => 0 for all events)" if set(fees.values()) == {0.0} else "")

    fills = []
    for r in allrows.itertuples():
        if pd.isna(r.main_p_yes) or pd.isna(r.p_model):
            continue
        rate = fees.get(r.slug, FEE_DEFAULT)
        for hs, tag in [(0.01, "base_1c"), (0.05, "stress_5c")]:
            if r.main_p_yes < r.p_model + hs + 0.01:
                continue
            cost = 1 - r.main_p_yes + hs
            fee = 1 * rate * cost * (1 - cost)
            payoff = 1 - int(r.resolved_yes)
            fills.append(dict(event_key=r.event_key, slug=r.slug, week_start=r.week_start,
                              label=r.label, sample=r.sample, case=tag,
                              p_model=r.p_model, p_yes=r.main_p_yes, cost=cost, fee=fee,
                              payoff=payoff, profit=payoff - cost - fee,
                              resolved_yes=int(r.resolved_yes)))
    f = pd.DataFrame(fills)
    f.to_csv(HERE / "tradable_fills.csv", index=False, float_format="%.10f")

    print("\n== trigger/fill counts ==")
    print(f.groupby(["case", "sample"]).size().to_string())

    print("\n== results (1 share per triggered bucket, fee included) ==")
    for case in ["base_1c", "stress_5c"]:
        d = f[f.case == case]
        print("\n" + case)
        print(summarize(d, "  all (13 events)"))
        print(summarize(d[d["sample"] == "draft_history"], "  draft history (12 events)"))
        print(summarize(d[d["sample"] == "post_draft_oos_2026_10_12"], "  post-draft OOS (1 event)"))
        print(summarize(d[d.week_start < "2026-09-01"], "  draft weeks < 2026-09-01 (post-hoc split)"))
        print(summarize(d[(d.week_start >= "2026-09-01") & (d["sample"] == "draft_history")],
                        "  draft weeks >= 2026-09-01 (post-hoc split)"))

    print("\n== per-event P&L, base_1c ==")
    d = f[f.case == "base_1c"]
    ev = d.groupby(["week_start", "slug", "sample"]).agg(shares=("profit", "size"),
                                                          profit=("profit", "sum"),
                                                          cost=("cost", "sum")).reset_index()
    ev["per_dollar"] = ev.profit / ev.cost
    print(ev.sort_values("week_start").to_string(index=False))

    base = f[f.case == "base_1c"]
    print("\n== verdict under the entry's frozen criteria ==")
    print(f"(1) median realised gross profit of filled NO shares <= 0? "
          f"median={base.profit.median():+.4f} => {'FAIL' if base.profit.median() <= 0 else 'PASS'}")
    print(f"(1-event-level) event median net profit = {ev.profit.median():+.4f}; "
          f"event hit rate = {(ev.profit > 0).mean():.4f}")
    print("(3) >=30 independent events with same-time tradable prices? "
          f"{base.event_key.nunique()} events (<30) => INSUFFICIENT")
    print("post-draft OOS is 1 event; it is reported, not used to claim significance.")


if __name__ == "__main__":
    main()
