#!/usr/bin/env python3
import csv, hashlib, math, random, statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
MERGED = HERE.parents[2] / "q012-hist"
BUCKETS = MERGED / "buckets.csv"
EVENTS = MERGED / "events.csv"
SPLIT = "2026-07-01"
random.seed(20261021)

def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()

def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def boot_ci(xs, fn, n=10000):
    vals = []
    for _ in range(n):
        sample = [xs[random.randrange(len(xs))] for _ in xs]
        vals.append(fn(sample))
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]

def summarize(buckets, label):
    net = [float(b["net_per_share"]) for b in buckets]
    gross = [float(b["gross_per_share"]) for b in buckets]
    staked = [float(b["no_exec_price"]) for b in buckets]
    wins = sum(1 for b in buckets if b["resolved_yes"] == "0")
    if not buckets:
        print(f"  {label:28s} n=0")
        return
    lo_m, hi_m = boot_ci(net, statistics.mean)
    lo_d, hi_d = boot_ci(net, statistics.median)
    print(f"  {label:28s} n={len(buckets):3d} win={wins:3d} ({wins/len(buckets):5.1%}) "
          f"median_gross={statistics.median(gross):+.4f} median_net={statistics.median(net):+.4f} "
          f"[{lo_d:+.4f},{hi_d:+.4f}] mean_net={statistics.mean(net):+.4f} "
          f"[{lo_m:+.4f},{hi_m:+.4f}] total={sum(net):+.4f}/{sum(staked):.4f}="
          f"{sum(net)/sum(staked):+.2%}")
    net0 = [float(b["gross_per_share"]) for b in buckets]
    print(f"  {'  same, fee=0':28s} median_net={statistics.median(net0):+.4f} "
          f"mean_net={statistics.mean(net0):+.4f} total={sum(net0):+.4f}/{sum(staked):.4f}="
          f"{sum(net0)/sum(staked):+.2%}")

def main():
    print("quant-012 H-quant-012 merged-evidence recheck")
    print(f"merged dir: {MERGED}")
    print(f"buckets md5 {md5(BUCKETS)} events md5 {md5(EVENTS)}")
    print("I01 md5, for comparison:")
    i01 = HERE.parents[2] / "scheduler" / "scratch" / "I01"
    print(f"  I01 buckets {md5(i01 / 'buckets.csv')} events {md5(i01 / 'events.csv')}")
    bs = rows(BUCKETS)
    es = rows(EVENTS)
    eby = {e["event_slug"]: e for e in es}
    start = {b["event_slug"]: eby[b["event_slug"]]["window_start_utc"] for b in bs}
    traded = [b for b in bs if b["traded"] == "1"]
    print(f"\nsample: events={len(es)} buckets={len(bs)} traded={len(traded)}")
    strict = {e["strict_group"] for e in es}
    strict_priced = {e["strict_group"] for e in es if int(e["n_priced_pre"]) > 0}
    strict_traded = {b["strict_group"] for b in traded}
    print(f"strict groups={len(strict)} with>=1 price={len(strict_priced)} with>=1 trade={len(strict_traded)}")
    for ser in ("M5.5+", "M6.5+", "M7.0+"):
        t = [b for b in traded if b["series"] == ser]
        print(f"  {ser} events={sum(1 for e in es if e['series']==ser)} traded={len(t)}")
    print("\nHEADLINE (as reported by merged run_output.txt):")
    summarize(traded, "all traded NO")
    print("\nTIME SPLIT (out-of-sample = window_start >= " + SPLIT + "):")
    for label, cond in (
        ("in-sample < " + SPLIT, lambda b: start[b["event_slug"]] < SPLIT),
        ("out-of-sample >= " + SPLIT, lambda b: start[b["event_slug"]] >= SPLIT),
    ):
        summarize([b for b in traded if cond(b)], label)
    print("\nSERIES SPLIT:")
    for ser in ("M5.5+", "M6.5+"):
        summarize([b for b in traded if b["series"] == ser], ser + " traded NO")
    print("\nLOG LOSS (model vs market, paired per event with every bracket priced):")
    ll = [e for e in es if e["model_logloss"] and e["market_logloss"]]
    for label, cond in (
        ("all", lambda e: True),
        ("in-sample < " + SPLIT, lambda e: e["window_start_utc"] < SPLIT),
        ("out-of-sample >= " + SPLIT, lambda e: e["window_start_utc"] >= SPLIT),
        ("M6.5+ only", lambda e: e["series"] == "M6.5+"),
        ("M5.5+ only", lambda e: e["series"] == "M5.5+"),
        ("USGS match only", lambda e: e["usgs_match"] == "MATCH"),
    ):
        sub = [e for e in ll if cond(e)]
        if not sub:
            print(f"  {label:28s} n=0")
            continue
        d = [float(e["market_logloss"]) - float(e["model_logloss"]) for e in sub]
        lo, hi = boot_ci(d, statistics.mean)
        mb = sum(1 for e in sub if float(e["model_logloss"]) < float(e["market_logloss"]))
        print(f"  {label:28s} n={len(sub):2d} model={statistics.mean(float(e['model_logloss']) for e in sub):.4f} "
              f"market={statistics.mean(float(e['market_logloss']) for e in sub):.4f} "
              f"diff(market-model)={statistics.mean(d):+.4f} [{lo:+.4f},{hi:+.4f}] "
              f"model_better={mb}/{len(sub)}")
    print("\nUSGS own-count vs resolved bracket by split:")
    for label, cond in (
        ("in-sample < " + SPLIT, lambda e: e["window_start_utc"] < SPLIT),
        ("out-of-sample >= " + SPLIT, lambda e: e["window_start_utc"] >= SPLIT),
    ):
        sub = [e for e in es if cond(e)]
        ok = sum(1 for e in sub if e["usgs_match"] == "MATCH")
        print(f"  {label:28s} {ok}/{len(sub)} MATCH")
    print("\nWorst / best traded NO by net per share:")
    s = sorted(traded, key=lambda b: float(b["net_per_share"]))
    for b in s[:3] + s[-3:]:
        print(f"  {float(b['net_per_share']):+.4f} {b['event_slug']} [{b['bucket']}] "
              f"yes_pre={b['market_yes_pre']} model={b['model_yes']} no={b['no_exec_price']}")
    print("\nFEE NOTE: recorded taker fee 0.05*... ; current 2026-10-21 Gamma check is in verify_output.txt")

if __name__ == "__main__":
    main()
