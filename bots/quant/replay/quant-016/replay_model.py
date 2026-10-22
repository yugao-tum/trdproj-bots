#!/usr/bin/env python3
"""quant-016 replay: Beta-binomial Tomatometer model at really-tradable prices.

Canonical round-2 replay. Universe = every closed `rotten-tomatoes` Gamma event
(history frozen in universe.csv / snapshots.csv, both fetched 2026-10-21).
Fills = data-api per-trade prints (fallback variant: CLOB prices-history, which
is last-trade/mid and therefore only a sensitivity check, not a fill price).

Frozen decision rule (copied verbatim from the entry, not fitted):
  p ~ Beta(k+1, m+1); displayed score >= T  <=>  round(100p) >= T
  => P_T = 1 - I_{(T-0.5)/100}(k+1, m+1)   (floor variant uses T/100)
  buy YES if P_T - mid > fee(ask) + 0.01 + 0.02
  buy NO  if mid - P_T > fee(no_ask) + 0.01 + 0.02
  hold to resolution, 1 share per bracket; independent unit = event.

Costs: taker fee rate 0.05 * q * (1-q) per share (Gamma feeSchedule mode for the
closed sample), plus a 1c half-spread. maker-fee-0 variant keeps the spread only.
No parameter is fitted; every closed event is out-of-sample for the model.

Usage: python3 replay_model.py [--fetch-clob]
Writes stdout only plus trades_model.csv (canonical variant). Raw HTTP is cached
in _cache/ (gitignored).
"""
import argparse, csv, datetime as dt, json, math, os, statistics, time
import concurrent.futures as cf
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
SNAPS = os.path.join(BASE, "snapshots.csv")
UNIV = os.path.join(BASE, "universe.csv")
FEE_RATE = 0.05
HALF = 0.01
BUFFER = 0.02
FILL_MAX_AGE = 6 * 3600
DATA_API = "https://data-api.polymarket.com"
CLOB = "https://clob.polymarket.com/prices-history"
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


def load_trades(cid, start, end):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"tr_{cid}_{int(start)}_{int(end)}.json")
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            pass
    out, off = [], 0
    for _ in range(6):
        r = get(f"{DATA_API}/trades", {"market": cid, "limit": 500, "offset": off,
                                       "start": int(start), "end": int(end)})
        if r is None or r.status_code != 200:
            return None
        try:
            ch = r.json()
        except Exception:
            return None
        out += ch
        if len(ch) < 500:
            break
        off += 500
    json.dump(out, open(path, "w"))
    return out


def load_clob(tok, start, end):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"ph_{tok}_{int(start)}_{int(end)}.json")
    if os.path.exists(path):
        try:
            return json.load(open(path)).get("history", [])
        except Exception:
            pass
    r = get(CLOB, {"market": tok, "startTs": int(start), "endTs": int(end), "fidelity": 60})
    if r is None or r.status_code != 200:
        return None
    try:
        h = r.json().get("history", [])
    except Exception:
        return None
    json.dump({"history": h}, open(path, "w"))
    return h


def yes_price(tr):
    try:
        p = float(tr.get("price"))
    except Exception:
        return None
    if not (0 <= p <= 1):
        return None
    return 1.0 - p if str(tr.get("outcome", "")).lower() == "no" else p


def last_fill(trs, t):
    best = None
    for tr in trs or []:
        try:
            ts = int(tr["timestamp"])
        except Exception:
            continue
        if ts > t:
            continue
        p = yes_price(tr)
        if p is None:
            continue
        if best is None or ts >= best[0]:
            best = (ts, p)
    if best is None or t - best[0] > FILL_MAX_AGE:
        return None
    return best


def last_clob(hist, t):
    best = None
    for x in hist or []:
        try:
            ts, p = int(x["t"]), float(x["p"])
        except Exception:
            continue
        if ts <= t and (best is None or ts >= best[0]):
            best = (ts, p)
    if best is None or t - best[0] > FILL_MAX_AGE:
        return None
    return best


