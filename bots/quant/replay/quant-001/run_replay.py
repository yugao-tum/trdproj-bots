#!/usr/bin/env python3
"""quant-001 round-2 replay: tradable prices, 2022-01-01..2024-12-31 only.

Mechanism (frozen, same as the entry / notes/xqt-migration/reproduce.py):
  * universe: BTC, ETH, SOL spot (USDT)
  * momentum: 30-day return skipping the most recent day
  * hold coins with positive momentum, equal weight
  * scale the whole sleeve by min(1, 15% / annualised 4-week vol of the
    unscaled sleeve), recompute every 5 trading days
  * BTC trend gate: hold only if BTC close >= n-day SMA (n = 50/100/200)
  * long-only spot, no leverage

Round-2 execution rules (GUIDE sec. 9):
  * signal at daily close t; fill at the OPEN of the next daily bar t+1
  * one-hour data are NOT used as a fill proxy here; the daily open is the
    first traded price of that bar
  * 0.30% cost per side on |change in target weight|
  * development window starts 2022-01-01; indicator warm-up is inside the
    window, so the first months are in cash
  * no 2021 or earlier data and no 2025+ data are downloaded or read

Data: keyless Binance public REST endpoint
  https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d
Raw responses are cached under
  bots/quant/notes/scheduler/scratch/H-quant-001/_cache/klines1d/
(gitignored, never committed).

Run: python3 bots/quant/replay/quant-001/run_replay.py
Outputs: replay_results.json, replay_equity.csv, placebo_results.json,
         episodes_SMA*.csv and stdout next to this file.
"""
import json
import pathlib
import urllib.request

import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # .../bots/quant/replay/quant-001 -> repo root
CACHE = ROOT / "bots/quant/notes/scheduler/scratch/H-quant-001/_cache/klines1d"
SYMS = ["BTC", "ETH", "SOL"]
REBAL = 5
FEE = 0.003
START = pd.Timestamp("2022-01-01")
END = pd.Timestamp("2024-12-31")
BASE_URL = ("https://data-api.binance.vision/api/v3/klines"
            "?symbol={sym}USDT&interval=1d&startTime={start}&endTime={end}&limit=1000")
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_base", "taker_quote", "ignore"]


def _window_only(df):
    """Hard-filter a cached/downloaded frame to the allowed development window.

    The round-2 rules forbid reading 2021 or 2025+ data.  A stale or manually
    edited cache must never leak those dates into the replay, so every read
    goes through this filter and the caller asserts the result is non-empty.
    """
    ot = pd.to_datetime(df["open_time"], unit="ms", utc=True, errors="coerce")
    df = df.assign(open_time=ot)
    for c in ("open", "high", "low", "close", "volume", "quote_volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    lo, hi = START.tz_localize("UTC"), END.tz_localize("UTC")
    df = df[(df.open_time >= lo) & (df.open_time <= hi)].dropna(
        subset=["open", "high", "low", "close", "volume"]).reset_index(drop=True)
    return df[["open_time", "open", "high", "low", "close", "volume", "quote_volume"]]


def fetch(sym):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{sym}USDT-1d-2022-2024.csv"
    if path.exists():
        cached = _window_only(pd.read_csv(path))
        if len(cached) > 0:
            return cached
    frames, start_ms = [], int(START.timestamp() * 1000)
    end_ms = int((END + pd.Timedelta(days=1)).timestamp() * 1000) - 1
    while start_ms <= end_ms:
        url = BASE_URL.format(sym=sym, start=start_ms, end=end_ms)
        with urllib.request.urlopen(url, timeout=45) as r:
            rows = json.loads(r.read())
        if not rows:
            break
        frames.append(pd.DataFrame(rows, columns=COLS))
        start_ms = int(rows[-1][6]) + 1
        if len(rows) < 1000:
            break
    df = _window_only(pd.concat(frames, ignore_index=True))
    if df.empty:
        raise RuntimeError(f"{sym}: no bars inside {START.date()}..{END.date()}")
    df.to_csv(path, index=False)
    return df


def load(sym):
    d = fetch(sym).copy()
    d["date"] = d.open_time.dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None)
    d = d.set_index("date")[["open", "high", "low", "close", "volume", "quote_volume"]]
    assert d.index.min() >= START, (sym, d.index.min())
    assert d.index.max() <= END, (sym, d.index.max())
    return d


def freeze(w):
    return w.reindex(w.index[::REBAL]).reindex(w.index, method="ffill")


