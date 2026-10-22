#!/usr/bin/env python3
"""Re-check the committed round-2 replay artefacts against the entry text.

Reads replay/quant-001/replay_results.json and holdout_results.json (produced
by run_replay.py / run_holdout.py) and asserts the headline numbers quoted in
the entry.  Fails loudly if any number drifts.

Run: python3 bots/quant/notes/scheduler/scratch/H-quant-001/verify_round2_numbers.py
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPLAY = HERE.parents[3] / "replay/quant-001"

EXPECTED = {
    "VM": (23.31, 8.90, -35.69, 0.428),
    "VM_x_SMA50": (59.73, 20.99, -24.58, 0.848),
    "VM_x_SMA100": (83.41, 27.99, -23.28, 1.141),
    "VM_x_SMA200": (48.97, 17.61, -33.54, 0.808),
    "const_scale_SMA50": (20.07, 7.73, -28.54, 0.428),
    "const_scale_SMA100": (19.05, 7.35, -26.67, 0.428),
    "const_scale_SMA200": (19.09, 7.37, -26.75, 0.428),
}
EPISODES = {"SMA50": 24, "SMA100": 18, "SMA200": 8}
HOLDOUT = {
    ("VM_x_SMA50", "2024"): (0.39, -24.58),
    ("VM_x_SMA100", "2024"): (2.10, -23.28),
    ("VM_x_SMA200", "2024"): (-16.29, -33.54),
    ("VM", "2024"): (-8.64, -35.17),
}

fails = []


def close(a, b, tol=0.011):
    return abs(a - b) <= tol


def main():
    r = json.loads((REPLAY / "replay_results.json").read_text())
    lines = ["round-2 number check", f"window: {r['window']}",
             f"fee/side: {r['fee_per_side']}  fill: {r['fill']}",
             f"eval_start: {r['eval_start']}"]
    for k, (comp, cagr, dd, sh) in EXPECTED.items():
        m = r["results"][k]
        got = (m["compound_pct"], m["cagr_pct"], m["max_dd_pct"], m["sharpe"])
        ok = (close(got[0], comp) and close(got[1], cagr) and
              close(got[2], dd) and close(got[3], sh, 0.0011))
        lines.append(f"  {k:<20} {got[0]:9.2f}% {got[1]:7.2f}% "
                     f"{got[2]:8.2f}% {got[3]:6.3f}  {'OK' if ok else 'MISMATCH'}")
        if not ok:
            fails.append((k, got, (comp, cagr, dd, sh)))
    for k, n in EPISODES.items():
        ok = r["episodes"][k] == n
        lines.append(f"  episodes {k:<12} {r['episodes'][k]} (expected {n}) "
                     f"{'OK' if ok else 'MISMATCH'}")
        if not ok:
            fails.append((f"episodes {k}", r["episodes"][k], n))
    fw = r["familywise"]
    lines.append(f"  familywise p compound={fw['p_family_compound']:.3f} "
                 f"DD={fw['p_family_dd']:.3f} Sharpe={fw['p_family_sharpe']:.3f}")
    h = json.loads((REPLAY / "holdout_results.json").read_text())
    for (k, period), (comp, dd) in HOLDOUT.items():
        m = h["splits"][{"2024": "holdout_2024"}.get(period, period)][k]
        ok = close(m["compound_pct"], comp) and close(m["max_dd_pct"], dd)
        lines.append(f"  holdout {period} {k:<12} {m['compound_pct']:8.2f}% "
                     f"{m['max_dd_pct']:8.2f}%  {'OK' if ok else 'MISMATCH'}")
        if not ok:
            fails.append((f"{period} {k}", m, (comp, dd)))
    lines.append("")
    lines.append(f"failures: {len(fails)}")
    text = "\n".join(lines)
    print(text)
    (HERE / "verify_round2_numbers_stdout.txt").write_text(text + "\n")
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
