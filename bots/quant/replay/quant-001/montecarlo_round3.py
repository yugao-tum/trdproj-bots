#!/usr/bin/env python3
"""quant-001 round-3 robustness: precise placebo p-values + block bootstrap.

Why this file exists
--------------------
The main replay (`run_replay.py`) uses 1,000 circular-shift placebos.  Two of
the reported p-values (0.052 and 0.065) are close enough to 0.05 that Monte
Carlo error matters.  This script re-runs the *same* placebo design with
20,000 shifts and adds a stationary block bootstrap (Politis & Romano, 1994)
for the CAGR/Sharpe difference between the recommended SMA50 gate and the two
benchmarks.  It is a statistical-precision check, not a new trading rule, so
it does not add variants.

Everything is inside the allowed window 2022-01-01..2024-12-31; fills are the
next daily bar open; cost is 0.30% per side, exactly as `run_replay.py`.

Run: python3 bots/quant/replay/quant-001/montecarlo_round3.py
Outputs: montecarlo_results.json, montecarlo_stdout.txt
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_replay as rr  # noqa: E402

N_PLACEBO = 20000
N_BOOT = 5000
BLOCK_MEAN = 10.0
SEED = 20261022


def build_arrays():
    panels = {s: rr.load(s) for s in rr.SYMS}
    close = pd.DataFrame({s: panels[s]["close"] for s in rr.SYMS}).dropna()
    open_ = pd.DataFrame({s: panels[s]["open"] for s in rr.SYMS}).reindex(close.index)
    btc_close = panels["BTC"]["close"].reindex(close.index)
    w_vm = rr.vm_signal(close)
    eval_start = max(w_vm.index[(w_vm.sum(axis=1) > 0)][0],
                     btc_close.rolling(200).mean().first_valid_index())
    w_sig = w_vm.shift(1).fillna(0.0).values.astype(float)
    r = (open_.shift(-1) / open_ - 1.0).values.astype(float)
    keep_shift = {}
    for n in (50, 100, 200):
        keep_shift[n] = rr.gate_signal(btc_close, n).shift(1).fillna(0.0).values.astype(float)
    return close.index, w_sig, r, keep_shift, eval_start


def net_from_gate(w_sig, r, gate):
    w = w_sig * gate[:, None]
    turn = np.empty(len(w))
    turn[0] = np.abs(w[0]).sum()
    turn[1:] = np.abs(np.diff(w, axis=0)).sum(axis=1)
    net = (w * r).sum(axis=1) - turn * rr.FEE
    return net


def stats(net):
    eq = np.cumprod(1.0 + net)
    comp = float(eq[-1] - 1.0)
    years = len(net) / 365.0
    cagr = float((1.0 + comp) ** (1.0 / years) - 1.0) if years > 0 else np.nan
    dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())
    sd = float(net.std())
    sharpe = float(net.mean() / sd * np.sqrt(365.0)) if sd > 0 else np.nan
    return comp * 100.0, cagr * 100.0, dd * 100.0, sharpe


def main():
    idx, w_sig, r, keep_shift, eval_start = build_arrays()
    T = len(idx)
    start = idx.get_loc(eval_start)
    valid = np.arange(T) < T - 1  # last row has NaN next-open return
    sl = slice(start, T - 1)

    # actual variants (same definition as run_replay.py)
    actual = {}
    base_net = net_from_gate(w_sig, r, np.ones(T))[sl]
    actual["VM"] = stats(base_net)
    gate_actual = {}
    for n in (50, 100, 200):
        net = net_from_gate(w_sig, r, keep_shift[n])[sl]
        actual[f"VM_x_SMA{n}"] = stats(net)
        gate_actual[n] = actual[f"VM_x_SMA{n}"]

    # ex-post constant scaling matched to average exposure
    vm_expo = float(np.abs(w_sig * np.ones((T, 1)))[sl].sum(axis=1).mean())
    const = {}
    for n in (50, 100, 200):
        g = keep_shift[n]
        gate_expo = float(np.abs(w_sig * g[:, None])[sl].sum(axis=1).mean())
        k = gate_expo / vm_expo
        net = net_from_gate(w_sig * k, r, np.ones(T))[sl]
        const[n] = stats(net)
        actual[f"const_scale_SMA{n}"] = const[n]

    rng = np.random.default_rng(SEED)
    shifts = rng.integers(1, T, size=N_PLACEBO)
    draw_comp = {n: np.empty(N_PLACEBO) for n in (50, 100, 200)}
    draw_dd = {n: np.empty(N_PLACEBO) for n in (50, 100, 200)}
    draw_sh = {n: np.empty(N_PLACEBO) for n in (50, 100, 200)}
    fam_comp = np.empty(N_PLACEBO)
    fam_dd = np.empty(N_PLACEBO)
    fam_sh = np.empty(N_PLACEBO)
    for d, s in enumerate(shifts):
        comps, dds, shs = [], [], []
        for n in (50, 100, 200):
            rolled = np.roll(keep_shift[n], int(s))
            net = net_from_gate(w_sig, r, rolled)[sl]
            c, _, dd, sh = stats(net)
            draw_comp[n][d], draw_dd[n][d], draw_sh[n][d] = c, dd, sh
            comps.append(c)
            dds.append(dd)
            shs.append(sh)
        fam_comp[d], fam_dd[d], fam_sh[d] = max(comps), max(dds), max(shs)

    single = {}
    for n in (50, 100, 200):
        c, _, dd, sh = gate_actual[n]
        single[n] = {
            "p_compound_ge_actual": float((draw_comp[n] >= c).mean()),
            "p_dd_le_actual": float((draw_dd[n] <= dd).mean()),
            "p_sharpe_ge_actual": float((draw_sh[n] >= sh).mean()),
            "draws": N_PLACEBO,
        }

    best_c = max(gate_actual[n][0] for n in (50, 100, 200))
    best_dd = max(gate_actual[n][2] for n in (50, 100, 200))
    best_sh = max(gate_actual[n][3] for n in (50, 100, 200))
    family = {
        "p_family_compound": float((fam_comp >= best_c).mean()),
        "p_family_dd": float((fam_dd >= best_dd).mean()),
        "p_family_sharpe": float((fam_sh >= best_sh).mean()),
        "best_compound_pct": best_c,
        "best_dd_pct": best_dd,
        "best_sharpe": best_sh,
        "draws": N_PLACEBO,
    }

    # stationary block bootstrap of daily net returns, common indices across
    # variants so that paired differences keep their cross-correlation.
    names = ["VM", "VM_x_SMA50", "VM_x_SMA100", "const_scale_SMA50"]
    k50 = float(np.abs(w_sig * keep_shift[50][:, None])[sl].sum(axis=1).mean()) / vm_expo
    nets = {
        "VM": base_net,
        "VM_x_SMA50": net_from_gate(w_sig, r, keep_shift[50])[sl],
        "VM_x_SMA100": net_from_gate(w_sig, r, keep_shift[100])[sl],
        "const_scale_SMA50": net_from_gate(w_sig * k50, r, np.ones(T))[sl],
    }

    n = len(base_net)
    boot = {name: {"cagr": np.empty(N_BOOT), "sharpe": np.empty(N_BOOT),
                   "dd": np.empty(N_BOOT)} for name in names}
    brng = np.random.default_rng(SEED + 1)
    p_geom = 1.0 / BLOCK_MEAN
    for b in range(N_BOOT):
        sample = np.empty(n, dtype=int)
        i = 0
        while i < n:
            start_i = int(brng.integers(0, n))
            length = int(brng.geometric(p_geom))
            for j in range(length):
                if i >= n:
                    break
                sample[i] = (start_i + j) % n
                i += 1
        for name in names:
            c, _, dd, sh = stats(nets[name][sample])
            boot[name]["cagr"][b] = c
            boot[name]["dd"][b] = dd
            boot[name]["sharpe"][b] = sh

    def pct(a, q):
        return float(np.percentile(a, q))

    # A paired block bootstrap of the *mean daily return difference* is the
    # clean test for "SMA50 adds return over the benchmark".  We deliberately
    # do NOT use the percentile bootstrap of the CAGR difference as a p-value:
    # resampling with replacement plus compounding shifts that distribution
    # upward (its median is far above the actual +12.1 pp difference), so it
    # would overstate significance.  The CAGR CI is descriptive only.
    diffs = {}
    for name in ("VM", "const_scale_SMA50"):
        d_daily = nets["VM_x_SMA50"] - nets[name]
        md = float(d_daily.mean())
        centered = d_daily - md
        null_means = np.empty(N_BOOT)
        for b in range(N_BOOT):
            sample = np.empty(n, dtype=int)
            i = 0
            while i < n:
                start_i = int(brng.integers(0, n))
                length = int(brng.geometric(p_geom))
                for j in range(length):
                    if i >= n:
                        break
                    sample[i] = (start_i + j) % n
                    i += 1
            null_means[b] = centered[sample].mean()
        # descriptive CI of the CAGR difference (biased upward; not a p-value)
        d_cagr = boot["VM_x_SMA50"]["cagr"] - boot[name]["cagr"]
        ds = boot["VM_x_SMA50"]["sharpe"] - boot[name]["sharpe"]
        diffs[name] = {
            "cagr_diff_actual_pct": float(stats(nets["VM_x_SMA50"])[1]
                                          - stats(nets[name])[1]),
            "cagr_diff_boot_p05_p50_p95_descriptive": [pct(d_cagr, 5),
                                                       pct(d_cagr, 50), pct(d_cagr, 95)],
            "mean_daily_diff_pct": md * 100.0,
            "mean_daily_diff_annualised_approx_pct": md * 365.0 * 100.0,
            "p_mean_daily_diff_le_0_centered": float((null_means >= md).mean()),
            "sharpe_diff_actual": (stats(nets["VM_x_SMA50"])[3] - stats(nets[name])[3]),
            "sharpe_diff_boot_p05_p50_p95_descriptive": [pct(ds, 5), pct(ds, 50), pct(ds, 95)],
        }
    p_sma_above_8 = float((boot["VM_x_SMA50"]["cagr"] > 8.0).mean())

    out = {
        "generated_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": "2022-01-01..2024-12-31",
        "eval_start": str(eval_start.date()),
        "fee_per_side": rr.FEE,
        "fill": "next daily bar open",
        "placebo_draws": N_PLACEBO,
        "actual": actual,
        "single_gate_placebo": single,
        "familywise": family,
        "bootstrap": {
            "draws": N_BOOT, "block_mean_days": BLOCK_MEAN,
            "p_sma50_cagr_above_8pct": p_sma_above_8,
            "variants": {name: {
                "cagr_p05_p50_p95": [pct(boot[name]["cagr"], 5),
                                     pct(boot[name]["cagr"], 50),
                                     pct(boot[name]["cagr"], 95)],
                "sharpe_p05_p50_p95": [pct(boot[name]["sharpe"], 5),
                                       pct(boot[name]["sharpe"], 50),
                                       pct(boot[name]["sharpe"], 95)],
                "dd_p05_p50_p95": [pct(boot[name]["dd"], 5),
                                   pct(boot[name]["dd"], 50),
                                   pct(boot[name]["dd"], 95)],
            } for name in names},
            "paired_diffs": diffs,
        },
    }

    lines = []
    lines.append("quant-001 round-3 Monte Carlo / block bootstrap")
    lines.append(f"window {out['window']}, eval start {out['eval_start']}, "
                 f"{len(base_net)} days, fee {rr.FEE*100:.2f}%/side, next-open fills")
    lines.append("")
    lines.append(f"placebo design: {N_PLACEBO:,} circular shifts of the same gate "
                 "(same design as run_replay.py, more draws)")
    for n_ in (50, 100, 200):
        s = single[n_]
        lines.append(f"  SMA{n_}: p(compound>=actual)={s['p_compound_ge_actual']:.4f} "
                     f"p(DD<=actual)={s['p_dd_le_actual']:.4f} "
                     f"p(Sharpe>=actual)={s['p_sharpe_ge_actual']:.4f}")
    lines.append(f"  family max-statistic (best actual SMA100): "
                 f"p(compound)={family['p_family_compound']:.4f} "
                 f"p(DD)={family['p_family_dd']:.4f} "
                 f"p(Sharpe)={family['p_family_sharpe']:.4f}")
    lines.append("  Monte Carlo s.e. at p=0.05 with 20,000 draws = 0.0015")
    lines.append("")
    lines.append(f"stationary block bootstrap: {N_BOOT:,} draws, mean block "
                 f"{BLOCK_MEAN:.0f} days, paired indices")
    for name in names:
        v = out["bootstrap"]["variants"][name]
        lines.append(f"  {name:<18} CAGR 5/50/95={v['cagr_p05_p50_p95'][0]:+.1f}/"
                     f"{v['cagr_p05_p50_p95'][1]:+.1f}/{v['cagr_p05_p50_p95'][2]:+.1f}% "
                     f"Sharpe={v['sharpe_p05_p50_p95'][0]:+.2f}/"
                     f"{v['sharpe_p05_p50_p95'][1]:+.2f}/"
                     f"{v['sharpe_p05_p50_p95'][2]:+.2f} "
                     f"DD={v['dd_p05_p50_p95'][0]:+.1f}/"
                     f"{v['dd_p05_p50_p95'][1]:+.1f}/"
                     f"{v['dd_p05_p50_p95'][2]:+.1f}%")
    for name in ("VM", "const_scale_SMA50"):
        d = diffs[name]
        lines.append(f"  SMA50 - {name}: actual CAGR diff={d['cagr_diff_actual_pct']:+.2f} pp; "
                     f"bootstrap CAGR diff p05/p50/p95="
                     f"{d['cagr_diff_boot_p05_p50_p95_descriptive'][0]:+.1f}/"
                     f"{d['cagr_diff_boot_p05_p50_p95_descriptive'][1]:+.1f}/"
                     f"{d['cagr_diff_boot_p05_p50_p95_descriptive'][2]:+.1f} pp "
                     "(descriptive, upward-biased; not a p-value); "
                     f"mean daily diff={d['mean_daily_diff_pct']:+.4f}%/day "
                     f"({d['mean_daily_diff_annualised_approx_pct']:+.1f}%/yr); "
                     f"centered block-bootstrap p(diff<=0)="
                     f"{d['p_mean_daily_diff_le_0_centered']:.4f}")
        lines.append(f"    Sharpe diff actual={d['sharpe_diff_actual']:+.3f}; "
                     f"bootstrap p05/p50/p95="
                     f"{d['sharpe_diff_boot_p05_p50_p95_descriptive'][0]:+.2f}/"
                     f"{d['sharpe_diff_boot_p05_p50_p95_descriptive'][1]:+.2f}/"
                     f"{d['sharpe_diff_boot_p05_p50_p95_descriptive'][2]:+.2f} "
                     "(descriptive only)")
    lines.append(f"  P(SMA50 bootstrap CAGR > 8%) = {p_sma_above_8:.4f} "
                 "(descriptive; compounding-biased)")
    lines.append("")
    text = "\n".join(lines)
    print(text)
    (HERE / "montecarlo_stdout.txt").write_text(text + "\n")
    (HERE / "montecarlo_results.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
