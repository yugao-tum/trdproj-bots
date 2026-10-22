#!/usr/bin/env python3
"""quant-016 replay, market side: are narrow Tomatometer brackets mispriced?

Model-free falsification test of the entry's premise. Pre-registered rules,
written before any output was seen:
  A  buy NO  on every bracket whose last YES-equivalent fill at T-h is >= 0.90
  B  buy YES on every bracket whose last YES-equivalent fill at T-h is <= 0.10
  C  buy NO  on every bracket whose last YES-equivalent fill at T-h is in [0.25,0.75]
Execution = last data-api per-trade print at/before T-h (max age 24h) + 1c
half-spread + taker fee 0.05*q*(1-q). Hold to resolution, 1 share/bracket.
Independent unit = event. All closed events are out-of-sample; no parameter is
fitted. CLOB prices-history (last-trade/mid, NOT a fill) is a sensitivity check.
Maker-fee-0 keeps the 1c spread but drops the fee.

Diagnostics (not P&L rules): market-implied boundary accuracy; boundary pair;
exploratory 0.25<=p<=0.90 buy-YES (NOT pre-registered).

Inputs frozen from 2026-10-21: universe.csv (Gamma closed brackets).
Usage: python3 replay_market.py [--fetch]
Raw HTTP cached in _cache/ (gitignored).
"""
import argparse, collections, csv, json, math, os, statistics, time
import concurrent.futures as cf
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
UNIV = os.path.join(BASE, "universe.csv")
HORIZONS = {"T-48h": 48 * 3600, "T-24h": 24 * 3600, "T-6h": 6 * 3600}
FEE_RATE = 0.05
HALF = 0.01
UA = {"User-Agent": "Mozilla/5.0 (research; quant-016 replay)"}
S = requests.Session(); S.headers.update(UA)


def get(url, params=None):
    for i in range(4):
        try:
            r = S.get(url, params=params, timeout=30)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (i + 1)); continue
            return r
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def fetch_trades(row, arg):
    cid = row["conditionId"]
    path = os.path.join(CACHE, f"mtr_{cid}.json")
    if os.path.exists(path) and os.path.getsize(path) > 2:
        return cid, "cached"
    if not arg:
        return cid, "missing"
    cutoff = row["end_ts"] - 9 * 86400
    out = []
    for page in range(4):
        r = get("https://data-api.polymarket.com/trades",
                {"market": cid, "limit": 500, "offset": page * 500})
        if r is None or r.status_code != 200:
            break
        try:
            batch = r.json()
        except Exception:
            break
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        try:
            oldest = min(int(x.get("timestamp", 0)) for x in batch)
        except Exception:
            break
        if oldest < cutoff:
            break
    if not out:
        return cid, "empty"
    json.dump(out, open(path, "w"))
    return cid, f"ok:{len(out)}"


def fetch_clob(row, arg):
    tok = row["yes_token"]
    path = os.path.join(CACHE, f"mph_{tok}.json")
    if os.path.exists(path) and os.path.getsize(path) > 10:
        return tok, "cached"
    if not arg:
        return tok, "missing"
    s = row["end_ts"] - 9 * 86400
    r = get("https://clob.polymarket.com/prices-history",
            {"market": tok, "startTs": s, "endTs": row["end_ts"] + 3600, "fidelity": 60})
    if r is None or r.status_code != 200:
        return tok, f"fail:{getattr(r,'status_code',None)}"
    open(path, "wb").write(r.content)
    return tok, "ok"


def trades(cid):
    try:
        return json.load(open(os.path.join(CACHE, f"mtr_{cid}.json")))
    except Exception:
        return []


def ph(tok):
    try:
        return json.load(open(os.path.join(CACHE, f"mph_{tok}.json"))).get("history", [])
    except Exception:
        return []


def fill_at(row, ts, max_age=86400):
    best = None
    for t in trades(row["conditionId"]):
        try:
            tst = int(t.get("timestamp", 0)); price = float(t.get("price", 0))
        except Exception:
            continue
        if tst <= ts and (best is None or tst > best[0]):
            yes = price if str(t.get("outcome", "")).lower() == "yes" else 1.0 - price
            best = (tst, yes)
    if best is None or ts - best[0] > max_age:
        return None
    return {"ts": best[0], "p": best[1], "age_h": (ts - best[0]) / 3600.0}


def clob_at(row, ts, max_age=6 * 3600):
    best = None
    for x in ph(row["yes_token"]):
        try:
            t, p = int(x["t"]), float(x["p"])
        except Exception:
            continue
        if t <= ts and (best is None or t > best[0]):
            best = (t, p)
    if best is None or ts - best[0] > max_age:
        return None
    return {"ts": best[0], "p": best[1], "age_h": (ts - best[0]) / 3600.0}


