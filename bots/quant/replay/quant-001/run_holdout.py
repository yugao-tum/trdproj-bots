#!/usr/bin/env python3
"""quant-001: temporal hold-out and walk-forward gate selection.

Purpose
-------
The main replay (`run_replay.py`) evaluates the frozen SMA gates over the whole
2022-07-19..2024-12-31 period.  That is a frozen-rule recomputation, not a blind
out-of-sample test: the original research may have seen 2022 and 2024.  This
script adds two pre-registered diagnostics that use only the allowed
2022-01-01..2024-12-31 window:

1. Calendar sub-periods.  Development = 2022-07-19..2023-12-31, hold-out =
   2024-01-01..2024-12-31.  Same frozen rules, no refitting.  This is a
   temporal split, not a blind hold-out (the rule family was known before).
2. Walk-forward gate choice.  At 2023-01-01, 2023-07-01, 2024-01-01 and
   2024-07-01 pick the gate (VM, SMA50, SMA100, SMA200) with the highest
   trailing 365-day net Sharpe using only returns already realised at that
   date, then apply it for the next six months.  Costs 0.30%/side, next-open
   fills, exactly as `run_replay.py`.

Nothing here downloads or reads 2021 or 2025+ data.

Run: python3 bots/quant/replay/quant-001/run_holdout.py
Outputs: holdout_results.json, holdout_stdout.txt next to this file.
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import run_replay as rr  # noqa: E402

SPLITS = {
    "development": ("2022-07-19", "2023-12-31"),
    "holdout_2024": ("2024-01-01", "2024-12-31"),
}
DECISIONS = ["2023-01-01", "2023-07-01", "2024-01-01", "2024-07-01"]
TRAIL_DAYS = 365
MIN_TRAIL = 60


def sharpe(net):
    if len(net) < MIN_TRAIL or net.std() == 0:
        return float("-inf")
    return float(net.mean() / net.std() * np.sqrt(365))


def build():
    panels = {s: rr.load(s) for s in rr.SYMS}
    close = pd.DataFrame({s: panels[s]["close"] for s in rr.SYMS}).dropna()
    open_ = pd.DataFrame({s: panels[s]["open"] for s in rr.SYMS}).reindex(close.index)
    btc_close = panels["BTC"]["close"].reindex(close.index)
    w_vm = rr.vm_signal(close)
    eval_start = max(w_vm.index[(w_vm.sum(axis=1) > 0)][0],
                     btc_close.rolling(200).mean().first_valid_index())

    series = {}
    net, w = rr.run(close, open_, w_vm, start=None)
    series["VM"] = (net, w)
    keep_map = {}
    for n in (50, 100, 200):
        keep = rr.gate_signal(btc_close, n)
        keep_map[n] = keep
        net, w = rr.run(close, open_, w_vm, keep, start=None)
        series[f"VM_x_SMA{n}"] = (net, w)
    return series, eval_start, keep_map


def metrics(net, w, start, end):
    s = net.loc[pd.Timestamp(start):pd.Timestamp(end)]
    ww = w.loc[s.index]
    return rr.metrics(s, ww)


def roll_forward(series, eval_start):
    names = list(series)
    idx = series["VM"][0].index
    idx = idx[idx >= pd.Timestamp(DECISIONS[0])]
    stitched, chosen_w = [], []
    history = []
    boundaries = [pd.Timestamp(d) for d in DECISIONS] + [idx[-1] + pd.Timedelta(days=1)]
    for k in range(len(boundaries) - 1):
        d, nxt = boundaries[k], boundaries[k + 1]
        trail_start = max(pd.Timestamp(eval_start), d - pd.Timedelta(days=TRAIL_DAYS))
        trail = {name: series[name][0].loc[trail_start:d - pd.Timedelta(days=1)]
                 for name in names}
        scores = {name: sharpe(trail[name]) for name in names}
        best = max(scores, key=lambda x: (scores[x], -list(names).index(x)))
        seg_idx = idx[(idx >= d) & (idx < nxt)]
        stitched.append(series[best][0].loc[seg_idx])
        chosen_w.append(series[best][1].loc[seg_idx])
        history.append({
            "decision": str(d.date()),
            "apply_until": str((nxt - pd.Timedelta(days=1)).date()),
            "trailing_start": str(trail_start.date()),
            "trailing_days": int(len(trail["VM"])),
            "chosen": best,
            "trailing_sharpe": {name: (None if not np.isfinite(scores[name]) else round(scores[name], 4))
                                for name in names},
            "trailing_return_pct": {name: round(float((1 + trail[name]).prod() - 1) * 100, 2)
                                    for name in names},
        })
    net = pd.concat(stitched).sort_index()
    w = pd.concat(chosen_w).sort_index()
    return net, w, history


def main():
    series, eval_start, _ = build()
    out = {"window": "2022-01-01..2024-12-31",
           "eval_start": str(eval_start.date()),
           "fee_per_side": rr.FEE,
           "fill": "next daily bar open",
           "splits": {}, "walk_forward": {}}
    lines = ["quant-001 temporal hold-out / walk-forward (0.30%/side, next-open fills)",
             f"data span: {series['VM'][0].index.min().date()}..{series['VM'][0].index.max().date()}"
             f" (only 2022-01-01..2024-12-31 downloaded)",
             f"common eval start: {eval_start.date()}", ""]

    for label, (a, b) in SPLITS.items():
        out["splits"][label] = {}
        lines.append(f"[{label}] {a}..{b}")
        for name, (net, w) in series.items():
            m = metrics(net, w, a, b)
            out["splits"][label][name] = m
            lines.append(f"  {name:<14} compound={m['compound_pct']:+8.2f}% "
                         f"cagr={m['cagr_pct']:+7.2f}% dd={m['max_dd_pct']:+7.2f}% "
                         f"sharpe={m['sharpe']:+.3f} expo={m['avg_exposure']:.3f} "
                         f"days={m['days']}")
        lines.append("")

    net_wf, w_wf, history = roll_forward(series, eval_start)
    m_wf = rr.metrics(net_wf, w_wf)
    out["walk_forward"] = {"metrics": m_wf, "history": history,
                           "decisions": DECISIONS, "trailing_days": TRAIL_DAYS,
                           "selection": "highest trailing net Sharpe; ties -> earlier list order"}
    lines.append("[walk-forward gate selection] " + " / ".join(DECISIONS))
    for h in history:
        lines.append(f"  {h['decision']} -> {h['chosen']} until {h['apply_until']} "
                     f"(trailing {h['trailing_start']}.., n={h['trailing_days']}); "
                     f"trailing Sharpe=" + ", ".join(
                         f"{k}:{'na' if v is None else v}" for k, v in h['trailing_sharpe'].items()))
    lines.append(f"  stitched: compound={m_wf['compound_pct']:+.2f}% "
                 f"cagr={m_wf['cagr_pct']:+.2f}% dd={m_wf['max_dd_pct']:+.2f}% "
                 f"sharpe={m_wf['sharpe']:+.3f} expo={m_wf['avg_exposure']:.3f} "
                 f"days={m_wf['days']}")
    for name in ("VM", "VM_x_SMA50", "VM_x_SMA100", "VM_x_SMA200"):
        m = metrics(series[name][0], series[name][1], str(net_wf.index.min().date()),
                    "2024-12-31")
        lines.append(f"  same span, always-{name:<12} compound={m['compound_pct']:+.2f}% "
                     f"cagr={m['cagr_pct']:+.2f}% dd={m['max_dd_pct']:+.2f}% "
                     f"sharpe={m['sharpe']:+.3f}")
    lines.append("")
    text = "\n".join(lines)
    print(text)
    (HERE / "holdout_stdout.txt").write_text(text + "\n")
    (HERE / "holdout_results.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
