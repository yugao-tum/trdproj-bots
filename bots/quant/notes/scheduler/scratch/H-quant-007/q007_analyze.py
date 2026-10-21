#!/usr/bin/env python3
"""Evaluate the pre-registered quant-007 rule on backtest_raw.csv."""
import pandas as pd, numpy as np, os

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "backtest_raw.csv"))
df["year"] = df.check.str[:4].astype(int)
RATE = 0.04
rng = np.random.default_rng(20261021)


def net(p, won, slip):
    if pd.isna(p):
        return np.nan
    fill = min(p + slip, 1.0)
    return (1.0 if won else 0.0) - fill - RATE * fill * (1 - fill)


for slip in (0.0, 0.005, 0.01):
    df["net_%s" % slip] = [net(p, w, slip) for p, w in zip(df.lb_price, df.lb_won)]
    df["favnet_%s" % slip] = [net(p, w, slip) for p, w in zip(df.mkt_fav_price, df.fav_won)]


def boot(x, n=20000):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (np.nan, np.nan)
    m = rng.choice(x, (n, len(x)), replace=True).mean(axis=1)
    return tuple(np.percentile(m, [2.5, 97.5]))


print("=== buy leaderboard Rank-1 at T-L, hold to settlement (taker fee 0.04*p*(1-p)) ===")
for lead in (7, 14, 21):
    s = df[(df.lead == lead) & df.lb_price.notna()]
    print("\n-- lead %dd  n=%d/22 --" % (lead, len(s)))
    print("hit rate %d/%d = %.3f" % (s.lb_won.sum(), len(s), s.lb_won.mean()))
    for slip in (0.0, 0.005, 0.01):
        c = "net_%s" % slip
        lo, hi = boot(s[c])
        print("  slip %.3f: mean %+.4f [95%% boot %.4f, %.4f]  median %+.4f  sum %+.4f on %.3f staked"
              % (slip, s[c].mean(), lo, hi, s[c].median(), s[c].sum(), s.lb_price.sum()))

print("\n=== split by settlement year ===")
for y in sorted(df.year.unique()):
    s = df[(df.lead == 7) & df.lb_price.notna() & (df.year == y)]
    print("T-7 %s: n=%d hit=%d/%d mean(+0.5c)=%+.4f median=%+.4f sum=%+.4f staked=%.3f"
          % (y, len(s), s.lb_won.sum(), len(s), s["net_0.005"].mean(),
             s["net_0.005"].median(), s["net_0.005"].sum(), s.lb_price.sum()))

print("\n=== entry's own gate: only when leaderboard arm price <= 0.85, T-7 ===")
s = df[(df.lead == 7) & df.lb_price.notna() & (df.lb_price <= 0.85)]
print(s[["slug", "lb_arm", "lb_price", "winner", "lb_won", "mkt_fav", "mkt_fav_price", "fav_won"]]
      .to_string(index=False))
for slip in (0.0, 0.005):
    c = "net_%s" % slip
    print("slip %.3f: n=%d mean %+.4f median %+.4f sum %+.4f staked %.3f"
          % (slip, len(s), s[c].mean(), s[c].median(), s[c].sum(), s.lb_price.sum()))

print("\n=== benchmark: buy the market's own favourite at the same instant, T-7 ===")
s = df[(df.lead == 7) & df.mkt_fav_price.notna()]
print("hit rate %d/%d = %.3f ; mean price %.4f"
      % (s.fav_won.sum(), len(s), s.fav_won.mean(), s.mkt_fav_price.mean()))
for slip in (0.0, 0.005):
    c = "favnet_%s" % slip
    lo, hi = boot(s[c])
    print("slip %.3f: mean %+.4f [95%% boot %.4f, %.4f] median %+.4f sum %+.4f staked %.3f"
          % (slip, s[c].mean(), lo, hi, s[c].median(), s[c].sum(), s.mkt_fav_price.sum()))
print("leaderboard arm == market favourite: %d/%d" % ((s.lb_arm == s.mkt_fav).sum(), len(s)))
print("when they differ (n=%d): lb hit %d, favourite hit %d"
      % ((s.lb_arm != s.mkt_fav).sum(),
         s[s.lb_arm != s.mkt_fav].lb_won.sum(), s[s.lb_arm != s.mkt_fav].fav_won.sum()))

print("\n=== calibration of leaderboard arm price, T-7 (n=%d) ===" % len(s))
print("mean price %.4f vs hit rate %.4f ; Brier(lb arm) %.4f"
      % (s.lb_price.mean(), s.lb_won.mean(),
         ((s.lb_price - s.lb_won) ** 2).mean()))
print("mean fav price %.4f vs fav hit rate %.4f ; Brier(fav) %.4f"
      % (s.mkt_fav_price.mean(), s.fav_won.mean(),
         ((s.mkt_fav_price - s.fav_won) ** 2).mean()))

print("\n=== concordance HF mirror rank-1 vs actual settlement ===")
for lead in (7, 14, 21):
    s2 = df[df.lead == lead]
    print("lead %dd: %d/%d" % (lead, s2.lb_won.sum(), len(s2)))
print("2026 only, T-7: %d/%d" % (df[(df.lead == 7) & (df.year == 2026)].lb_won.sum(),
                                  (df[(df.lead == 7) & (df.year == 2026)]).shape[0]))

print("\n=== per-event, lead 7 ===")
cols = ["check", "lb_arm", "lb_model", "lb_price", "winner", "lb_won",
        "mkt_fav", "mkt_fav_price", "fav_won", "net_0.0", "net_0.005"]
print(df[df.lead == 7][cols].to_string(index=False))

print("\n=== paired: leaderboard Rank-1 vs market favourite (T-7, both priced) ===")
s = df[(df.lead == 7) & df.lb_price.notna() & df.mkt_fav_price.notna()].copy()
s["diff"] = s["net_0.005"] - s["favnet_0.005"]
lo, hi = boot(s["diff"])
print("n=%d mean(lb - fav)=%+.4f [95%% boot %.4f, %.4f] median=%+.4f"
      % (len(s), s["diff"].mean(), lo, hi, s["diff"].median()))
print("lb better on %d, worse on %d, tied on %d"
      % ((s["diff"] > 1e-9).sum(), (s["diff"] < -1e-9).sum(), (s["diff"].abs() <= 1e-9).sum()))

print("\n=== 2026-only CI and rank-column-rule era ===")
for label, g in [("2026 all (n=9)", df[(df.lead == 7) & (df.year == 2026) & df.lb_price.notna()]),
                 ("rank-era 2026-04..09", df[(df.lead == 7) & df.lb_price.notna() &
                                             (df.check >= "2026-04-01")])]:
    lo, hi = boot(g["net_0.005"])
    print("%-24s n=%d hit=%d mean=%+.4f [%.4f, %.4f] median=%+.4f"
          % (label, len(g), g.lb_won.sum(), g["net_0.005"].mean(), lo, hi, g["net_0.005"].median()))

print("\n=== where leaderboard and market disagree (T-7) ===")
s = df[(df.lead == 7) & df.lb_price.notna() & df.mkt_fav_price.notna()]
print(s[s.lb_arm != s.mkt_fav][["check", "lb_arm", "lb_price", "winner", "lb_won",
                                 "mkt_fav", "mkt_fav_price", "fav_won",
                                 "net_0.005", "favnet_0.005"]].to_string(index=False))