def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d; h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d; de = d * c; h *= de
        if abs(de - 1.0) < EPS: break
    return h


def betai(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1 - x) / b


def probs(k, m, thresholds, mode):
    a, b = k + 1.0, m + 1.0
    out = []
    for T in thresholds:
        thr = (T / 100.0) if mode == "floor" else ((T - 0.5) / 100.0)
        out.append(1.0 - betai(a, b, min(0.999999999, max(1e-9, thr))))
    blocks = [[v, 1] for v in out]  # isotonic non-increasing as T rises
    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] < blocks[i + 1][0] - 1e-15:
            v = blocks[i][0] * blocks[i][1] + blocks[i + 1][0] * blocks[i + 1][1]
            w = blocks[i][1] + blocks[i + 1][1]
            blocks[i:i + 2] = [[v / w, w]]
            if i > 0: i -= 1
        else:
            i += 1
    o = []
    for v, w in blocks: o.extend([v] * w)
    return o


def brier(p, y): return (p - y) ** 2
def logloss(p, y):
    p = min(1 - 1e-12, max(1e-12, p))
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def read_inputs():
    snaps = {r["event_slug"]: r for r in csv.DictReader(open(SNAPS))}
    by = {}
    for r in csv.DictReader(open(UNIV)):
        r["threshold"] = int(r["threshold"]); r["end_ts"] = int(r["end_ts"])
        r["outcome_yes"] = int(r["outcome_yes"])
        r["volume"] = float(r["volume"] or 0)
        by.setdefault(r["event"], []).append(r)
    for e in by:
        by[e].sort(key=lambda z: z["threshold"])
    return snaps, by


def parse_snap(s):
    return dt.datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)


def run_variant(snaps, by, window, mode, source, fee_rate, progress=False):
    """window: 'primary' or 'sens'. source: 'fill' or 'clob'."""
    events = []
    for e, r in snaps.items():
        if e not in by: continue
        s_ts, kk, mm = ((r["snapshot_ts_primary"], r["k"], r["m"]) if window == "primary"
                        else (r["snapshot_ts_sens"], r["k_sens"], r["m_sens"]))
        if not s_ts or not kk or not mm:
            continue
        events.append((e, parse_snap(s_ts), int(kk), int(mm)))
    if progress:
        print(f"  events with snapshot: {len(events)}", flush=True)

    # fetch price windows in parallel
    jobs = {}
    for e, snap, k, m in events:
        end = int(snap.timestamp()); start = end - FILL_MAX_AGE
        for x in by[e]:
            jobs[(e, x["threshold"])] = (x["conditionId"], x["yes_token"], start, end)
    got = {}
    fn = load_trades if source == "fill" else load_clob
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {}
        for k, (cid, tok, a, b) in jobs.items():
            futs[k] = ex.submit(fn, cid, a, b) if source == "fill" else ex.submit(fn, tok, a, b)
        for k, f in futs.items():
            got[k] = f.result()

    out = dict(scored_events=0, n_scored=0, mb=[], kb=[], ml=[], kl=[],
               trades=[], event_nets=[], event_staked=[], event_triggered=[],
               priced_events=[], event_dates={})
    for e, snap, k, m in events:
        ordered = by[e]
        ps = probs(k, m, [x["threshold"] for x in ordered], mode)
        any_scored, evtr, evstake, evb, evl = False, [], [], [], []
        for x, p in zip(ordered, ps):
            rows = got.get((e, x["threshold"]))
            last = last_fill(rows, int(snap.timestamp())) if source == "fill" else last_clob(rows, int(snap.timestamp()))
            if last is None:
                continue
            mid = last[1]
            if not (0 < mid < 1):
                continue
            any_scored = True
            y = x["outcome_yes"]
            out["mb"].append(brier(p, y)); out["kb"].append(brier(mid, y))
            out["ml"].append(logloss(p, y)); out["kl"].append(logloss(mid, y))
            evb.append(brier(p, y)); evl.append(logloss(p, y))
            ask_y, no_ask = mid + HALF, 1.0 - (mid - HALF)
            fee_y = fee_rate * ask_y * (1 - ask_y)
            fee_n = fee_rate * no_ask * (1 - no_ask)
            edge_y, edge_n = p - mid, mid - p
            side = entry = fee = net = None
            if ask_y <= 1 and edge_y > fee_y + HALF + BUFFER and edge_y >= edge_n:
                side, entry, fee = "YES", ask_y, fee_y
                net = y - entry - fee
            elif no_ask <= 1 and edge_n > fee_n + HALF + BUFFER:
                side, entry, fee = "NO", no_ask, fee_n
                net = (1 - y) - entry - fee
            if side:
                out["trades"].append(dict(event=e, threshold=x["threshold"], side=side,
                                          entry=entry, fee=fee, outcome_yes=y, net=net))
                evtr.append(net); evstake.append(entry)
        if any_scored:
            out["scored_events"] += 1
            out["event_nets"].append(sum(evtr))
            out["event_staked"].append(sum(evstake))
            out["event_triggered"].append(1 if evtr else 0)
            out["priced_events"].append(e)
            out["event_dates"][e] = snap
        out["n_scored"] = len(out["mb"])
    return out


