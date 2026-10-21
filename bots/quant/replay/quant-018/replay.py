#!/usr/bin/env python3
"""quant-018 replay: buy NO on Bab el-Mandeb weekly transit-count buckets at
real data-api trade prices, then hold to UMA resolution.

PRE-DECLARED RULE (identical to the entry; nothing is tuned in this file)
  * Only Bab el-Mandeb (Hormuz is explicitly excluded by the entry).
  * Decision time T = Monday 00:00 UTC of the event week.
  * Model p_i = Laplace((k_i+1)/(12+n)) from the last 12 complete Mon-Sun
    PortWatch weeks whose Monday is strictly before T.
  * Entry price per bucket = last data-api trade in [T-24h, T], mapped to a
    YES price (YES print p, NO print 1-p).  If several prints share the last
    second, the HIGHEST YES price at that second is used (worst for a NO
    buyer).  No trade in the window => no fill.
  * Buy NO only if p_yes >= p_model + half_spread + 0.01 (safety cushion).
  * Base half_spread = 0.01; stress = 0.05, and the trigger is recomputed
    under the stress cost (not applied ex post to base fills).
  * Cost = 1 - p_yes + half_spread.  Fee = shares * rate * cost * (1-cost);
    Gamma returned feesEnabled=false (rate 0) for all 13 events on 2026-10-21.
  * Payoff = 1 if the bucket did NOT resolve YES, else 0.
  * One share per triggered bucket; losing shares are included.

Inputs (frozen, < 1 MB, built by
bots/quant/notes/scheduler/scratch/H-quant-018/build_replay_inputs.py):
  * inputs/buckets_bab.csv - 12 draft-era Bab events, same-time [T-24h,T]
    last data-api trade, copied from bots/quant/notes/q018-paired/buckets.csv
    (sha1 962b0b2434581fdf75a6ea8210836a6931baa6e3).
  * inputs/oos_bab_oct12.csv - 1 post-draft event (week of 2026-10-12) that
    resolved after the 2026-10-20 draft snapshot.

Run:
    python3 bots/quant/replay/quant-018/replay.py
Writes trades.csv next to this script and prints every variant.
"""
import random
import statistics
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SEED = 20261021
N_BOOT = 10000
FEE_RATE = 0.0          # Gamma feesEnabled=false for all 13 events (2026-10-21)
SAFETY = 0.01
VARIANTS = [("base_1c", 0.01), ("stress_5c", 0.05)]


def pf(x):
    return f"{x:+.4f}"


def load():
    d = pd.concat([
        pd.read_csv(HERE / "inputs" / "buckets_bab.csv"),
        pd.read_csv(HERE / "inputs" / "oos_bab_oct12.csv"),
    ], ignore_index=True, sort=False)
    d["sample"] = d.week_start.apply(
        lambda w: "post_draft_oos_2026_10_12" if w == "2026-10-12" else "draft_history")
    d["event_key"] = d.slug
    return d


def build_fills(rows):
    fills = []
    for r in rows.itertuples():
        if pd.isna(r.main_p_yes) or pd.isna(r.p_model):
            continue
        for tag, hs in VARIANTS:
            if r.main_p_yes < r.p_model + hs + SAFETY:
                continue
            cost = 1 - r.main_p_yes + hs
            fee = 1 * FEE_RATE * cost * (1 - cost)
            payoff = 1 - int(r.resolved_yes)
            fills.append(dict(event_key=r.event_key, slug=r.slug, week_start=r.week_start,
                              label=r.label, sample=r.sample, case=tag,
                              p_model=r.p_model, p_yes=r.main_p_yes,
                              cost=cost, fee=fee, payoff=payoff,
                              profit=payoff - cost - fee,
                              resolved_yes=int(r.resolved_yes)))
    return pd.DataFrame(fills)


