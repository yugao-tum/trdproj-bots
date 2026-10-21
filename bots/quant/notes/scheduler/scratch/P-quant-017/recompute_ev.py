#!/usr/bin/env python3
"""P-quant-017: recompute the rank-persistence headline numbers from the full
sample recorded in notes/r2prep-verification/quant-017.md (the checker re-fetched
all 120 pre-registered and 158 wide snapshots), plus the EV/breakeven table.

No network. Inputs are quoted from that merged note:
  pre-reg frame: P1 53/60, P2 17/23
  wide frame   : P1 71/79, P2 25/34
Run: python3 recompute_ev.py
"""
import math


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (centre - half, centre + half)


def fee(p, rate):
    return rate * p * (1 - p)


def breakeven(P, rate, hs):
    # solve p + rate*p*(1-p) + hs = P
    # rate*p^2 - (1+rate)*p + (P-hs) = 0
    a, b, c = rate, -(1 + rate), (P - hs)
    disc = b * b - 4 * a * c
    return (-b - math.sqrt(disc)) / (2 * a)


def main():
    print("=== P-quant-017 recompute of rank persistence (full sample) ===")
    print("source: bots/quant/notes/r2prep-verification/quant-017.md section 2.1")
    for label, k, n in [("pre-reg P1 06->16", 53, 60),
                        ("pre-reg P2 overnight", 17, 23),
                        ("wide P1 06->16", 71, 79),
                        ("wide P2 overnight", 25, 34)]:
        lo, hi = wilson(k, n)
        print(f"{label:<24} {k:2d}/{n:2d} = {k/n:.4f}  Wilson 95% CI "
              f"[{lo:.4f}, {hi:.4f}]")

    print("\n--- EV table, pre-registered full sample P1=53/60=0.88333, "
          "rate=0.05, half-spread 1.5c ---")
    P = 53 / 60
    print("p     fee      cost     EV(c)    EV(%)")
    for p in (0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90):
        c = p + fee(p, 0.05) + 0.015
        ev = P - c
        print(f"{p:.2f}  {fee(p,0.05):.5f}  {c:.4f}  {ev*100:+.2f}   {ev/c*100:+.2f}")
    print(f"breakeven p = {breakeven(P,0.05,0.015):.4f}; "
          f"+2% margin threshold p = {breakeven(P-0.02,0.05,0.015):.4f}")

    print("\n--- EV table, wide full sample P1=71/79=0.89873, "
          "rate=0.05, half-spread 1.5c ---")
    P = 71 / 79
    print("p     fee      cost     EV(c)    EV(%)")
    for p in (0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90):
        c = p + fee(p, 0.05) + 0.015
        ev = P - c
        print(f"{p:.2f}  {fee(p,0.05):.5f}  {c:.4f}  {ev*100:+.2f}   {ev/c*100:+.2f}")
    print(f"breakeven p = {breakeven(P,0.05,0.015):.4f}; "
          f"+2% margin threshold p = {breakeven(P-0.02,0.05,0.015):.4f}")

    print("\n--- overnight, wide P2=25/34=0.73529, rate=0.05, hs=1.5c ---")
    P2 = 25 / 34
    for p in (0.68, 0.69, 0.70, 0.71, 0.72):
        c = p + fee(p, 0.05) + 0.015
        print(f"p={p:.2f} cost={c:.4f} EV={P2-c:+.4f}")

    print("\n--- fee sensitivity at p=0.95 / 0.98 (rate 0.05 vs 0 now) ---")
    for p in (0.95, 0.98):
        for rate in (0.05, 0.0):
            print(f"p={p:.2f} rate={rate:.2f} fee={fee(p,rate):.5f} "
                  f"net_win_after_hs1.5c={1-p-fee(p,rate)-0.015:+.5f}")


if __name__ == "__main__":
    main()