def summarize(d):
    # primary: every priced event contributes its net (0 if untriggered), per no-trigger=0 rule
    ev = d["event_nets"]
    per_dollar = (sum(t["net"] for t in d["trades"]) / sum(t["entry"] for t in d["trades"])
                  if d["trades"] else None)
    return dict(
        scored_events=d["scored_events"], n_scored=d["n_scored"],
        model_brier=statistics.mean(d["mb"]), market_brier=statistics.mean(d["kb"]),
        model_ll=statistics.mean(d["ml"]), market_ll=statistics.mean(d["kl"]),
        trades=len(d["trades"]), trigger_events=sum(d["event_triggered"]),
        median_event_net=statistics.median(ev), mean_event_net=statistics.mean(ev),
        hit=sum(1 for t in d["trades"] if t["net"] > 0),
        total_net=sum(t["net"] for t in d["trades"]),
        total_staked=sum(t["entry"] for t in d["trades"]),
        per_dollar=per_dollar,
    )


def equity_path(d, account=5000.0, per_event=300.0):
    """Modeled cash-funded account: 300 USDT staked per priced event (0 if no
    trigger), P&L = 300 * that event's per-dollar return, ordered by snapshot.
    The account cannot lose more than principal, so equity is floored at 0."""
    order = sorted(d["priced_events"], key=lambda e: d["event_dates"][e])
    nets = dict(zip(d["priced_events"], d["event_nets"]))
    stakes = dict(zip(d["priced_events"], d["event_staked"]))
    eq, peak, mdd, ruin_at = account, account, 0.0, None
    for i, e in enumerate(order, 1):
        r = (nets[e] / stakes[e]) if stakes[e] else 0.0
        eq = max(0.0, eq + per_event * r)
        peak = max(peak, eq)
        if peak > 0:
            mdd = max(mdd, (peak - eq) / peak)
        if eq <= 0 and ruin_at is None:
            ruin_at = i
    return mdd * 100.0, ruin_at, len(order)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch-clob", action="store_true", help="also run the CLOB sensitivity")
    args = ap.parse_args()
    snaps, by = read_inputs()
    print("quant-016 model replay | closed Rotten Tomatoes Tomatometer events")
    print("inputs: snapshots.csv (Wayback (k,m)), universe.csv (Gamma brackets),")
    print("        data-api trades (fill price), CLOB prices-history (sensitivity)")
    print("costs: taker fee 0.05*q*(1-q) + 1c half-spread; 1 share/bracket; hold to resolution")
    print("independent unit: event; all closed events are out-of-sample\n")

    combos = [
        ("primary", "floor", "fill", FEE_RATE, "M1 floor, main [T-72h,T-12h], fills, taker"),
        ("primary", "round", "fill", FEE_RATE, "M2 round, main, fills, taker (CANONICAL)"),
        ("sens",    "round", "fill", FEE_RATE, "M3 round, sens [T-7d,T-24h], fills, taker"),
        ("primary", "round", "fill", 0.0,     "M4 round, main, fills, maker fee 0 (1c spread)"),
    ]
    if args.fetch_clob:
        combos.append(("primary", "round", "clob", FEE_RATE,
                       "M5 round, main, CLOB prices-history, taker"))
    results = {}
    for window, mode, source, fee, label in combos:
        print(f"== {label} ==", flush=True)
        d = run_variant(snaps, by, window, mode, source, fee, progress=True)
        s = summarize(d)
        results[label] = (d, s)
        print(f"  scored events={s['scored_events']}  scored brackets={s['n_scored']}")
        print(f"  Brier model={s['model_brier']:.6f} market={s['market_brier']:.6f} "
              f"diff={s['model_brier']-s['market_brier']:+.6f}")
        print(f"  logloss model={s['model_ll']:.6f} market={s['market_ll']:.6f} "
              f"diff={s['model_ll']-s['market_ll']:+.6f}")
        print(f"  triggered trades={s['trades']} events/triggered={s['trigger_events']} "
              f"hit(net>0)={s['hit']}/{s['trades']}")
        print(f"  PRIMARY all priced events: median event net/share={s['median_event_net']:+.6f} "
              f"mean={s['mean_event_net']:+.6f}")
        if s['per_dollar'] is not None:
            print(f"  total net={s['total_net']:+.6f} on staked={s['total_staked']:.6f} "
                  f"-> per $={s['per_dollar']:+.6f}")
        print()

    d, s = results["M2 round, main, fills, taker (CANONICAL)"]
    mdd, ruin_at, n_ev = equity_path(d)
    yrs = (dt.date(2026, 10, 19) - dt.date(2026, 3, 2)).days / 365.0
    ev_per_year = s["scored_events"] / yrs
    contrib_raw = s["per_dollar"] * 300.0 * ev_per_year / 5000.0 * 100.0
    contrib = max(-100.0, contrib_raw)
    print("== canonical replay summary ==")
    print(f"priced events={s['scored_events']}  window=2026-03-02..2026-10-19")
    print(f"median event net/share={s['median_event_net']:+.6f}  mean={s['mean_event_net']:+.6f}")
    print(f"per $ staked={s['per_dollar']:+.6f}  result=负")
    print(f"modeled max drawdown (300 USDT/event on 5,000)={mdd:.1f}%"
          + (f"  (equity reaches 0 after event {ruin_at}/{n_ev})" if ruin_at else ""))
    print(f"modeled annual contribution on 5,000 = per$ * 300 * events/year / 5000 = {contrib_raw:.1f}%"
          f" -> reported {contrib:.1f}% (cash-funded loss capped at -100%)")
    print(f"(events/year={ev_per_year:.1f})")
    print("NOTE: the modeled % assumes the losing replay repeats; it is not a forecast.")

    with open(os.path.join(BASE, "events_model.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event", "snapshot_ts", "triggered", "net_per_share", "staked_per_share", "per_dollar"])
        for e, net, st, tr in sorted(zip(d["priced_events"], d["event_nets"], d["event_staked"], d["event_triggered"]),
                                     key=lambda z: d["event_dates"][z[0]]):
            w.writerow([e, d["event_dates"][e].strftime("%Y-%m-%dT%H:%M:%SZ"), tr,
                        f"{net:.6f}", f"{st:.6f}", (f"{net/st:.6f}" if st else "")])
    print("wrote events_model.csv", len(d["priced_events"]), "rows")

    with open(os.path.join(BASE, "trades_model.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["event", "threshold", "side", "entry", "fee", "outcome_yes", "net"])
        w.writeheader()
        for t in sorted(d["trades"], key=lambda z: (z["event"], z["threshold"], z["side"])):
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in t.items()})
    print("wrote trades_model.csv", len(d["trades"]), "rows")


if __name__ == "__main__":
    main()
