#!/usr/bin/env python3
"""Re-score the merged q016-hist model-side backtest with the corrected RT rounding rule.

Why: bots/quant/notes/q016-hist/ (merged PR e950778) reconstructed historical (k,m)
from Wayback snapshots and scored the Beta model against data-api trades, but its
pre-declared model used the old floor(100*p) convention. The entry now proves RT uses
round-half-up, i.e. displayed >= T <=> p >= (T-0.5)/100. This script re-uses that merged
event table (events.csv: per-event snapshot k,m and capture time) and re-fetches only the
same 6h trade windows, then reports model calibration under BOTH conventions on the same
scored thresholds. It also re-runs the frozen trigger/P&L rule with the round convention.

Keyless public endpoints only. Raw trades cached under _cache/ (gitignored).
"""
import csv, datetime as dt, json, math, os, statistics, time
import concurrent.futures as cf
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_cache")
HIST = os.path.abspath(os.path.join(BASE, "..", "..", "..", "q016-hist", "events.csv"))
MARKETS = os.path.join(BASE, "markets.json")
DATA_API = "https://data-api.polymarket.com"
FEE_RATE = 0.05
HALF = 0.01
BUFFER = 0.02
UA = {"User-Agent": "Mozilla/5.0 (research; quant-016 hardening round)"}
S = requests.Session(); S.headers.update(UA)


def get(url, **kw):
    for i in range(4):
        try:
            r = S.get(url, timeout=30, **kw)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (i + 1)); continue
            return r
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def trades(cid, start, end):
    key = f"{cid}_{int(start)}_{int(end)}.json"
    path = os.path.join(CACHE, key)
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            pass
    out = []
    off = 0
    for _ in range(6):
        r = get(f"{DATA_API}/trades", params={"market": cid, "limit": 500,
                                             "offset": off, "start": int(start), "end": int(end)})
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


def yes_price(tr):
    try:
        p = float(tr.get("price"))
    except Exception:
        return None
    if not (0 <= p <= 1):
        return None
    return 1.0 - p if str(tr.get("outcome", "")).lower() == "no" else p


def last_yes(trs, t):
    best = None
    for tr in trs:
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
        p = 1.0 - betai(a, b, min(0.999999999, max(1e-9, thr)))
        out.append(p)
    # isotonic non-increasing (same as q016-hist)
    blocks = [[v, 1] for v in out]
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


