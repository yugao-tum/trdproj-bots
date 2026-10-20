#!/usr/bin/env python3
"""quant-001 multiple-testing robustness: DSR, CSCV/PBO, paired bootstrap.

Data and VM/fold logic are reused from ../reproduce.py (public Binance daily klines,
keyless). This script does NOT modify reproduce.py. Downloads are cached in ./_data.

--------------------------------------------------------------------------------
PRE-SPECIFIED GATE FAMILY (frozen 2026-10-20, before any result was computed)
--------------------------------------------------------------------------------
Base book (identical to reproduce.py "M1_VM_base"): BTC/ETH/SOL spot, 30-day
momentum skipping the last day, equal weight among positive-momentum coins,
scaled by min(1, 15% / annualised 4-week realised vol), rebalanced every 5 days,
weights decided at t-1 close and earning day t returns, long-only, no leverage.

Each variant = the same VM weights multiplied by one BTC daily on/off gate
(gate observed at t-1 close, applied to day t). "off" means all cash.
Family (106 variants, counted before estimation):

  no gate (VM baseline)                                             1
  BTC close >= SMA(n) * (1+b), n in {5,10,15,20,30,40,50,75,100,
      125,150,200}, b in {-0.01, 0.00, +0.01}                      36
  BTC close >= EMA(n) * (1+b), same n and b grid                  36
  BTC close >= Parabolic SAR, af in {0.01,0.02,0.03},
      max_af in {0.10,0.15,0.20}                                   9
  BTC CCI(n) >= thr, n in {10,20,40}, thr in {-50,0,50}            9
  BTC Bollinger %B(20,2) >= thr, thr in {0.0,0.2,0.4,0.6,0.8}      5
  BTC close > highest close of prior n days (Donchian),
      n in {10,20,30,60,90}                                        5
  BTC n-day ROC > 0, n in {10,20,30,60,90}                         5
                                                                ----
                                                                 106

The b=+/-1% bands are pre-declared confirmation/tolerance variants of the same
MA rule, not a second search. SAR(0.02,0.15) is the private-repo leader and is
inside the family (not added after seeing results).

Protocol: 4 OOS folds exactly as reproduce.py; 0.30% cost per side on |delta w|;
compound = product of fold returns - 1; CAGR on OOS days; Sharpe = mean/std of
daily OOS returns * sqrt(365); path drawdown on the stitched 4-fold daily series.
All 106 variants use the same baseline weights and the same folds.

Statistics:
(a) Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014). Trial Sharpes are daily
    (not annualised); Var is the cross-variant sample variance (ddof=1). SR0 uses
    N = 106 and, separately, N = 224,000 (private-repo search size in README.md).
(b) PBO via CSCV, S=16 contiguous blocks, all C(16,8)=12,870 splits; at each
    split the IS-best (highest Sharpe) variant's OOS rank is recorded; PBO is
    the fraction of splits whose OOS rank is in the bottom half (logit <= 0).
(c) Paired vs baseline: circular block bootstrap, block length 20 days,
    4,000 resamples, seed 20261020. One-sided p for mean daily return difference
    (gate - baseline); also for daily Sharpe difference. Holm and BH across the
    105 gated variants.
(d) Fractions of the 105 gates beating baseline on Sharpe, path max DD and
    compound return.

Run: python3 q001_robustness.py
Outputs: run_output.txt, variants.csv (both written by this script).
"""
import itertools
import math
import pathlib
import sys
from statistics import NormalDist

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
XQT = HERE.parent
sys.path.insert(0, str(XQT))
import reproduce as rp  # noqa: E402

FEE = 0.003
S_BLOCKS = 16
N_BOOT = 4000
BLOCK_LEN = 20
SEED = 20261020
GAMMA = 0.5772156649015329
ND = NormalDist()

NS = [5, 10, 15, 20, 30, 40, 50, 75, 100, 125, 150, 200]
BUFS = [-0.01, 0.0, 0.01]
SAR_AF = [0.01, 0.02, 0.03]
SAR_MAX = [0.10, 0.15, 0.20]
CCI_NS = [10, 20, 40]
CCI_THR = [-50.0, 0.0, 50.0]
PCTB_THR = [0.0, 0.2, 0.4, 0.6, 0.8]
DON_N = [10, 20, 30, 60, 90]
ROC_N = [10, 20, 30, 60, 90]


