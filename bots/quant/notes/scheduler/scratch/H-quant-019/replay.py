#!/usr/bin/env python3
"""H-quant-019 replay: CDC measles count-flow model vs really-traded Polymarket prices.

v2 (2026-10-21, after bot `dot`'s review): causal. v1 chose strikes by the
average price of fills that happened AFTER the decision time (look-ahead) and
wrote one leftover market slug for every strike of a ladder. v2 decides only on
prints with ts <= decision time, fills on the first print after the decision,
and carries each strike's own market slug. See SUMMARY.md for before/after.

Rule (taken from the round-1 entry, 2026-10-20; nothing is tuned here):
  - state variable f = official case flow (cases/day), taken as a RANGE from the
    last two settled monthly count windows;
  - fair value P(total >= N) from Monte-Carlo (lognormal daily flow + Poisson
    count, 20k paths, fixed seed), f at both ends of the range, take the SMALLER
    probability p_lo;
  - buy YES only when a REAL taker print is at price <= p_lo - 0.05;
  - max 2 adjacent strikes per ladder, <=300 USDT/strike, hold to settlement.
Variant 2 mirrors it on NO (buy NO when a real NO print <= (1-p_hi) - 0.05).

Fill prices are data-api per-trade prints (https://data-api.polymarket.com/trades).
Only side=BUY prints are used: a taker BUY at p proves the ask was p, so a limit
buy at p was executable. CLOB prices-history is NOT used as a fill price.
Only CLOSED ladders with 0/1 settlement are used.
"""
import csv
import json
import math
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# Cache (events.json + trades/<conditionId>.json). Keep it OUTSIDE the repo:
# set Q019_CACHE=<dir>. Falls back to the git-ignored ./_cache.
CACHE = os.environ.get("Q019_CACHE") or os.path.join(HERE, "_cache")
OUT = os.environ.get("Q019_OUT") or HERE
DATA = "https://data-api.polymarket.com"

SIGMA_M = 0.35          # monthly log-sd, taken from the round-1 entry
EDGE = 0.05             # required edge per share, round-1 entry
FEE_RATE = 0.04         # conservative; many closed monthly markets had feesEnabled=false
N_PATHS = 20000
SEED = 19
CAP_USDT = 300.0        # per strike
SPLIT = "2026-06-01"    # reporting split; no parameter was fitted on either half


def get(url, tries=3):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (research; keyless)"})
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1 + i)
    raise RuntimeError(f"GET failed {url}: {last}")


def load_events():
    p = os.path.join(CACHE, "events.json")
    if not os.path.exists(p):
        raise SystemExit("run fetch_events.py first")
    with open(p) as f:
        return json.load(f)


def strike_of(m):
    t = (m.get("threshold") or "").replace("+", "").replace(",", "").strip()
    try:
        return int(float(t))
    except ValueError:
        return None


def window_of(ev):
    """(lo, hi) count window: highest YES strike <= x < lowest NO strike."""
    yes, no = [], []
    for m in ev["markets"]:
        n = strike_of(m)
        op = m.get("outcomePrices") or []
        if n is None or len(op) < 2:
            continue
        try:
            p_yes = float(op[0])
        except (ValueError, IndexError):
            continue
        if p_yes >= 0.99:
            yes.append(n)
        elif p_yes <= 0.01:
            no.append(n)
    if not yes or not no:
        return None
    lo, hi = max(yes), min(no)
    return (lo, hi) if lo < hi else None


def settled(m):
    op = m.get("outcomePrices") or []
    if len(op) < 2:
        return None
    try:
        y = float(op[0])
    except ValueError:
        return None
    return y >= 0.99 if y in (0.0, 1.0) else None


def parse_dt(s):
    if not s:
        return None
    s = s.replace(" ", "T")
    if s.endswith("+00"):
        s = s[:-3] + "+00:00"
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def mc_p(total_base, days, f, strikes):
    rng = np.random.default_rng(SEED)
    n = N_PATHS
    sig_d = SIGMA_M / math.sqrt(30.44)
    logf = np.full(n, math.log(f))
    tot = np.full(n, float(total_base))
    for _ in range(days):
        logf = logf + sig_d * rng.standard_normal(n)
        tot += rng.poisson(np.maximum(np.exp(logf), 0.0))
    return {k: float((tot >= k).mean()) for k in strikes}


def fetch_trades(cond, max_pages=12, page=500):
    cp = os.path.join(CACHE, "trades", f"{cond}.json")
    if os.path.exists(cp):
        with open(cp) as f:
            return json.load(f)
    rows = _fetch_trades_live(cond, max_pages, page)
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    with open(cp, "w") as f:
        json.dump(rows, f)
    return rows