def summarize(df, label):
    if df.empty:
        return f"{label}: n=0"
    ev = df.groupby("event_key").agg(profit=("profit", "sum"), cost=("cost", "sum"))
    rng = random.Random(SEED)
    groups = [g for _, g in df.groupby("event_key")]
    means, perd = [], []
    for _ in range(N_BOOT):
        pick = [groups[rng.randrange(len(groups))] for _ in range(len(groups))]
        x = pd.concat(pick, ignore_index=True)
        means.append(float(x.profit.mean()))
        perd.append(float(x.profit.sum() / x.cost.sum()))
    means.sort()
    perd.sort()
    lo_m, hi_m = means[int(0.025 * N_BOOT)], means[int(0.975 * N_BOOT) - 1]
    lo_d, hi_d = perd[int(0.025 * N_BOOT)], perd[int(0.975 * N_BOOT) - 1]
    return (f"{label}: shares={len(df)} events={len(ev)} "
            f"median={pf(df.profit.median())}/sh mean={pf(df.profit.mean())}/sh "
            f"total={pf(df.profit.sum())} invested={df.cost.sum():.4f} "
            f"per$={pf(df.profit.sum() / df.cost.sum())} "
            f"hit={((df.resolved_yes == 0).mean()):.4f} | "
            f"event_total={pf(ev.profit.sum())} event_median={pf(ev.profit.median())} "
            f"event_win={int((ev.profit > 0).sum())}/{len(ev)} | "
            f"boot mean95%=[{lo_m:+.3f},{hi_m:+.3f}] "
            f"per$95%=[{lo_d:+.3f},{hi_d:+.3f}]")


def drawdown(ev):
    """Event-sequence equity drawdown of the 1-share replay, in USDT."""
    eq = ev.sort_values("week_start").profit.cumsum()
    peak = eq.cummax()
    dd = eq - peak
    return float(dd.min()), float(dd.min() / 200.0)


def main():
    rows = load()
    print("quant-018 replay | Bab el-Mandeb NO ladder at data-api trade prices")
    print(f"draft events=12 (2026-07-20..2026-10-05) + post-draft OOS=1 (2026-10-12)")
    print(f"fee rate={FEE_RATE} (Gamma feesEnabled=false for all 13 events)")
    print(f"variants: {', '.join(f'{t} half_spread={h}' for t, h in VARIANTS)}")
    print(f"buckets with a [T-24h,T] trade: {rows.main_p_yes.notna().sum()}/{len(rows)}")

    f = build_fills(rows)
    f.to_csv(HERE / "trades.csv", index=False, float_format="%.10f")
    print(f"\ntrades.csv: {len(f)} filled bucket-rows "
          f"({f[f.case == 'base_1c'].event_key.nunique()} base events)")
    print("\n== trigger/fill counts ==")
    print(f.groupby(["case", "sample"]).size().to_string())

    print("\n== results (1 share per triggered bucket, fee included) ==")
    for case, _ in VARIANTS:
        d = f[f.case == case]
        print("\n" + case)
        print(summarize(d, "  all"))
        print(summarize(d[d["sample"] == "draft_history"], "  draft history (pre-OOS)"))
        print(summarize(d[d["sample"] == "post_draft_oos_2026_10_12"], "  post-draft OOS"))

    print("\n== per-event P&L, base_1c ==")
    base = f[f.case == "base_1c"]
    ev = base.groupby(["week_start", "slug", "sample"]).agg(
        shares=("profit", "size"), profit=("profit", "sum"),
        cost=("cost", "sum")).reset_index()
    ev["per_dollar"] = ev.profit / ev.cost
    print(ev.sort_values("week_start").to_string(index=False))
    dd, dd_pct = drawdown(ev)
    print(f"\nevent-sequence max drawdown (1-share scale): {dd:+.4f} USDT "
          f"({dd_pct * 100:+.2f}% of the 200 USDT/event cap)")

    d = base[base["sample"] == "draft_history"]
    per_dollar = d.profit.sum() / d.cost.sum()
    events_per_year = 52 * (d.event_key.nunique() / 12)
    annual = per_dollar * 200 * events_per_year / 5000 * 100
    print(f"\nannualised contribution on 5,000 USDT (draft per$={per_dollar:+.4f}, "
          f"200 USDT/event, {events_per_year:.0f} events/yr): {annual:.1f}%")

    print("\n== verdict under the entry's frozen criteria ==")
    print(f"(1) median realised gross profit of filled NO shares <= 0? "
          f"median={base.profit.median():+.4f} => "
          f"{'FAIL' if base.profit.median() <= 0 else 'PASS'}")
    print(f"(1-event-level) event median net profit = {ev.profit.median():+.4f}; "
          f"event hit rate = {(ev.profit > 0).mean():.4f}")
    print(f"(3) >=30 independent events with same-time tradable prices? "
          f"{base.event_key.nunique()} events (<30) => INSUFFICIENT")


if __name__ == "__main__":
    main()