def build_specs():
    specs = [{"name": "none", "family": "baseline", "params": {}}]
    for n in NS:
        for b in BUFS:
            specs.append({"name": f"sma{n}_b{b:+.2f}", "family": "SMA level",
                          "params": {"n": n, "buffer": b}})
    for n in NS:
        for b in BUFS:
            specs.append({"name": f"ema{n}_b{b:+.2f}", "family": "EMA level",
                          "params": {"n": n, "buffer": b}})
    for af in SAR_AF:
        for mx in SAR_MAX:
            specs.append({"name": f"sar_{af:.2f}_{mx:.2f}", "family": "SAR",
                          "params": {"af": af, "max_af": mx}})
    for n in CCI_NS:
        for thr in CCI_THR:
            specs.append({"name": f"cci{n}_{int(thr)}", "family": "CCI",
                          "params": {"n": n, "threshold": thr}})
    for thr in PCTB_THR:
        specs.append({"name": f"pctb_{thr:.1f}", "family": "%B(20,2)",
                      "params": {"threshold": thr}})
    for n in DON_N:
        specs.append({"name": f"donchian{n}", "family": "Donchian",
                      "params": {"n": n}})
    for n in ROC_N:
        specs.append({"name": f"roc{n}", "family": "ROC", "params": {"n": n}})
    return specs


def gate_series(spec, btc):
    kind = spec["family"]
    p = spec["params"]
    c = btc["close"]
    if kind == "baseline":
        return pd.Series(True, index=c.index)
    if kind == "SMA level":
        return c >= c.rolling(p["n"]).mean() * (1.0 + p["buffer"])
    if kind == "EMA level":
        return c >= c.ewm(span=p["n"], adjust=False).mean() * (1.0 + p["buffer"])
    if kind == "SAR":
        return pd.Series(rp.sar_above(btc["high"], btc["low"], c, p["af"], p["max_af"]),
                         index=c.index)
    if kind == "CCI":
        tp = (btc["high"] + btc["low"] + c) / 3.0
        ma = tp.rolling(p["n"]).mean()
        md = tp.rolling(p["n"]).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        return ((tp - ma) / (0.015 * md)) >= p["threshold"]
    if kind == "%B(20,2)":
        m, s = c.rolling(20).mean(), c.rolling(20).std()
        return ((c - (m - 2 * s)) / (4 * s)) >= p["threshold"]
    if kind == "Donchian":
        return c > c.rolling(p["n"]).max().shift(1)
    if kind == "ROC":
        return (c / c.shift(p["n"]) - 1.0) > 0
    raise ValueError(kind)


def variant_stats(te):
    eq = (1.0 + te).cumprod()
    comp = eq.iloc[-1] - 1.0
    years = len(te) / 365.0
    cagr = (1.0 + comp) ** (1.0 / years) - 1.0 if years > 0 else np.nan
    sd = te.std()
    sharpe = te.mean() / sd * math.sqrt(365.0) if sd > 0 else np.nan
    year_frac = len(te) / 365.0
    return {
        "compound_pct": comp * 100.0,
        "cagr_pct": cagr * 100.0,
        "sharpe_ann": sharpe,
        "path_dd_pct": (eq / eq.cummax() - 1.0).min() * 100.0,
        "mean_daily_pct": te.mean() * 100.0,
        "T": int(len(te)),
        "years": year_frac,
    }