def _fetch_trades_live(cond, max_pages, page):
    rows = []
    for i in range(max_pages):
        q = urllib.parse.urlencode({"market": cond, "limit": page, "offset": i * page})
        try:
            chunk = get(f"{DATA}/trades?{q}")
        except Exception as exc:  # noqa: BLE001
            print(f"    trades fetch failed {cond} offset={i*page}: {exc}")
            break
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < page:
            break
    return rows


def buy_prints(rows, kind, end):
    """Taker BUY prints of the traded outcome with ts <= end: sorted [(ts, px, sz)]."""
    want = "Yes" if kind == "YES" else "No"
    q = []
    for t in rows:
        if t.get("side") != "BUY" or t.get("outcome") != want:
            continue
        ts = datetime.fromtimestamp(int(t["timestamp"]), tz=timezone.utc)
        if ts > end:
            continue
        q.append((ts, float(t["price"]), float(t["size"])))
    q.sort(key=lambda x: x[0])
    return q


def simulate_ladder(kind, books, limits, start, end, log=None):
    """Causal event-driven replay of one ladder for one side.

    books:  {strike: [(ts, px, sz), ...]} taker BUY prints of the traded outcome.
    limits: {strike: max price (model fair value - EDGE)}.
    Decisions use ONLY prints with ts <= the decision time:
      * at `start` (info time) a strike is selected if its last print at or
        before `start` is <= limit (ranked by that pre-decision edge);
      * afterwards, every print at time t that is <= limit is a decision at t.
    Max 2 strikes per ladder; the second must be the ladder neighbour of the
    first. A decision is filled by the FIRST print of that market/outcome
    strictly after the decision time (GUIDE s.13); if that print is above the
    limit the order does not fill and the decision lapses. Once filled, the
    order keeps resting at the limit and takes later prints <= limit (their
    real size) until 300 USDT. Taker fee shares*FEE_RATE*p*(1-p) (GUIDE s.8).
    Returns {strike: position dict}. Data after a decision never changes it.
    `log`, if a list, receives (ts, action, strike, price) for every decide /
    fill / lapse, so the causality test can compare traces.
    """
    log = [] if log is None else log
    ladder = sorted(books)
    pos, pending, order = {}, {}, []   # order: strikes in decision order

    def allowed(k):
        live = [x for x in order if x in pos or x in pending]
        if k in live or len(live) >= 2:
            return False
        if not live:
            return True
        i, j = ladder.index(live[0]), ladder.index(k)
        return abs(i - j) == 1

    def decide(k, t, px):
        pending[k] = {"decision_ts": t, "decision_px": px}
        order.append(k)
        log.append((t, "decide", k, px))

    # 1) decision at start, from data <= start only
    pre = []
    for k in ladder:
        last = [p for p in books[k] if p[0] <= start]
        if last and last[-1][1] <= limits[k]:
            pre.append((limits[k] - last[-1][1], k, last[-1][1]))
    for edge, k, px in sorted(pre, key=lambda x: (-x[0], x[1])):
        if allowed(k):
            decide(k, start, px)

    # 2) walk every later print in time order
    stream = sorted((ts, k, px, sz) for k in ladder for ts, px, sz in books[k]
                    if start < ts <= end)
    for ts, k, px, sz in stream:
        lim = limits[k]
        if k in pos:                      # resting limit after first fill
            p = pos[k]
            if px <= lim and p["cost"] < CAP_USDT - 1e-9:
                take = min(sz, (CAP_USDT - p["cost"]) / px)
                p["cost"] += take * px
                p["shares"] += take
                p["n_prints"] += 1
            continue
        if k in pending and ts > pending[k]["decision_ts"]:
            d = pending.pop(k)
            if px <= lim:                 # first trade after the decision
                take = min(sz, CAP_USDT / px)
                pos[k] = dict(d, first_fill=ts, first_px=px, first_sz=sz,
                              cost=take * px, shares=take, n_prints=1)
                log.append((ts, "fill", k, px))
                continue
            order.remove(k)               # lapsed: price moved above limit
            log.append((ts, "lapse", k, px))
        if px <= lim and allowed(k):
            decide(k, ts, px)
    return pos


def settle(kind, p, settled_yes):
    avg = p["cost"] / p["shares"]
    fee = p["shares"] * FEE_RATE * avg * (1 - avg)
    win = settled_yes if kind == "YES" else not settled_yes
    payout = p["shares"] * (1.0 if win else 0.0)
    net = payout - p["cost"] - fee
    return dict(p, kind=kind, avg_price=avg, fee=fee, win=int(win), payout=payout,
                net=net, ret=net / p["cost"])


