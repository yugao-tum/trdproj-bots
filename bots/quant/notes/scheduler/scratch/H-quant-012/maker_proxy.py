#!/usr/bin/env python3
import csv, gzip, json, statistics, time
from datetime import datetime, timezone
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
MERGED = HERE.parents[2] / "q012-hist"
CACHE = HERE / "_cache"
(CACHE / "gamma").mkdir(parents=True, exist_ok=True)
(CACHE / "trades").mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers["User-Agent"] = "quant-research/1.0 (public data; no auth)"

def get_json(url, params, path, tries=5):
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    last = None
    for i in range(tries):
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code == 200:
                d = r.json()
                with gzip.open(path, "wt", encoding="utf-8") as f:
                    json.dump(d, f)
                time.sleep(0.08)
                return d
            last = f"HTTP {r.status_code}"
            time.sleep(1.5 * (i + 1))
        except Exception as e:
            last = repr(e)
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url} {params}: {last}")

def load(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def trades_for(cid, t0, t1):
    path = CACHE / "trades" / f"{cid}.json.gz"
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            return json.load(f)
    out = []
    offset = 0
    for _ in range(40):
        d = get_json("https://data-api.polymarket.com/trades",
                     {"market": cid, "limit": 500, "offset": offset},
                     CACHE / "trades" / f"{cid}.__p{offset}.json.gz")
        if not d:
            break
        for x in d:
            ts = int(x["timestamp"])
            if t0 - 86400 <= ts <= t1 + 86400:
                out.append({"t": ts, "price": float(x["price"]),
                            "outcome": x["outcome"], "side": x["side"],
                            "size": float(x.get("size", 0))})
        oldest = min(int(x["timestamp"]) for x in d)
        newest = max(int(x["timestamp"]) for x in d)
        if len(d) < 500 or oldest < t0 - 86400 or newest < t0 - 86400:
            break
        offset += 500
    out.sort(key=lambda x: x["t"])
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(out, f)
    for p in (CACHE / "trades").glob(f"{cid}.__p*.json.gz"):
        p.unlink()
    return out

def no_price(x):
    return x["price"] if x["outcome"].lower() == "no" else 1.0 - x["price"]

def is_taker_sell_no(x):
    o = x["outcome"].lower()
    s = x["side"].upper()
    return (o == "no" and s == "SELL") or (o == "yes" and s == "BUY")

def fill_trade(trades, q, t0, t1, through=0.0):
    for x in trades:
        if not (t0 <= x["t"] <= t1):
            continue
        if is_taker_sell_no(x) and no_price(x) <= q - through:
            return x
    return None

def stats(rows, label):
    if not rows:
        print(f"  {label:30s} n=0")
        return
    net = [r["net"] for r in rows]
    q = [r["q"] for r in rows]
    print(f"  {label:30s} filled={len(rows):3d} median_q={statistics.median(q):.4f} "
          f"median_net={statistics.median(net):+.4f} mean_net={statistics.mean(net):+.4f} "
          f"win={sum(1 for r in rows if r['payoff']==1)}/{len(rows)} "
          f"total={sum(net):+.4f}/{sum(q):.4f}={sum(net)/sum(q):+.2%}")

def main():
    bs = [b for b in load(MERGED / "buckets.csv") if b["traded"] == "1"]
    es = {e["event_slug"]: e for e in load(MERGED / "events.csv")}
    by_slug = {}
    for b in bs:
        by_slug.setdefault(b["event_slug"], []).append(b)
    rows_mid, rows_bid, rows_entry, diag = [], [], [], []
    for slug, group in sorted(by_slug.items()):
        ev = get_json("https://gamma-api.polymarket.com/events", {"slug": slug},
                      CACHE / "gamma" / f"{slug}.json.gz")
        ev = ev[0] if isinstance(ev, list) else ev
        cid = {m["groupItemTitle"]: m["conditionId"] for m in ev.get("markets", [])}
        e = es[slug]
        t0 = int(datetime.fromisoformat(e["window_start_utc"]).timestamp())
        t1 = int(datetime.fromisoformat(e["window_end_excl_utc"]).timestamp())
        for b in group:
            c = cid.get(b["bucket"])
            if not c:
                continue
            tr = trades_for(c, t0, t1)
            p = float(b["market_yes_pre"]); m = float(b["model_yes"])
            q_entry = 1 - m - 0.01
            q_mid = 1 - p
            q_bid = 1 - p - 0.01
            no_ask = 1 - p + 0.01
            diag.append({"cross": q_entry >= no_ask - 1e-12, "edge": p - m})
            payoff = 0.0 if b["resolved_yes"] == "1" else 1.0
            for q, out, name in ((q_mid, rows_mid, "mid"), (q_bid, rows_bid, "bid"),
                                 (q_entry, rows_entry, "entry")):
                if q <= 0 or q >= 1:
                    continue
                ft = fill_trade(tr, q, t0, t1)
                if ft is not None:
                    out.append({"slug": slug, "bucket": b["bucket"], "q": q,
                                "net": payoff - q, "payoff": payoff,
                                "fill_t": ft["t"], "t0": t0, "split": e["window_start_utc"]})
    print("quant-012 true-maker fill proxy (data-api trades, maker fee 0)")
    print(f"traded buckets tested: {len(bs)}; band = last pre-window YES price")
    print("\n[diag] entry formula q=1-model-0.01 vs NO ask=1-market+0.01")
    n = len(diag)
    print(f"  would cross NO ask (taker): {sum(1 for d in diag if d['cross'])}/{n} = "
          f"{sum(1 for d in diag if d['cross'])/n:.1%}")
    print(f"  edge on crossing subset: median {statistics.median([d['edge'] for d in diag if d['cross']]):.4f}")
    print("\n[maker] order at NO mid (q=1-market_yes), fill only on taker sell NO <= q")
    stats(rows_mid, "all")
    stats([r for r in rows_mid if r["split"] < "2026-07-01"], "in-sample < 2026-07-01")
    stats([r for r in rows_mid if r["split"] >= "2026-07-01"], "out-of-sample >= 2026-07-01")
    print("\n[maker] order at NO bid (q=1-market_yes-0.01)")
    stats(rows_bid, "all")
    stats([r for r in rows_bid if r["split"] < "2026-07-01"], "in-sample < 2026-07-01")
    stats([r for r in rows_bid if r["split"] >= "2026-07-01"], "out-of-sample >= 2026-07-01")
    print("\n[entry formula] q=1-model-0.01 (may cross; same proxy fill)")
    stats(rows_entry, "all")
    print("\nfill timing (mid):")
    ages = [(r["fill_t"] - r["t0"]) / 3600 for r in rows_mid]
    if ages:
        print(f"  median {statistics.median(ages):.2f}h max {max(ages):.2f}h "
              f"negative(immediate cross) {sum(1 for a in ages if a < 0)}")
    print("\nnote: data-api prints are taker-side; a print through our limit is necessary,")
    print("not sufficient, for a fill. Queue position, depth and adverse selection are unknown.")

if __name__ == "__main__":
    main()