def run_family(panels, specs):
    rows = []
    series = {}
    exposures = {}
    fold_rets = {}
    for spec in specs:
        series[spec["name"]] = []
        fold_rets[spec["name"]] = []
        exposures[spec["name"]] = []
    for a, b in rp.FOLDS:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        sub = {s: panels[s].loc[a - pd.Timedelta(days=rp.LOOK):b] for s in panels}
        px = pd.DataFrame({s: sub[s]["close"] for s in rp.SYMS}).dropna()
        w0 = rp.vm_weights(px)
        btc = sub["BTC"].reindex(px.index)
        for spec in specs:
            if spec["family"] == "baseline":
                w = w0
            else:
                keep = gate_series(spec, btc).astype(float)
                w = w0.mul(keep.shift(1).fillna(1.0), axis=0)
            net = rp.apply(w, px, FEE).loc[a:b]
            series[spec["name"]].append(net)
            fold_rets[spec["name"]].append((1.0 + net).prod() - 1.0)
            exposures[spec["name"]].append(w.loc[a:b].sum(axis=1).mean())
    names = [s["name"] for s in specs]
    rets = pd.DataFrame({n: pd.concat(series[n]) for n in names})
    for spec in specs:
        n = spec["name"]
        te = rets[n]
        st = variant_stats(te)
        fr = fold_rets[n]
        rows.append({
            "name": n, "family": spec["family"], **spec["params"],
            "compound_pct": st["compound_pct"], "cagr_pct": st["cagr_pct"],
            "sharpe_ann": st["sharpe_ann"], "path_dd_pct": st["path_dd_pct"],
            "avg_exposure": float(np.mean(exposures[n])),
            "folds_pos": int(sum(r > 0 for r in fr)),
            "fold_rets_pct": "|".join(f"{r * 100:.1f}" for r in fr),
            "mean_daily_pct": st["mean_daily_pct"], "T": st["T"],
            "skew": float(te.skew()), "kurtosis": float(te.kurt() + 3.0),
        })
    return pd.DataFrame(rows), rets


def dsr(sr_daily, T, skew, kurt, var_trial_sr, n_trials):
    e = math.e
    sr0 = math.sqrt(var_trial_sr) * (
        (1.0 - GAMMA) * ND.inv_cdf(1.0 - 1.0 / n_trials)
        + GAMMA * ND.inv_cdf(1.0 - 1.0 / (n_trials * e))
    )
    denom = math.sqrt(max(1e-12, 1.0 - skew * sr_daily
                          + ((kurt - 1.0) / 4.0) * sr_daily ** 2))
    z = (sr_daily - sr0) * math.sqrt(T - 1) / denom
    return {"dsr": ND.cdf(z), "sr0_daily": sr0, "z": z, "denom": denom}