def main():
    events = load_events()
    milestones = []
    for ev in events:
        w = window_of(ev)
        end = parse_dt(ev["endDate"])
        if w is None or end is None or end.year != 2026:
            continue
        milestones.append({"slug": ev["slug"], "end": end,
                           "closed": parse_dt(ev.get("closedTime")) or end,
                           "lo": w[0], "hi": w[1]})
    milestones.sort(key=lambda x: x["end"])
    print("settled 2026 milestone windows (Gamma outcomePrices):")
    for m in milestones:
        print(f"  {m['slug']:58s} end={m['end'].date()} closed={m['closed']:%Y-%m-%d %H:%M} "
              f"window=[{m['lo']},{m['hi']})")

    flows = []
    prev = None
    for m in milestones:
        if prev is None:
            prev = m
            continue
        days = (m["end"] - prev["end"]).days
        lo = max(0.0, (m["lo"] - prev["hi"]) / days)
        hi = (m["hi"] - prev["lo"]) / days
        if hi <= 0:
            if flows:
                lo, hi = flows[-1][0], flows[-1][1]
            else:
                continue
        flows.append((lo, hi, prev, m))
        prev = m

    def flow_for(end_dt):
        best = None
        for lo, hi, a, b in flows:
            if b["end"] < end_dt:
                best = (lo, hi, b)
        return best

    # target ladders: closed, >=2 settled strikes. Drop the duplicated August
    # event (20260728213423295) whose strikes were re-listed in the canonical one.
    DUP = {"measles-cases-in-uptspt-by-august-31-20260728213423295"}
    targets = []
    for ev in events:
        end = parse_dt(ev["endDate"])
        if end is None or end.year != 2026 or not ev.get("closed"):
            continue
        if ev["slug"] in DUP:
            continue
        good = [m for m in ev["markets"] if strike_of(m) is not None and settled(m) is not None]
        strikes = sorted({strike_of(m) for m in good})
        if len(strikes) < 2:
            continue
        ev = dict(ev, markets=good)
        targets.append((end, ev, strikes))
    targets.sort()

    all_fills, per_event = [], []
    print("\nreplay (position: <=2 adjacent strikes, 300 USDT each):")
    for end, ev, strikes in targets:
        fl = flow_for(end)
        if fl is None:
            print(f"  {ev['slug']}: skipped (no prior two settled windows)")
            continue
        f_lo, f_hi, prior = fl
        info_dt = prior["closed"]
        base = (prior["lo"] + prior["hi"]) / 2.0
        days = (end - prior["end"]).days
        if days <= 0:
            continue
        p_lo = mc_p(base, days, f_lo, strikes)
        p_hi = mc_p(base, days, f_hi, strikes)
        print(f"\n  {ev['slug']} end={end.date()} base={base:.0f} days={days} "
              f"f=[{f_lo:.2f},{f_hi:.2f}]/d (info {prior['closed']:%Y-%m-%d})")

        mk = {}   # strike -> (market, rows, settled_yes); identity carried per strike
        for m in ev["markets"]:  # already filtered to settled strikes
            k = strike_of(m)
            if k is None or k not in p_lo:
                continue
            sy = settled(m)
            if sy is None:
                continue
            rows = fetch_trades(m["conditionId"])
            mk[k] = (m, rows, sy)

        ev_fills = []
        for kind in ("YES", "NO"):
            limits = {k: (p_lo[k] - EDGE) if kind == "YES" else ((1 - p_hi[k]) - EDGE)
                      for k in mk}
            books = {k: buy_prints(rows, kind, end) for k, (m, rows, sy) in mk.items()}
            chosen = simulate_ladder(kind, books, limits, info_dt, end)
            for k in sorted(chosen):
                m, rows, sy = mk[k]
                f = settle(kind, chosen[k], sy)
                rec = {"event": ev["slug"], "market": m["slug"], "condition_id": m["conditionId"],
                       "strike": k, "kind": kind,
                       "limit": round(limits[k], 4),
                       "decision_ts": f["decision_ts"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "decision_px": round(f["decision_px"], 4),
                       "first_fill": f["first_fill"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "first_px": round(f["first_px"], 4),
                       "shares": round(f["shares"], 2), "avg_price": round(f["avg_price"], 4),
                       "cost": round(f["cost"], 2), "fee": round(f["fee"], 2),
                       "win": f["win"], "payout": round(f["payout"], 2),
                       "net": round(f["net"], 2), "ret": round(f["ret"], 5),
                       "n_prints": f["n_prints"]}
                ev_fills.append(rec)
                all_fills.append(rec)
                print(f"    {kind} strike={k:5d} decide={rec['decision_ts']} @{f['decision_px']:.3f} "
                      f"fill={rec['first_fill']} @{f['first_px']:.3f} avg={f['avg_price']:.3f} "
                      f"cost={f['cost']:.0f} net={f['net']:+.0f} ret={f['ret']:+.1%} win={f['win']}")
        if ev_fills:
            cost = sum(r["cost"] for r in ev_fills)
            net = sum(r["net"] for r in ev_fills)
            per_event.append({"event": ev["slug"], "end": end.strftime("%Y-%m-%d"),
                              "fills": len(ev_fills), "cost": cost, "net": net,
                              "ret": net / cost if cost else 0.0})
        else:
            print("    -> no qualifying prints")
        time.sleep(0.1)

    print("\n=== per event (independent result = event) ===")
    for r in per_event:
        print(f"{r['event']:52s} {r['end']} {r['fills']:2d} {r['cost']:8.2f} "
              f"{r['net']:8.2f} {r['ret']:+8.2%}")

    def agg(rows):
        cost = sum(r["cost"] for r in rows)
        net = sum(r["net"] for r in rows)
        return len(rows), cost, net, (net / cost if cost else 0.0)

    for kind in ("YES", "NO"):
        rows = [r for r in all_fills if r["kind"] == kind]
        print(f"\n=== variant {kind} ===")
        for label, sub in (("ALL", rows),
                           (f"IN <{SPLIT}", [r for r in rows if r["first_fill"] < SPLIT]),
                           (f"OUT >={SPLIT}", [r for r in rows if r["first_fill"] >= SPLIT])):
            n, cost, net, ret = agg(sub)
            evs = len({r["event"] for r in sub})
            print(f"  {label:12s} fills={n:2d} events={evs:2d} cost={cost:8.2f} "
                  f"net={net:7.2f} ret={ret:+.2%}")

    # account-level drawdown on 5,000 USDT, realised at each ladder's end date
    # (no intra-event mark-to-market), per variant and combined.
    ev_end = {r["event"]: r["end"] for r in per_event}

    def max_dd(rows):
        by = {}
        for r in rows:
            by[ev_end[r["event"]]] = by.get(ev_end[r["event"]], 0.0) + r["net"]
        eq = peak = 5000.0
        dd = 0.0
        for d in sorted(by):
            eq += by[d]
            peak = max(peak, eq)
            dd = max(dd, (peak - eq) / peak)
        return dd

    dds = {k: max_dd([r for r in all_fills if r["kind"] == k]) for k in ("YES", "NO")}
    dds["ALL"] = max_dd(all_fills)
    print("\nmax drawdown on 5,000 USDT (settlement-date steps): "
          + ", ".join(f"{k}={v:.2%}" for k, v in dds.items()))
    for kind in ("YES", "NO"):
        ex = [r for r in all_fills if r["kind"] == kind and ev_end[r["event"]] != "2026-07-31"]
        n, cost, net, ret = agg(ex)
        print(f"{kind} ex 2026-07-31: fills={n} cost={cost:.2f} net={net:.2f} ret={ret:+.2%}")

    rows0 = [dict(r, net=r["payout"] - r["cost"]) for r in all_fills]
    n, cost, net, ret = agg(rows0)
    print(f"\nfee=0 sensitivity: fills={n} cost={cost:.2f} net={net:.2f} ret={ret:+.2%}")

    # annualised contribution to a 5,000 USDT account.
    # capital-weighted return per event * average deployed * events/year / 5000
    if per_event:
        tot_cost = sum(r["cost"] for r in per_event)
        tot_net = sum(r["net"] for r in per_event)
        avg_ret = tot_net / tot_cost
        avg_deployed = tot_cost / len(per_event)
        events_per_year = 12.0
        contrib = avg_ret * avg_deployed * events_per_year / 5000.0
        print(f"\navg deployed/event={avg_deployed:.2f} USDT, avg ret/event={avg_ret:+.2%}, "
              f"12 events/yr -> contribution={contrib:+.2%} of 5,000 USDT")
    else:
        contrib = 0.0

    with open(os.path.join(OUT, "fills.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_fills[0].keys()) if all_fills else
                           ["event", "kind", "net"])
        w.writeheader()
        w.writerows(all_fills)
    print(f"wrote fills.csv ({len(all_fills)} rows)")

    summary = {"sigma_m": SIGMA_M, "edge": EDGE, "fee_rate": FEE_RATE,
               "cap_usdt": CAP_USDT, "n_paths": N_PATHS, "seed": SEED,
               "split": SPLIT, "per_event": per_event,
               "contribution": contrib, "max_dd": dds, "variants": {}}
    for kind in ("YES", "NO"):
        rows = [r for r in all_fills if r["kind"] == kind]
        summary["variants"][kind] = {
            k: dict(zip(("fills", "cost", "net", "ret"), agg(sub)))
            for k, sub in (("all", rows),
                           ("in", [r for r in rows if r["first_fill"] < SPLIT]),
                           ("out", [r for r in rows if r["first_fill"] >= SPLIT]))}
    with open(os.path.join(OUT, "replay_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print("wrote replay_summary.json")


if __name__ == "__main__":
    main()