def vm_signal(close):
    mom = close.shift(1) / close.shift(31) - 1.0
    sel = (mom > 0).astype(float)
    w0 = sel.div(sel.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    sleeve = (freeze(w0).shift(1) * close.pct_change()).sum(axis=1)
    wvol = (sleeve.resample("W-FRI").sum().rolling(4).std() * np.sqrt(52)).shift(1)
    scale = (0.15 / wvol.reindex(close.index, method="ffill").replace(0, np.nan)).clip(0, 1)
    return freeze(w0.mul(scale, axis=0)).fillna(0.0)


def gate_signal(btc_close, n):
    sma = btc_close.rolling(n).mean()
    keep = (btc_close >= sma).astype(float)
    keep[sma.isna()] = 0.0  # warm-up inside the window = cash, never look back
    return keep


def run(close, open_, w_signal, keep=None, start=None):
    w_entry = w_signal.shift(1).fillna(0.0)
    if keep is not None:
        w_entry = w_entry.mul(keep.shift(1).fillna(0.0), axis=0)
    r_entry = (open_.shift(-1) / open_ - 1.0)
    turn = w_entry.diff().abs().sum(axis=1).fillna(w_entry.abs().sum(axis=1))
    net = (w_entry * r_entry).sum(axis=1) - turn * FEE
    net = net.dropna()
    if start is not None:
        net = net.loc[start:]
    return net, w_entry.loc[net.index]


def metrics(net, w):
    eq = (1 + net).cumprod()
    dd = float((eq / eq.cummax() - 1).min() * 100)
    years = len(net) / 365.0
    comp = float(eq.iloc[-1] - 1)
    cagr = float((1 + comp) ** (1 / years) - 1) if years > 0 else np.nan
    sharpe = float(net.mean() / net.std() * np.sqrt(365)) if net.std() > 0 else np.nan
    yearly = {str(y): float((1 + net[net.index.year == y]).prod() - 1)
              for y in sorted(set(net.index.year))}
    return {"compound_pct": comp * 100, "cagr_pct": cagr * 100,
            "max_dd_pct": dd, "sharpe": sharpe,
            "avg_exposure": float(w.sum(axis=1).mean()),
            "days": int(len(net)), "yearly_pct": yearly}


def episodes(keep_entry, base_net, start=None):
    if start is not None:
        keep_entry = keep_entry.loc[start:]
    off = keep_entry.fillna(0).eq(0).values
    idx = keep_entry.index
    runs, i = [], 0
    while i < len(off):
        if off[i]:
            j = i
            while j + 1 < len(off) and off[j + 1]:
                j += 1
            runs.append((idx[i], idx[j]))
            i = j + 1
        else:
            i += 1
    rows = []
    for a, b in runs:
        sub = base_net.loc[a:b]
        if len(sub) == 0:
            continue
        rows.append({"start": a.date().isoformat(), "end": b.date().isoformat(),
                     "days": int(len(sub)),
                     "vm_ret_pct": float(((1 + sub).prod() - 1) * 100)})
    return pd.DataFrame(rows)


def placebo(close, open_, w_signal, keep, base_net, actual, start, n_draw=1000, seed=20261021):
    rng = np.random.default_rng(seed)
    arr = keep.shift(1).fillna(0.0).values.astype(float)
    comps, dds, shs = [], [], []
    for _ in range(n_draw):
        rolled = pd.Series(np.roll(arr, int(rng.integers(1, len(arr)))),
                           index=keep.index)
        we = w_signal.shift(1).fillna(0.0).mul(rolled, axis=0)
        r_entry = (open_.shift(-1) / open_ - 1.0)
        turn = we.diff().abs().sum(axis=1).fillna(we.abs().sum(axis=1))
        net = ((we * r_entry).sum(axis=1) - turn * FEE).dropna().loc[start:]
        eq = (1 + net).cumprod()
        comps.append(eq.iloc[-1] - 1)
        dds.append((eq / eq.cummax() - 1).min())
        shs.append(net.mean() / net.std() * np.sqrt(365))
    comps, dds, shs = np.array(comps), np.array(dds), np.array(shs)
    return {"draws": n_draw,
            "p_compound_ge_actual": float((comps >= actual["compound_pct"] / 100).mean()),
            "p_dd_le_actual": float((dds <= actual["max_dd_pct"] / 100).mean()),
            "p_sharpe_ge_actual": float((shs >= actual["sharpe"]).mean()),
            "compound_p50_pct": float(np.median(comps) * 100),
            "compound_p95_pct": float(np.percentile(comps, 95) * 100),
            "dd_p5_pct": float(np.percentile(dds, 5) * 100),
            "dd_p50_pct": float(np.median(dds) * 100)}




def familywise(close, open_, w_signal, keep_map, actual, start, n_draw=1000, seed=20261021):
    """Same circular shifts for SMA50/100/200; max-statistic correction."""
    rng = np.random.default_rng(seed)
    n = len(close)
    arrs = {k: v.shift(1).fillna(0.0).values.astype(float) for k, v in keep_map.items()}
    r_entry = (open_.shift(-1) / open_ - 1.0)
    draws = {"compound": [], "dd": [], "sharpe": []}
    gates = [k for k in actual if k.startswith("VM_x_SMA")]
    for _ in range(n_draw):
        shift = int(rng.integers(1, n))
        comps, dds, shs = [], [], []
        for k, arr in arrs.items():
            rolled = pd.Series(np.roll(arr, shift), index=close.index)
            we = w_signal.shift(1).fillna(0.0).mul(rolled, axis=0)
            turn = we.diff().abs().sum(axis=1).fillna(we.abs().sum(axis=1))
            net = ((we * r_entry).sum(axis=1) - turn * FEE).dropna().loc[start:]
            eq = (1 + net).cumprod()
            comps.append(eq.iloc[-1] - 1)
            dds.append((eq / eq.cummax() - 1).min())
            shs.append(net.mean() / net.std() * np.sqrt(365))
        draws["compound"].append(max(comps))
        draws["dd"].append(max(dds))
        draws["sharpe"].append(max(shs))
    best_comp = max(actual[k]["compound_pct"] / 100 for k in gates)
    best_dd = max(actual[k]["max_dd_pct"] / 100 for k in gates)
    best_sh = max(actual[k]["sharpe"] for k in gates)
    return {"draws": n_draw,
            "best_compound_pct": best_comp * 100,
            "best_dd_pct": best_dd * 100,
            "best_sharpe": best_sh,
            "p_family_compound": float((np.array(draws["compound"]) >= best_comp).mean()),
            "p_family_dd": float((np.array(draws["dd"]) >= best_dd).mean()),
            "p_family_sharpe": float((np.array(draws["sharpe"]) >= best_sh).mean())}


def main():
    panels = {s: load(s) for s in SYMS}
    close = pd.DataFrame({s: panels[s]["close"] for s in SYMS}).dropna()
    open_ = pd.DataFrame({s: panels[s]["open"] for s in SYMS}).reindex(close.index)
    btc_close = panels["BTC"]["close"].reindex(close.index)
    w_vm = vm_signal(close)
    # common evaluation start: all indicators are defined here, so no variant gets
    # a cash-in-warm-up advantage during the 2022 bear market.
    eval_start = max(w_vm.index[(w_vm.sum(axis=1) > 0)][0],
                     btc_close.rolling(200).mean().first_valid_index())

    results, lines = {}, []
    lines.append("quant-001 round-2 replay — tradable next-open fills, 0.30%/side")
    lines.append(f"data: Binance daily klines (UTC), {close.index.min().date()}.."
                 f"{close.index.max().date()}, {len(close)} rows per symbol")
    lines.append(f"common evaluation start after warm-up: {eval_start.date()}")
    lines.append("fill: OPEN of the next daily bar after the signal close; no 2021/2025 data")
    lines.append("")

    base_net, base_w = run(close, open_, w_vm, start=eval_start)
    results["VM"] = metrics(base_net, base_w)

    keep_map = {}
    for n in (50, 100, 200):
        keep = gate_signal(btc_close, n)
        keep_map[n] = keep
        net, w = run(close, open_, w_vm, keep, start=eval_start)
        results[f"VM_x_SMA{n}"] = metrics(net, w)

    # ex-post constant-exposure diagnostic: k = gate avg exposure / VM avg exposure
    for n in (50, 100, 200):
        k = results[f"VM_x_SMA{n}"]["avg_exposure"] / results["VM"]["avg_exposure"]
        wc = w_vm * k
        net, w = run(close, open_, wc, start=eval_start)
        m = metrics(net, w)
        m["const_scale_k"] = float(k)
        results[f"const_scale_SMA{n}"] = m

    hdr = (f"{'variant':<20}{'compound%':>11}{'cagr%':>9}{'maxDD%':>9}"
           f"{'sharpe':>8}{'expo':>7}")
    lines.append(hdr)
    for name, m in results.items():
        lines.append(f"{name:<20}{m['compound_pct']:>11.2f}{m['cagr_pct']:>9.2f}"
                     f"{m['max_dd_pct']:>9.2f}{m['sharpe']:>8.3f}"
                     f"{m['avg_exposure']:>7.3f}")
    lines.append("")
    lines.append("yearly net returns (%):")
    for name, m in results.items():
        ys = " ".join(f"{y}:{v*100:+.1f}" for y, v in m["yearly_pct"].items())
        lines.append(f"  {name:<20}{ys}")
    lines.append("")

    # independent results: contiguous gate-off episodes inside the window
    lines.append("gate-off episodes (independent results):")
    ep_frames = {}
    for n in (50, 100, 200):
        keep = keep_map[n]
        keep_entry = keep.shift(1).fillna(0.0).loc[eval_start:]
        ep = episodes(keep_entry, base_net)
        ep_frames[n] = ep
        ep.to_csv(HERE / f"episodes_SMA{n}.csv", index=False, float_format="%.4f")
        off_days = int((keep_entry == 0).sum())
        switches = int((keep_entry.diff().fillna(0) != 0).sum())
        lines.append(f"  SMA{n}: episodes={len(ep)} switches={switches} off_days={off_days} "
                     f"vm_ret_mean={ep.vm_ret_pct.mean():.2f}% "
                     f"negative={int((ep.vm_ret_pct < 0).sum())}/{len(ep)}")
    lines.append("")

    # placebo: same gate, circular random shifts (preserves run structure)
    lines.append("placebo (1,000 circular shifts of the same gate):")
    placebo_out = {}
    for n in (50, 100, 200):
        keep = keep_map[n]
        net, w = run(close, open_, w_vm, keep, start=eval_start)
        m = metrics(net, w)
        p = placebo(close, open_, w_vm, keep, base_net, m, eval_start)
        placebo_out[f"SMA{n}"] = p
        lines.append(f"  SMA{n}: p(compound>=actual)={p['p_compound_ge_actual']:.3f} "
                     f"p(DD<=actual)={p['p_dd_le_actual']:.3f} "
                     f"p(Sharpe>=actual)={p['p_sharpe_ge_actual']:.3f}; "
                     f"placebo compound p50/p95={p['compound_p50_pct']:.1f}%/"
                     f"{p['compound_p95_pct']:.1f}%, DD p5/p50={p['dd_p5_pct']:.1f}%/"
                     f"{p['dd_p50_pct']:.1f}%")
    lines.append("")

    fw = familywise(close, open_, w_vm, keep_map, results, eval_start)
    lines.append("familywise max-statistic (same shifts across SMA50/100/200):")
    lines.append(f"  best actual: compound={fw['best_compound_pct']:.2f}% "
                 f"DD={fw['best_dd_pct']:.2f}% Sharpe={fw['best_sharpe']:.3f}; "
                 f"p(compound)={fw['p_family_compound']:.3f} "
                 f"p(DD)={fw['p_family_dd']:.3f} p(Sharpe)={fw['p_family_sharpe']:.3f}")
    lines.append("")

    lines.append("cost sensitivity at 1.00%/side (same rules):")
    for n in (50, 100, 200):
        keep = keep_map[n]
        we = w_vm.shift(1).fillna(0.0).mul(keep.shift(1).fillna(0.0), axis=0)
        r_entry = (open_.shift(-1) / open_ - 1.0)
        turn = we.diff().abs().sum(axis=1).fillna(we.abs().sum(axis=1))
        net = ((we * r_entry).sum(axis=1) - turn * 0.01).dropna().loc[eval_start:]
        m = metrics(net, we.loc[net.index])
        lines.append(f"  SMA{n}: compound={m['compound_pct']:.2f}% cagr={m['cagr_pct']:.2f}% "
                     f"maxDD={m['max_dd_pct']:.2f}%")
    lines.append("")

    for n in (50, 100, 200):
        turn = (w_vm.mul(keep_map[n].shift(1).fillna(0.0), axis=0)).diff().abs().sum(axis=1)
        lines.append(f"SMA{n}: sum |dw|={turn.sum():.2f}, arithmetic fee sum at 0.30%/side="
                     f"{turn.sum() * FEE * 100:.1f}%")
    lines.append("")

    eq = pd.DataFrame({"date": base_net.index.strftime("%Y-%m-%d"),
                       "vm_net": base_net.values,
                       "vm_equity": (1 + base_net).cumprod().values})
    eq.to_csv(HERE / "replay_equity.csv", index=False, float_format="%.6f")
    out = {"generated_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
           "window": f"{close.index.min().date()}..{close.index.max().date()}",
           "fee_per_side": FEE, "fill": "next daily bar open",
           "results": results, "placebo": placebo_out, "familywise": fw,
           "eval_start": str(eval_start.date()),
           "episodes": {f"SMA{n}": int(len(ep_frames[n])) for n in ep_frames}}
    (HERE / "replay_results.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    (HERE / "placebo_results.json").write_text(
        json.dumps(placebo_out, indent=2) + "\n")
    text = "\n".join(lines)
    print(text)
    (HERE / "replay_stdout.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