def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def bh(pvals):
    p = np.asarray(pvals, dtype=float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 1.0
    for rank in range(m, 0, -1):
        idx = order[rank - 1]
        running = min(running, p[idx] * m / rank)
        adj[idx] = min(1.0, running)
    return adj


def pbo_cscv(rets, s_blocks=S_BLOCKS):
    vals = rets.to_numpy(dtype=float)
    T, N = vals.shape
    idx_blocks = np.array_split(np.arange(T), s_blocks)
    sums = np.array([vals[idx].sum(axis=0) for idx in idx_blocks])
    sqs = np.array([(vals[idx] ** 2).sum(axis=0) for idx in idx_blocks])
    cnt = np.array([len(idx) for idx in idx_blocks], dtype=float)
    tot_sum, tot_sq = sums.sum(axis=0), sqs.sum(axis=0)
    combos = list(itertools.combinations(range(s_blocks), s_blocks // 2))
    lambdas = np.empty(len(combos))
    ranks = np.empty(len(combos), dtype=int)
    for k, comb in enumerate(combos):
        sel = list(comb)
        is_sum = sums[sel].sum(axis=0)
        is_sq = sqs[sel].sum(axis=0)
        is_n = cnt[sel].sum()
        oo_sum = tot_sum - is_sum
        oo_sq = tot_sq - is_sq
        oo_n = cnt.sum() - is_n
        is_mean = is_sum / is_n
        oo_mean = oo_sum / oo_n
        is_sd = np.sqrt(np.maximum(is_sq / is_n - is_mean ** 2, 1e-24))
        oo_sd = np.sqrt(np.maximum(oo_sq / oo_n - oo_mean ** 2, 1e-24))
        is_sr = is_mean / is_sd
        oo_sr = oo_mean / oo_sd
        best = int(np.argmax(is_sr))
        rank = 1 + int(np.sum(oo_sr < oo_sr[best]))
        ranks[k] = rank
        omega = rank / (N + 1.0)
        lambdas[k] = math.log(omega / (1.0 - omega))
    pbo = float(np.mean(lambdas <= 0.0))
    return {"pbo": pbo, "n_splits": len(combos), "S": s_blocks,
            "block_min": int(cnt.min()), "block_max": int(cnt.max()),
            "median_rank": float(np.median(ranks)),
            "mean_lambda": float(np.mean(lambdas)),
            "P_rank_le_half": float(np.mean(ranks <= (N + 1) // 2))}


def block_bootstrap_pvalues(gates, base):
    """Circular block bootstrap, paired, one-sided p for gate > baseline."""
    T, m = gates.shape
    rng = np.random.default_rng(SEED)
    nblocks = int(math.ceil(T / BLOCK_LEN))
    starts = rng.integers(0, T, size=(N_BOOT, nblocks))
    offs = np.arange(BLOCK_LEN)
    idx = ((starts[:, :, None] + offs[None, None, :]).reshape(N_BOOT, -1)[:, :T]) % T
    base_idx = base[idx]
    base_mean = base_idx.mean(axis=1)
    base_sd = base_idx.std(axis=1, ddof=1)
    p_mean = np.empty(m)
    p_sr = np.empty(m)
    obs_mean_diff = np.empty(m)
    obs_sr_diff = np.empty(m)
    for j in range(m):
        x = gates[:, j][idx]
        dm = (x - base_idx).mean(axis=1)
        p_mean[j] = (1.0 + np.sum(dm <= 0.0)) / (N_BOOT + 1.0)
        sr = x.mean(axis=1) / x.std(axis=1, ddof=1)
        dsr = sr - base_mean / base_sd
        p_sr[j] = (1.0 + np.sum(dsr <= 0.0)) / (N_BOOT + 1.0)
        obs_mean_diff[j] = gates[:, j].mean() - base.mean()
        obs_sr_diff[j] = (gates[:, j].mean() / gates[:, j].std(ddof=1)
                          - base.mean() / base.std(ddof=1))
    return p_mean, p_sr, obs_mean_diff, obs_sr_diff


def main():
    specs = build_specs()
    print(f"PRE-SPECIFIED FAMILY SIZE: {len(specs)} variants")
    counts = pd.Series([s["family"] for s in specs]).value_counts()
    print("families:", {str(k): int(v) for k, v in counts.items()})
    print("loading public Binance daily data (cache ./_data, reused if present)...")
    rp.DATA = HERE / "_data"
    panels = {s: rp.load(s) for s in rp.SYMS}
    for s in rp.SYMS:
        print(f"  {s}: {panels[s].index[0].date()} .. {panels[s].index[-1].date()} "
              f"({len(panels[s])} rows)")

    df, rets = run_family(panels, specs)
    base_name = "none"
    base = df.loc[df["name"] == base_name].iloc[0]
    df["sharpe_diff_vs_base"] = df["sharpe_ann"] - float(base["sharpe_ann"])
    df["delta_compound_pp"] = df["compound_pct"] - float(base["compound_pct"])
    df["delta_path_dd_pp"] = df["path_dd_pct"] - float(base["path_dd_pct"])

    gates = [s["name"] for s in specs if s["family"] != "baseline"]
    p_mean, p_sr, obs_md, obs_sd = block_bootstrap_pvalues(
        rets[gates].to_numpy(), rets[base_name].to_numpy())
    df.loc[df["name"] != base_name, "p_mean_boot"] = p_mean
    df.loc[df["name"] != base_name, "p_sharpe_boot"] = p_sr
    df.loc[df["name"] != base_name, "p_mean_holm"] = holm(p_mean)
    df.loc[df["name"] != base_name, "p_mean_bh"] = bh(p_mean)
    df.loc[df["name"] != base_name, "p_sharpe_holm"] = holm(p_sr)
    df.loc[df["name"] != base_name, "p_sharpe_bh"] = bh(p_sr)

    df = df.sort_values("sharpe_ann", ascending=False).reset_index(drop=True)

    pd.set_option("display.width", 260)
    pd.set_option("display.max_columns", 40)
    print("\n=== VM baseline (0.30% per side, 4 stitched OOS folds) ===")
    print(df.loc[df["name"] == base_name, [
        "name", "compound_pct", "cagr_pct", "sharpe_ann", "path_dd_pct",
        "folds_pos", "avg_exposure", "fold_rets_pct"]].round(4).to_string(index=False))

    print("\n=== Gate family: top 15 by annualised OOS Sharpe ===")
    cols = ["name", "family", "compound_pct", "cagr_pct", "sharpe_ann",
            "path_dd_pct", "avg_exposure", "sharpe_diff_vs_base",
            "p_mean_boot", "p_mean_holm"]
    print(df.head(15)[cols].round(4).to_string(index=False))

    print("\n=== Selected named variants ===")
    sel = ["none", "sar_0.02_0.15", "cci20_0", "pctb_0.4",
           "sma50_b+0.00", "sma100_b+0.00", "sma200_b+0.00"]
    scols = ["name", "compound_pct", "cagr_pct", "sharpe_ann", "path_dd_pct",
             "avg_exposure", "sharpe_diff_vs_base", "p_mean_boot", "p_mean_holm"]
    print(df[df["name"].isin(sel)].set_index("name").loc[
        [x for x in sel if x in set(df["name"])], scols[1:]].round(4).to_string())

    best = df.iloc[0]
    best_name = str(best["name"])
    sr_trials = rets.mean() / rets.std() * math.sqrt(365.0)
    var_daily = float(np.var(sr_trials / math.sqrt(365.0), ddof=1))
    var_ann = float(np.var(sr_trials, ddof=1))
    T = int(best["T"])

    print("\n=== (a) Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) ===")
    print("Inputs: trial Sharpe = daily mean/std (not annualised); "
          "Var[trial SR] is cross-variant sample variance (ddof=1).")
    print(f"  family size N={len(specs)}; T={T} daily OOS observations; "
          f"Var[trial SR_daily]={var_daily:.8f} (sd={math.sqrt(var_daily):.6f}); "
          f"Var[trial SR_ann]={var_ann:.6f}")
    print(f"  formula: SR0 = sqrt(Var[SR]) * [(1-g)*Phi^-1(1-1/N) + g*Phi^-1(1-1/(N*e))], "
          f"g={GAMMA:.6f}")
    print("  DSR = Phi((SR_hat - SR0)*sqrt(T-1) / sqrt(1 - skew*SR_hat + "
          "((kurt-1)/4)*SR_hat^2))")
    dcols = ["name", "sharpe_ann", "skew", "kurtosis"]
    dsr_rows = []
    for label, name in [("best by OOS Sharpe", best_name), ("SAR(0.02,0.15)", "sar_0.02_0.15")]:
        r = df.loc[df["name"] == name].iloc[0]
        sr_d = float(r["sharpe_ann"]) / math.sqrt(365.0)
        for N in (len(specs), 224000):
            d = dsr(sr_d, int(r["T"]), float(r["skew"]), float(r["kurtosis"]),
                    var_daily, N)
            dsr_rows.append({"label": label, "name": name, "N": N,
                             "sharpe_ann": float(r["sharpe_ann"]),
                             "sr0_ann": d["sr0_daily"] * math.sqrt(365.0),
                             "dsr": d["dsr"], "z": d["z"]})
    ddf = pd.DataFrame(dsr_rows)
    print(ddf.round(6).to_string(index=False))
    print("  (SR0 shown annualised; z and the DSR are invariant to annualisation.)")
    print("  best variant inputs:", df.loc[df["name"] == best_name, dcols].round(4).to_dict("records")[0])

    print("\n=== (b) Probability of Backtest Overfitting (CSCV) ===")
    pb = pbo_cscv(rets)
    print(pb)
    print("  interpretation: PBO = share of all IS/OOS splits where the IS-best "
          "variant lands in the bottom half OOS.")

    print("\n=== (c) Paired gate vs VM baseline (block bootstrap) ===")
    print(f"  circular block bootstrap, L={BLOCK_LEN} days, B={N_BOOT}, seed={SEED}; "
          "one-sided H1: gate > baseline")
    n = len(gates)
    print(f"  raw p<0.05: mean-diff {int(np.sum(p_mean < 0.05))}/{n}; "
          f"Sharpe-diff {int(np.sum(p_sr < 0.05))}/{n}")
    print(f"  Holm p<0.05: mean-diff {int(np.sum(df['p_mean_holm'] < 0.05))}/{n}; "
          f"Sharpe-diff {int(np.sum(df['p_sharpe_holm'] < 0.05))}/{n}")
    print(f"  BH   p<0.05: mean-diff {int(np.sum(df['p_mean_bh'] < 0.05))}/{n}; "
          f"Sharpe-diff {int(np.sum(df['p_sharpe_bh'] < 0.05))}/{n}")
    pcols = ["name", "sharpe_diff_vs_base", "p_mean_boot", "p_mean_holm",
             "p_sharpe_boot", "p_sharpe_holm"]
    print("  smallest mean-diff p-values:")
    print(df[df["name"] != base_name].nsmallest(10, "p_mean_boot")[pcols]
          .round(5).to_string(index=False))
    hb = df[(df["name"] != base_name) & (df["p_mean_holm"] < 0.05)]
    print(f"  variants surviving Holm on mean daily return ({len(hb)}): "
          + (", ".join(hb["name"]) if len(hb) else "none"))

    print("\n=== (d) How many gates beat VM baseline ===")
    g = df[df["name"] != base_name]
    print(f"  N gates = {len(g)}")
    print(f"  Sharpe: {int((g['sharpe_ann'] > float(base['sharpe_ann'])).sum())}/{len(g)} "
          f"({(g['sharpe_ann'] > float(base['sharpe_ann'])).mean() * 100:.1f}%)")
    print(f"  path max DD (smaller): "
          f"{int((g['path_dd_pct'] > float(base['path_dd_pct'])).sum())}/{len(g)} "
          f"({(g['path_dd_pct'] > float(base['path_dd_pct'])).mean() * 100:.1f}%)")
    print(f"  compound return: "
          f"{int((g['compound_pct'] > float(base['compound_pct'])).sum())}/{len(g)} "
          f"({(g['compound_pct'] > float(base['compound_pct'])).mean() * 100:.1f}%)")
    print(f"  both Sharpe and path DD: "
          f"{int(((g['sharpe_ann'] > float(base['sharpe_ann'])) & (g['path_dd_pct'] > float(base['path_dd_pct']))).sum())}/{len(g)}")
    print("  median changes vs baseline: "
          f"Sharpe {g['sharpe_ann'].median() - float(base['sharpe_ann']):+.3f}, "
          f"path DD {g['path_dd_pct'].median() - float(base['path_dd_pct']):+.2f} pp, "
          f"compound {g['compound_pct'].median() - float(base['compound_pct']):+.1f} pp")

    print("\n=== median by family (vs baseline) ===")
    fam = (df[df["name"] != base_name].groupby("family")
           .agg(n=("name", "size"),
                median_sharpe=("sharpe_ann", "median"),
                median_dd=("path_dd_pct", "median"),
                median_compound=("compound_pct", "median"),
                beat_sharpe=("sharpe_diff_vs_base", lambda x: int((x > 0).sum())),
                beat_dd=("delta_path_dd_pp", lambda x: int((x > 0).sum()))))
    print(fam.round(4).to_string())

    out = df.copy()
    out.to_csv(HERE / "variants.csv", index=False, float_format="%.6f")
    print(f"\nwrote {HERE / 'variants.csv'} ({len(out)} rows)")
    print("done.")


if __name__ == "__main__":
    orig = sys.stdout

    class Tee:
        def __init__(self, path, stream):
            self.f = open(path, "w", encoding="utf-8")
            self.stream = stream

        def write(self, s):
            self.stream.write(s)
            self.f.write(s)

        def flush(self):
            self.stream.flush()
            self.f.flush()

    sys.stdout = Tee(HERE / "run_output.txt", orig)
    try:
        main()
    finally:
        sys.stdout.flush()
        sys.stdout = orig