def net(kind, p, outcome, maker=False):
    q = p if kind == "YES" else 1.0 - p
    pay = outcome if kind == "YES" else 1 - outcome
    fee = 0.0 if maker else FEE_RATE * q * (1 - q)
    return pay - (q + HALF) - fee


def rule_stats(rows, side, pred, maker=False):
    per_event = collections.defaultdict(list)
    for r in rows:
        if pred(r["p"]):
            per_event[r["event"]].append(net(side, r["p"], r["outcome_yes"], maker))
    ev = [sum(v) / len(v) for v in per_event.values()]
    allv = [x for v in per_event.values() for x in v]
    if not allv:
        return None
    pos = sum(1 for x in ev if x > 0); n = len(ev)
    z = (pos - n / 2) / math.sqrt(n / 4) if n else 0
    return dict(n_brackets=len(allv), n_events=n, mean_net=statistics.mean(allv),
                median_net=statistics.median(allv), total_net=sum(allv),
                event_mean=statistics.mean(ev), event_median=statistics.median(ev),
                pos_events=pos, neg_events=n - pos, z=z)


def fmt(x): return "None" if x is None else f"{x:.6f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download missing data-api/CLOB data")
    args = ap.parse_args()
    os.makedirs(CACHE, exist_ok=True)
    rows = []
    for r in csv.DictReader(open(UNIV)):
        r["end_ts"] = int(r["end_ts"]); r["threshold"] = int(r["threshold"])
        r["outcome_yes"] = int(r["outcome_yes"]); r["volume"] = float(r["volume"] or 0)
        rows.append(r)
    by_cid = {r["conditionId"]: r for r in rows}
    by_tok = {r["yes_token"]: r for r in rows}
    if args.fetch:
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            list(ex.map(lambda r: fetch_trades(r, True), by_cid.values()))
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            list(ex.map(lambda r: fetch_clob(r, True), by_tok.values()))

    print("quant-016 market replay | closed Rotten Tomatoes Tomatometer brackets")
    print(f"events={len({r['event'] for r in rows})} brackets={len(rows)} "
          f"window=2026-03-02..2026-10-19")
    print("execution: last data-api print at/before T-h + 1c half-spread + taker "
          "0.05*q*(1-q); hold to resolution; 1 share/bracket")
    print("independent unit = event; no fitted parameter\n")

    data, data_clob = {}, {}
    print("horizon  priced_brackets  priced_events  median_fill_age_h  median_clob_age_h")
    for label, back in HORIZONS.items():
        out, outc = [], []
        for r in rows:
            ts = r["end_ts"] - back
            f = fill_at(r, ts); c = clob_at(r, ts)
            rec = dict(r, p=f["p"] if f else None, fill_age_h=f["age_h"] if f else None)
            recc = dict(r, p=c["p"] if c else None, clob_age_h=c["age_h"] if c else None)
            out.append(rec); outc.append(recc)
        data[label], data_clob[label] = out, outc
        priced = [r for r in out if r["p"] is not None]
        cl = [r for r in outc if r["p"] is not None]
        print(f"{label:6s}  {len(priced):5d}  {len({r['event'] for r in priced}):5d}  "
              f"{statistics.median([r['fill_age_h'] for r in priced]):8.2f}  "
              f"{statistics.median([r['clob_age_h'] for r in cl]):8.2f}")

    # calibration at T-24h
    print("\n== T-24h price calibration (last fill, YES-equivalent) ==")
    rr = [r for r in data["T-24h"] if r["p"] is not None]
    buckets = [(0, .05), (.05, .10), (.10, .25), (.25, .50), (.50, .75), (.75, .90), (.90, .95), (.95, 1.0001)]
    print("bucket        n   events  mean_p  realised_yes  brier")
    brier = []
    for lo, hi in buckets:
        b = [r for r in rr if lo <= r["p"] < hi]
        if not b: continue
        br = statistics.mean((r["p"] - r["outcome_yes"]) ** 2 for r in b)
        brier.extend((r["p"] - r["outcome_yes"]) ** 2 for r in b)
        print(f"[{lo:.2f},{hi:.2f})  {len(b):4d}  {len({r['event'] for r in b}):5d}  "
              f"{statistics.mean(r['p'] for r in b):.4f}  "
              f"{statistics.mean(r['outcome_yes'] for r in b):.4f}  {br:.4f}")
    print("overall market Brier (bracket-level):", round(statistics.mean(brier), 6))
    base = statistics.mean(r["outcome_yes"] for r in rr)
    print("YES base rate:", round(base, 6),
          " constant-Brier:", round(statistics.mean((base - r["outcome_yes"]) ** 2 for r in rr), 6))

    rules = [("A", "NO", lambda p: p >= 0.90), ("B", "YES", lambda p: p <= 0.10),
             ("C", "NO", lambda p: 0.25 <= p <= 0.75)]
    print("\n== pre-registered rules (taker fee + 1c half-spread) ==")
    for label in HORIZONS:
        rows_h = [r for r in data[label] if r["p"] is not None]
        for name, side, pred in rules:
            s = rule_stats(rows_h, side, pred)
            if s:
                print(f"{label} {name} buy {side:3s}: brackets={s['n_brackets']:4d} "
                      f"events={s['n_events']:3d} mean_net={s['mean_net']:+.6f} "
                      f"median_net={s['median_net']:+.6f} total_net={s['total_net']:+.6f} "
                      f"event_mean={s['event_mean']:+.6f} pos/neg={s['pos_events']}/{s['neg_events']} "
                      f"z={s['z']:+.2f}")

    print("\n== maker-fee-0 variant (T-24h, 1c spread still charged) ==")
    rows_h = [r for r in data["T-24h"] if r["p"] is not None]
    for name, side, pred in rules:
        s = rule_stats(rows_h, side, pred, maker=True)
        if s:
            print(f"A/B/C {name} buy {side:3s}: n={s['n_brackets']:4d} events={s['n_events']:3d} "
                  f"mean_net={s['mean_net']:+.6f} event_mean={s['event_mean']:+.6f} "
                  f"total_net={s['total_net']:+.6f}")

    print("\n== CLOB-price sensitivity at T-24h (CLOB = last/mid, not a fill) ==")
    rows_c = [r for r in data_clob["T-24h"] if r["p"] is not None]
    print(f"priced brackets: {len(rows_c)} events: {len({r['event'] for r in rows_c})}")
    for name, side, pred in rules:
        s = rule_stats(rows_c, side, pred)
        if s:
            print(f"{name} buy {side:3s}: brackets={s['n_brackets']:4d} events={s['n_events']:3d} "
                  f"mean_net={s['mean_net']:+.6f} event_mean={s['event_mean']:+.6f} "
                  f"pos/neg={s['pos_events']}/{s['neg_events']}")

    # diagnostics
    byev = collections.defaultdict(list)
    for r in rows_h: byev[r["event"]].append(r)
    errs, pair = [], []
    for ev, rs in byev.items():
        rs = sorted(rs, key=lambda x: x["threshold"])
        yes = [r["threshold"] for r in rs if r["outcome_yes"] == 1]
        if not yes: continue
        final_lo = max(yes)
        above = [r for r in rs if r["p"] >= 0.5]
        if not above: continue
        implied_lo = max(r["threshold"] for r in above)
        errs.append(implied_lo - final_lo)
        lo_row = next(r for r in rs if r["threshold"] == implied_lo)
        hi_rows = [r for r in rs if r["threshold"] > implied_lo]
        if hi_rows:
            hi_row = min(hi_rows, key=lambda r: r["threshold"])
            pair.append((net("YES", lo_row["p"], lo_row["outcome_yes"]),
                         net("NO", hi_row["p"], hi_row["outcome_yes"])))
    print("\nmarket-implied boundary vs final boundary at T-24h (threshold points)")
    print(f"  n={len(errs)} exact={sum(1 for e in errs if e == 0)} "
          f"|error|<=2={sum(1 for e in errs if abs(e) <= 2)}")
    if pair:
        for i, nm in enumerate(["YES lo", "NO hi"]):
            v = [x[i] for x in pair]
            print(f"  {nm}: mean_net={statistics.mean(v):+.4f} total={sum(v):+.4f} "
                  f"pos/neg={sum(1 for x in v if x > 0)}/{sum(1 for x in v if x <= 0)}")

    mid = [r for r in rows_h if 0.25 <= r["p"] <= 0.90]
    pe = collections.defaultdict(list)
    for r in mid: pe[r["event"]].append(net("YES", r["p"], r["outcome_yes"]))
    ev = [sum(v) / len(v) for v in pe.values()]
    if ev:
        n = len(ev); pos = sum(1 for x in ev if x > 0); k = min(pos, n - pos)
        pval = min(1.0, 2 * sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n)
        print("\nexploratory buy YES on 0.25<=p<=0.90 at T-24h (NOT pre-registered)")
        print(f"  brackets={len(mid)} events={n} "
              f"mean_net={statistics.mean([x for v in pe.values() for x in v]):+.4f} "
              f"event_mean={statistics.mean(ev):+.4f} event_median={statistics.median(ev):+.4f} "
              f"pos/neg={pos}/{n-pos} sign_test_p={pval:.4f}")

    bm, bc = [], []
    for evn, rs in byev.items():
        bm.append(statistics.mean((r["p"] - r["outcome_yes"]) ** 2 for r in rs))
        bc.append(statistics.mean((base - r["outcome_yes"]) ** 2 for r in rs))
    print("\nevent-level Brier (mean over brackets, then over events)")
    print(f"  events={len(bm)} market={statistics.mean(bm):.6f} "
          f"constant={statistics.mean(bc):.6f}")


if __name__ == "__main__":
    main()
