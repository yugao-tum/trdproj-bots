#!/usr/bin/env python3
"""quant-007: historical TRADABLE-fill backtest from data-api executed trades.

For every closed event in series 10030, at check_time - L days (L=7/14/21):
  - leaderboard arm = Rank-1 company on the latest HF overall snapshot on/before that date
  - benchmark arm   = market's own most expensive named arm at the same instant
  - fill price      = last executed data-api BUY on that arm's YES token at/before entry
                      (actual taker print, not a daily mark)
  - net PnL         = won - fill - 0.04*fill*(1-fill)   [taker fee, one share]
No parameter is fitted; the same pre-registered rule as the prices-history run.

Outputs (this directory):
  q007_trades_fills.csv   per event/lead fills
  q007_trades_output.txt  stdout of this script
"""
import json, os, time, urllib.request, datetime as dt
from urllib.parse import urlencode
import pandas as pd
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0"
RATE = 0.04
rng = np.random.default_rng(20261021)


def fetch(url, tries=4):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read())
        except Exception as e:
            if a == tries - 1:
                raise
            time.sleep(1.2 * (a + 1))


def ts(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def last_buy(cond, token, entry, max_pages=4):
    """Latest data-api BUY print on `token` at/before entry (paged backwards)."""
    off = 0
    for _ in range(max_pages):
        q = urlencode({"market": cond, "side": "BUY", "limit": 1000,
                       "offset": off, "end": entry})
        batch = fetch("https://data-api.polymarket.com/trades?" + q)
        if not batch:
            return None, off // 1000 + 1
        cand = [t for t in batch if t.get("asset") == token and t["timestamp"] <= entry]
        if cand:
            # require at least one share; fall back to the largest of the latest prints
            big = [t for t in cand if float(t.get("size", 0)) >= 1.0]
            return max(big or cand, key=lambda t: t["timestamp"]), off // 1000 + 1
        if min(t["timestamp"] for t in batch) < entry - 30 * 86400:
            break
        off += 1000
        time.sleep(0.1)
    return None, off // 1000 + 1


print("fetching closed events ...", flush=True)
events = fetch("https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true")
by_slug = {e["slug"]: e for e in events}
print("closed events:", len(events))

raw = pd.read_csv(os.path.join(HERE, "backtest_raw.csv"))


def arm_info(ev, name):
    m = [x for x in ev["markets"] if (x.get("groupItemTitle") or x.get("question")) == name]
    if not m:
        return None
    m = m[0]
    return {"cond": m["conditionId"], "yes_token": json.loads(m["clobTokenIds"])[0]}


rows = []
for _, r in raw.iterrows():
    ev = by_slug[r["slug"]]
    entry = int(r["entry_ts"])
    out = {"slug": r["slug"], "lead": int(r["lead"]), "check": r["check"],
           "entry_ts": entry, "winner": r["winner"], "lb_arm": r["lb_arm"],
           "mkt_fav": r["mkt_fav"]}
    for tag, arm in (("lb", r["lb_arm"]), ("fav", r["mkt_fav"])):
        if not isinstance(arm, str) or not arm:
            out[tag + "_fill"] = np.nan
            continue
        ai = arm_info(ev, arm)
        if ai is None:
            out[tag + "_fill"] = np.nan
            continue
        tr, pages = last_buy(ai["cond"], ai["yes_token"], entry)
        if tr is None:
            out[tag + "_fill"] = np.nan
            out[tag + "_pages"] = pages
        else:
            out[tag + "_fill"] = float(tr["price"])
            out[tag + "_size"] = float(tr["size"])
            out[tag + "_hrs_before"] = (entry - tr["timestamp"]) / 3600.0
            out[tag + "_pages"] = pages
    rows.append(out)
    print("  %-58s L%-2d lb=%s fav=%s" % (
        r["slug"][:58], r["lead"], out.get("lb_fill"), out.get("fav_fill")), flush=True)

df = pd.DataFrame(rows)
df["lb_won"] = (df.lb_arm == df.winner).astype(int)
df["fav_won"] = (df.mkt_fav == df.winner).astype(int)


def net(fill, won, fee=RATE, slip=0.0):
    if pd.isna(fill):
        return np.nan
    p = min(fill + slip, 1.0)
    return (1.0 if won else 0.0) - p - fee * p * (1 - p)


for slip in (0.0, 0.005):
    df["lb_net_%s" % slip] = [net(p, w, slip=slip) for p, w in zip(df.lb_fill, df.lb_won)]
    df["fav_net_%s" % slip] = [net(p, w, slip=slip) for p, w in zip(df.fav_fill, df.fav_won)]
    df["lb_net_%s_nofee" % slip] = [net(p, w, fee=0.0, slip=slip)
                                    for p, w in zip(df.lb_fill, df.lb_won)]

df.to_csv(os.path.join(HERE, "q007_trades_fills.csv"), index=False)


def boot(x, n=20000):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (np.nan, np.nan)
    m = rng.choice(x, (n, len(x)), replace=True).mean(axis=1)
    return tuple(np.percentile(m, [2.5, 97.5]))


print("\n=== executed data-api BUY fills, leaderboard Rank-1 arm ===")
for lead in (7, 14, 21):
    s = df[(df.lead == lead) & df.lb_fill.notna()]
    print("\n-- lead %dd  n=%d/%d --" % (lead, len(s), len(df[df.lead == lead])))
    print("hit rate %d/%d = %.3f ; mean fill %.4f"
          % (s.lb_won.sum(), len(s), s.lb_won.mean(), s.lb_fill.mean()))
    for slip in (0.0, 0.005):
        c = "lb_net_%s" % slip
        lo, hi = boot(s[c])
        print("  slip %.3f: mean %+.4f [95%% boot %.4f, %.4f] median %+.4f sum %+.4f"
              % (slip, s[c].mean(), lo, hi, s[c].median(), s[c].sum()))
    c = "lb_net_0.0_nofee"
    lo, hi = boot(s[c])
    print("  fee=0:    mean %+.4f [95%% boot %.4f, %.4f] median %+.4f"
          % (s[c].mean(), lo, hi, s[c].median()))

print("\n=== benchmark at same instant: market's most expensive named arm ===")
for lead in (7, 14, 21):
    s = df[(df.lead == lead) & df.fav_fill.notna()]
    lo, hi = boot(s["fav_net_0.0"])
    print("lead %dd: n=%d hit=%d/%d mean(+fee,0slip)=%+.4f [%.4f, %.4f] mean fill %.4f"
          % (lead, len(s), s.fav_won.sum(), len(s), s["fav_net_0.0"].mean(),
             lo, hi, s.fav_fill.mean()))

print("\n=== paired leaderboard-minus-favourite using executed fills (T-7) ===")
s = df[(df.lead == 7) & df.lb_fill.notna() & df.fav_fill.notna()].copy()
s["diff"] = s["lb_net_0.0"] - s["fav_net_0.0"]
lo, hi = boot(s["diff"])
print("n=%d mean=%+.4f [95%% boot %.4f, %.4f] median=%+.4f lb better %d / worse %d / tie %d"
      % (len(s), s["diff"].mean(), lo, hi, s["diff"].median(),
         (s["diff"] > 1e-9).sum(), (s["diff"] < -1e-9).sum(), (s["diff"].abs() <= 1e-9).sum()))
dis = s[s.lb_arm != s.mkt_fav]
print("disagreement events n=%d: lb hit %d, favourite hit %d"
      % (len(dis), dis.lb_won.sum(), dis.fav_won.sum()))

print("\n=== entry's own ask<=0.85 gate (proxy: executed fill <= 0.85, T-7) ===")
s = df[(df.lead == 7) & df.lb_fill.notna() & (df.lb_fill <= 0.85)]
for slip in (0.0, 0.005):
    c = "lb_net_%s" % slip
    print("slip %.3f: n=%d mean %+.4f median %+.4f sum %+.4f"
          % (slip, len(s), s[c].mean(), s[c].median(), s[c].sum()))
print(s[["slug", "lb_arm", "lb_fill", "winner", "lb_won", "mkt_fav", "fav_fill",
         "fav_won", "lb_net_0.0", "fav_net_0.0"]].to_string(index=False))

print("\n=== prices-history point vs executed fill, T-7 ===")
m = df[df.lead == 7].merge(
    raw[raw.lead == 7][["slug", "lb_price", "mkt_fav_price"]], on="slug", how="left")
m["lb_gap_c"] = (m.lb_fill - m.lb_price) * 100
m["fav_gap_c"] = (m.fav_fill - m.mkt_fav_price) * 100
print("leaderboard arm: n=%d mean gap %+.2fc median %+.2fc max |gap| %.2fc"
      % (m.lb_gap_c.notna().sum(), m.lb_gap_c.mean(), m.lb_gap_c.median(),
         m.lb_gap_c.abs().max()))
print("favourite arm:   n=%d mean gap %+.2fc median %+.2fc max |gap| %.2fc"
      % (m.fav_gap_c.notna().sum(), m.fav_gap_c.mean(), m.fav_gap_c.median(),
         m.fav_gap_c.abs().max()))
print("\n=== per event, T-7 (executed fills) ===")
cols = ["check", "lb_arm", "lb_fill", "winner", "lb_won", "mkt_fav", "fav_fill",
        "fav_won", "lb_net_0.0", "fav_net_0.0"]
print(df[df.lead == 7][cols].to_string(index=False))