def main():
    rows = {r["event_slug"]: r for r in csv.DictReader(open(HIST))}
    mk = json.load(open(MARKETS))
    by = {}
    for x in mk:
        by.setdefault(x["event"], []).append(x)
    events = [e for e in by if e in rows and rows[e]["snapshot_ts_primary"] and rows[e]["k"] and rows[e]["m"]]

    # fetch all trade windows in parallel
    jobs = {}
    for e in events:
        r = rows[e]
        snap = dt.datetime.strptime(r["snapshot_ts_primary"], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
        for x in by[e]:
            jobs[(e, x["threshold"])] = (x["conditionId"], int((snap - dt.timedelta(hours=6)).timestamp()), int(snap.timestamp()))
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {k: ex.submit(trades, *v) for k, v in jobs.items()}
        got = {k: f.result() for k, f in futs.items()}

    res = {}
    for mode in ("floor", "round"):
        mb, kb, ml, kl = [], [], [], []
        ev_b, ev_l = [], []
        trades_list, event_nets = [], []
        scored_events = 0
        for e in events:
            r = rows[e]
            snap = dt.datetime.strptime(r["snapshot_ts_primary"], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
            thr = [x["threshold"] for x in sorted(by[e], key=lambda z: z["threshold"])]
            ps = probs(int(r["k"]), int(r["m"]), thr, mode)
            evb, evl = [], []
            evtr = []
            any_scored = False
            for x, p in zip(sorted(by[e], key=lambda z: z["threshold"]), ps):
                trs = got.get((e, x["threshold"]))
                if trs is None:
                    continue
                last = last_yes(trs, int(snap.timestamp()))
                if last is None:
                    continue
                mid = last[1]
                if not (0 < mid < 1):
                    continue
                any_scored = True
                y = int(x["outcome_yes"])
                mb.append(brier(p, y)); kb.append(brier(mid, y))
                ml.append(logloss(p, y)); kl.append(logloss(mid, y))
                evb.append(brier(p, y)); evl.append(logloss(p, y))
                # frozen trigger, round mode only needs P&L but compute same filter for both
                ask_y, no_ask = mid + HALF, 1.0 - (mid - HALF)
                fee_y = FEE_RATE * ask_y * (1 - ask_y)
                fee_n = FEE_RATE * no_ask * (1 - no_ask)
                edge_y, edge_n = p - mid, mid - p
                side = entry = fee = net = None
                if ask_y <= 1 and edge_y > fee_y + HALF + BUFFER and edge_y >= edge_n:
                    side, entry, fee = "YES", ask_y, fee_y
                    net = y - entry - fee
                elif no_ask <= 1 and edge_n > fee_n + HALF + BUFFER:
                    side, entry, fee = "NO", no_ask, fee_n
                    net = (1 - y) - entry - fee
                if side:
                    trades_list.append({"event": e, "T": x["threshold"], "side": side,
                                        "entry": entry, "net": net, "y": y})
                    evtr.append(net)
            if any_scored:
                scored_events += 1
                ev_b.append(statistics.mean(evb)); ev_l.append(statistics.mean(evl))
            if evtr:
                event_nets.append(sum(evtr))
        res[mode] = {
            "scored_events": scored_events, "n_scored": len(mb),
            "model_brier": statistics.mean(mb), "market_brier": statistics.mean(kb),
            "model_ll": statistics.mean(ml), "market_ll": statistics.mean(kl),
            "event_brier_model": statistics.mean(ev_b), "event_brier_market": statistics.mean([x for x in [] ]) if False else None,
            "trades": len(trades_list),
            "trigger_events": len(event_nets),
            "median_event_net": statistics.median(event_nets) if event_nets else None,
            "mean_event_net": statistics.mean(event_nets) if event_nets else None,
            "hit": sum(1 for t in trades_list if t["net"] > 0),
            "total_net": sum(t["net"] for t in trades_list),
            "total_staked": sum(t["entry"] for t in trades_list),
            "per_dollar": (sum(t["net"] for t in trades_list) / sum(t["entry"] for t in trades_list)) if trades_list else None,
        }
        # event-level market brier needs parallel list; recompute simply
        # (collect per-event pairs instead)
    # recompute event-level market brier cleanly
    for mode in ("floor", "round"):
        evm, evk, evml, evkl = [], [], [], []
        for e in events:
            r = rows[e]
            snap = dt.datetime.strptime(r["snapshot_ts_primary"], "%Y%m%d%H%M%S").replace(tzinfo=dt.timezone.utc)
            ordered = sorted(by[e], key=lambda z: z["threshold"])
            ps = probs(int(r["k"]), int(r["m"]), [x["threshold"] for x in ordered], mode)
            bm, bk, lm, lk = [], [], [], []
            for x, p in zip(ordered, ps):
                trs = got.get((e, x["threshold"]))
                if trs is None: continue
                last = last_yes(trs, int(snap.timestamp()))
                if last is None: continue
                mid = last[1]
                if not (0 < mid < 1): continue
                y = int(x["outcome_yes"])
                bm.append(brier(p, y)); bk.append(brier(mid, y)); lm.append(logloss(p, y)); lk.append(logloss(mid, y))
            if bm:
                evm.append(statistics.mean(bm)); evk.append(statistics.mean(bk))
                evml.append(statistics.mean(lm)); evkl.append(statistics.mean(lk))
        res[mode]["event_brier_model"] = statistics.mean(evm)
        res[mode]["event_brier_market"] = statistics.mean(evk)
        res[mode]["event_ll_model"] = statistics.mean(evml)
        res[mode]["event_ll_market"] = statistics.mean(evkl)

    print("Merged q016-hist snapshots re-scored with corrected RT rounding")
    print("source event table: bots/quant/notes/q016-hist/events.csv (", len(rows), "events )")
    print("events with snapshot k,m:", len(events))
    print("trade windows fetched:", len(jobs), "cached/requests\n")
    for mode in ("floor", "round"):
        d = res[mode]
        print(f"[{mode}]")
        print(f"  scored events={d['scored_events']}  scored thresholds={d['n_scored']}")
        print(f"  model Brier={d['model_brier']:.6f}  market Brier={d['market_brier']:.6f}  diff={d['model_brier']-d['market_brier']:+.6f}")
        print(f"  model logloss={d['model_ll']:.6f}  market logloss={d['market_ll']:.6f}  diff={d['model_ll']-d['market_ll']:+.6f}")
        print(f"  event-level Brier model={d['event_brier_model']:.6f} market={d['event_brier_market']:.6f}  logloss model={d['event_ll_model']:.6f} market={d['event_ll_market']:.6f}")
        print(f"  triggered trades={d['trades']}  events/triggered={d['trigger_events']}  hit(net>0)={d['hit']}/{d['trades']}")
        print(f"  median event net/share={d['median_event_net']:+.6f}  mean={d['mean_event_net']:+.6f}")
        print(f"  total net={d['total_net']:+.6f} on staked={d['total_staked']:.6f} -> per $={d['per_dollar']:+.6f}\n")


if __name__ == "__main__":
    main()
