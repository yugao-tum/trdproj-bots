#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quant-005 历史可成交价回测：Polymarket Elon Musk / Trump 发帖数分档市场
================================================================================
本文件头部的口径在查看任何回测结果之前写死（pre-declared）。

【Universe】
  Gamma keyless，closed=true，按 series 抓全部已结算事件：
    - series 10816  elon-tweets-48h   "Elon Tweets 48H"      窗口 48h
    - series 10000  elon-tweets       "Elon Tweets weekly"   窗口 7d
    - series 11108  trump-truth-social "Trump Truth Social"  窗口 7d
  一个 event 的 10–12 个档位算 1 个独立结果；event 之间按结算时间重叠不合并。
  只保留至少一个档位已 resolved、且能取到结算 outcomePrices 的事件。
  事件窗口 = [本地 noon ET − 2/7 天, 本地 noon ET)；把 Gamma endDate 转成
  America/New_York 后在本地日历上减 2/7 天，因此跨 DST 的窗口是 47/49h（或 167/169h），
  不再是固定 48h/168h。不采用 startDate（它是建盘时间）。

【Decision time】
  主口径：窗口已过 50% 的时点 decision = start + 0.5 * duration。
  敏感性：窗口已过 75% 的时点。
  n_elapsed = createdAt ∈ [start, decision) 的帖数（严格左闭右开）。

【计数与模型】
  帖子时间戳来自 xtracker keyless：
    https://xtracker.polymarket.com/api/users/elonmusk/posts
    https://xtracker.polymarket.com/api/users/realDonaldTrump/posts
  历史窗口：以本地 12h 为步长回溯、结束时刻对齐当前事件 endDate 的本地时/分/秒，
  起点同样按本地日历减 2/7 天；要求窗口起点不早于该 feed 最早帖。walk-forward：
  只用 decision 之前已经结束的窗口的最终计数，不使用当前窗口结算结果。
  经验条件分布：历史窗口的“前 elapsed_fraction 时长计数” ≤ n_elapsed 者入选，
  并施加硬约束“最终计数 ≥ n_elapsed”（已经观测到 n 条，最终不可能更少）。
  当前 event 的各档 p_k = 入选窗口最终计数落在该档的比例。
  （entry 原文只写了“≤ n_elapsed”。若只照字面执行，会买到 upper < n_elapsed 的
   逻辑上不可能档位；本脚本主口径加上 ≥ n_elapsed。字面版单独保存为
   run_output_literal_le.txt 作对照，两者结论相同。）
  保守版（主口径）：在入选样本内按最终计数排序，剔除最高的 ceil(10%) 个窗口后再算 p_k。
  入选样本 <30 或剔除后 <20 → 该事件跳过（不交易，不计入 P&L 样本）。
  NB（负二项）只用矩估计拟合同一入选样本，作为平滑检查，不用于触发交易。

【可成交价】
  data-api keyless：https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N
  取 decision−6h 到 decision 之间最后一笔成交；outcome="No" 时 YES 价 = 1 − price。
  ask_k = 该 YES 成交价 + 0.01（1¢ 滑点/价差缓冲）。
  若某档在 [decision−6h, decision] 无成交，则该档没有可成交价，不参与买入。
  主口径费用：所有事件统一用 Gamma 现行 feeSchedule 的 taker 费率 0.05，
    fee_k = 0.05 × ask_k × (1 − ask_k) 每份（GUIDE §8 公式）。
    历史早期 feesEnabled=false 的市场实际 taker 费为 0；统一收 0.05 是保守处理。
  edge_k = p_k − ask_k − fee_k − 0.01。只买 edge_k 最大的那一档，且必须 edge_k > 0。
  持有到结算：payoff = 1 若该档在 Gamma 结算为 Yes，否则 0。
  净收益/份 = payoff − ask_k − fee_k；净收益/本金 = 净收益/份 ÷ ask_k。
  未触发的事件按 0 持仓处理（不进主 P&L 样本，但单独报告 all-event 口径）。

【独立性与统计】
  主 P&L 样本 = 50% 决策点触发买入的事件，每个事件一个结果。
  ISO 周 block bootstrap（按 decision 所在 ISO 周分块，周内有放回抽样，
  10000 次，固定 seed=20260520）给均值的 95% 百分位 CI。

【冻结失败标准（entry 原文）】
  逐事件（一个 event 的所有档 = 1 个结果）扣费后买入侧净收益中位数 ≤ 0 → FAIL。
  要求 ≥30 个独立事件结果；触发样本 <30 → INSUFFICIENT。
  本脚本判据：triggered_events < 30 → INSUFFICIENT；否则 median(net_per_share) ≤ 0 → FAIL；
  否则 PASS。PASS/FAIL 不看敏感性口径（敏感性只报告）。

【数据/缓存/复现】
  所有下载缓存在 _cache/（已 .gitignore）；成交缓存只有完整分页成功才标
  complete=true，失败/半截下载标 complete=false、本次不用于定价且下次重取；
  没有 complete 字段的旧缓存一律视为不完整。输出不打印运行时刻，仅打印首次抓取的
  UTC 日期，因此同一缓存下 stdout 应逐字节一致。
"""

import csv
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = Path(__file__).resolve().parent
CACHE = BASE / "_cache"
TRADE_CACHE = CACHE / "trades"
CACHE.mkdir(parents=True, exist_ok=True)
TRADE_CACHE.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (quant-005 research; keyless public endpoints)"}
TIMEOUT = 90
SERIES = {
    10816: {"tag": "elon48", "handle": "elonmusk", "days": 2},
    10000: {"tag": "elon7d", "handle": "elonmusk", "days": 7},
    11108: {"tag": "trump7d", "handle": "realDonaldTrump", "days": 7},
}
NY = ZoneInfo("America/New_York")
STEP = 12 * 3600          # 历史窗口步长 12h
FRACS = (0.50, 0.75)
PRICE_LOOKBACK = 6 * 3600 # decision 前 6h
FEE_RATE = 0.05
SLIP = 0.01
EDGE_BUFFER = 0.01
MIN_HIST = 30
MIN_KEPT = 20
BOOT_N = 10000
SEED = 20260520
COND_MODE = os.environ.get("Q005_COND", "le_ge")


# ---------------------------------------------------------------- fetch helpers
def _get_json(url, params=None, tries=6):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=TIMEOUT)
            if r.status_code == 429:
                time.sleep(2 ** i)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(min(2 ** i, 20))
    raise RuntimeError(f"fetch failed {url} {params}: {last}")


def _meta_path():
    return CACHE / "fetch_meta.json"


def touch_meta():
    p = _meta_path()
    if not p.exists():
        p.write_text(json.dumps({"access_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d")}, indent=2))


def get_meta():
    touch_meta()
    return json.loads(_meta_path().read_text())


def fetch_events(sid):
    p = CACHE / f"events_{sid}.json"
    if p.exists():
        return json.loads(p.read_text())
    out = []
    for off in range(0, 5000, 100):
        d = _get_json("https://gamma-api.polymarket.com/events",
                      {"series_id": sid, "closed": "true", "limit": 100, "offset": off})
        out.extend(d)
        if len(d) < 100:
            break
    p.write_text(json.dumps(out))
    return out


def fetch_posts(handle):
    p = CACHE / f"posts_{handle}.json"
    if p.exists():
        return json.loads(p.read_text())
    d = _get_json(f"https://xtracker.polymarket.com/api/users/{handle}/posts",
                  {"limit": 100, "offset": 0}, tries=8)
    rows = d.get("data", d) if isinstance(d, dict) else d
    ts = []
    for x in rows:
        c = x.get("createdAt")
        if not c:
            continue
        ts.append(datetime.fromisoformat(c.replace("Z", "+00:00")).timestamp())
    ts = sorted(ts)
    p.write_text(json.dumps(ts))
    return ts


def _trade_cache_file(cid):
    return TRADE_CACHE / f"{cid}.json"


def fetch_trades_for_market(cid, need_lo, need_hi):
    """Fetch trades in [need_lo, need_hi], newest-first.

    A cache entry is reusable only when it is explicitly marked complete=True,
    has no stored error, and covers the requested bounds. Failed or partially
    paginated downloads are stored with complete=False and are never reused;
    they are also NOT returned as prices for the current run (the affected
    market is excluded instead of being silently priced from missing pages).

    Returns (trades, complete, error).
    """
    p = _trade_cache_file(cid)
    if p.exists():
        try:
            c = json.loads(p.read_text())
            if (c.get("complete") is True and not c.get("error")
                    and c.get("lo", 1e30) <= need_lo and c.get("hi", -1e30) >= need_hi):
                return c.get("trades", []), True, None
        except Exception:  # noqa: BLE001
            pass
    got = []
    off = 0
    err = None
    complete = False
    try:
        while off < 20000:
            d = _get_json("https://data-api.polymarket.com/trades",
                          {"market": cid, "limit": 500, "offset": off})
            if not isinstance(d, list):
                raise RuntimeError(f"non-list trades response: {str(d)[:200]}")
            if not d:
                complete = True
                break
            for x in d:
                t = x.get("timestamp")
                if t is None:
                    continue
                if need_lo <= t <= need_hi:
                    got.append([int(t), x.get("outcome"), float(x.get("price", 0)), float(x.get("size", 0))])
            if min(x["timestamp"] for x in d if x.get("timestamp") is not None) < need_lo:
                complete = True
                break
            if len(d) < 500:
                complete = True
                break
            off += 500
        else:
            err = "pagination hit 20000-offset limit before reaching need_lo"
    except Exception as e:  # noqa: BLE001
        err = str(e)
    p.write_text(json.dumps({"lo": need_lo, "hi": need_hi, "complete": complete,
                             "error": err, "trades": got}))
    if not complete:
        return [], False, err
    return got, True, None


# ---------------------------------------------------------------- bracket parsing
_DASH = str.maketrans({"\u2013": "-", "\u2014": "-", "\u2212": "-"})


def parse_bracket(label):
    s = (label or "").translate(_DASH).strip().replace(" ", "")
    m = re.match(r"^<(\d+)$", s)
    if m:
        return -math.inf, int(m.group(1)) - 1
    m = re.match(r"^(\d+)\+$", s)
    if m:
        return int(m.group(1)), math.inf
    m = re.match(r"^(\d+)-(\d+)$", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        return a, b
    return None


def in_bracket(x, lo, hi):
    return lo <= x <= hi


def parse_outcome_prices(s):
    if s is None:
        return None
    try:
        v = json.loads(s) if isinstance(s, str) else s
        return [float(x) for x in v]
    except Exception:  # noqa: BLE001
        return None


def iso_week(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isocalendar()[:2]


# ---------------------------------------------------------------- model
def empirical_model(posts, end_local, days, frac, n_elapsed, brackets):
    """Walk-forward windows ending before decision, aligned to local-noon boundaries.

    Event end is the Gamma endDate converted to America/New_York. Historical
    window ends are obtained by subtracting 12h steps in *local wall time* and
    starts by subtracting `days` local calendar days, so a window that spans a
    DST transition keeps the advertised noon-ET-to-noon-ET boundaries (rather
    than a fixed 168h/48h elapsed duration).
    """
    start_local = end_local - timedelta(days=days)
    start_ts = start_local.timestamp()
    end_ts = end_local.timestamp()
    dur = end_ts - start_ts
    decision = start_ts + frac * dur
    earliest = posts[0]
    pairs = []
    k = 1
    while True:
        he_local = end_local - timedelta(seconds=k * STEP)
        he = he_local.timestamp()
        if he >= decision:
            k += 1
            continue
        hs_local = he_local - timedelta(days=days)
        hs = hs_local.timestamp()
        if hs < earliest:
            break
        pe = hs + frac * (he - hs)
        i0 = int(np.searchsorted(posts, hs, side="left"))
        i1 = int(np.searchsorted(posts, pe, side="left"))
        j1 = int(np.searchsorted(posts, he, side="left"))
        part = i1 - i0
        final = j1 - i0
        pairs.append((part, final))
        k += 1

    if COND_MODE == "le":
        finals = [f for p_, f in pairs if p_ <= n_elapsed]
    elif COND_MODE == "le_ge":
        finals = [f for p_, f in pairs if p_ <= n_elapsed and f >= n_elapsed]
    elif COND_MODE == "exact":
        finals = [f for p_, f in pairs if p_ == n_elapsed and f >= n_elapsed]
    elif COND_MODE.startswith("band"):
        pct = float(COND_MODE[4:]) / 100.0
        w = max(3, int(round(pct * max(1, n_elapsed))))
        finals = [f for p_, f in pairs if abs(p_ - n_elapsed) <= w and f >= n_elapsed]
    elif COND_MODE.startswith("knn"):
        K = int(COND_MODE[3:])
        cand = [(abs(p_ - n_elapsed), f) for p_, f in pairs if f >= n_elapsed]
        cand.sort(key=lambda x: x[0])
        finals = [f for _, f in cand[:K]]
    else:
        raise ValueError(COND_MODE)
    n_cond = len(finals)
    if n_cond < MIN_HIST:
        return None
    finals_sorted = sorted(finals)
    drop = int(math.ceil(0.10 * n_cond))
    kept = finals_sorted[: n_cond - drop]
    if len(kept) < MIN_KEPT:
        return None

    def probs(sample):
        denom = len(sample)
        out = []
        for lo, hi in brackets:
            c = sum(1 for x in sample if in_bracket(x, lo, hi))
            out.append(c / denom if denom else 0.0)
        return out

    p_cons = probs(kept)
    p_raw = probs(finals)

    # NB method-of-moments on the conditional sample (smoothing check only)
    mu = float(np.mean(finals))
    var = float(np.var(finals, ddof=1)) if n_cond > 1 else 0.0
    if var > mu + 1e-9 and mu > 0:
        r = mu * mu / (var - mu)
        q = r / (r + mu)
        pmf = []
        cap = int(max(1000, max(finals) * 3 + 50))
        for x in range(cap + 1):
            logp = math.lgamma(x + r) - math.lgamma(r) - math.lgamma(x + 1) + r * math.log(q) + x * math.log(1 - q)
            pmf.append(math.exp(logp))
        nb = []
        for lo, hi in brackets:
            a = 0 if not math.isfinite(lo) else max(0, int(lo))
            b = cap if not math.isfinite(hi) else min(cap, int(hi))
            nb.append(float(sum(pmf[a:b + 1])))
        s = sum(nb)
        nb = [x / s for x in nb] if s > 0 else [0.0] * len(brackets)
    else:
        nb = None

    return {
        "decision": decision,
        "p_cons": p_cons,
        "p_raw": p_raw,
        "nb": nb,
        "n_hist_windows": n_cond,
        "n_kept": len(kept),
        "n_dropped": drop,
        "mu_hist": mu,
        "var_hist": var,
    }


def last_yes_price(trades, lo, hi):
    best_ts = None
    best_p = None
    for t, outcome, price, _size in trades:
        if lo <= t <= hi:
            yp = price if outcome == "Yes" else (1.0 - price if outcome == "No" else None)
            if yp is None:
                continue
            if best_ts is None or t >= best_ts:
                best_ts, best_p = t, yp
    return best_ts, best_p


def price_event(markets, trades_by_cid, decision):
    """Return list of (raw_yes, ask, ts) or None per bracket, using decision-6h..decision."""
    lo, hi = decision - PRICE_LOOKBACK, decision
    out = []
    for m in markets:
        tr = trades_by_cid.get(m["conditionId"], [])
        ts, yp = last_yes_price(tr, lo, hi)
        if yp is None:
            out.append(None)
        else:
            out.append({"ts": ts, "yes": yp, "ask": min(1.0, yp + SLIP)})
    return out


def fee_of(ask):
    return FEE_RATE * ask * (1.0 - ask)


def decide_trade(model, prices, brackets):
    best = None
    for i, (lo, hi) in enumerate(brackets):
        if prices[i] is None:
            continue
        ask = prices[i]["ask"]
        if ask <= 0 or ask >= 1:
            continue
        fee = fee_of(ask)
        edge = model["p_cons"][i] - ask - fee - EDGE_BUFFER
        if best is None or edge > best["edge"]:
            best = {"idx": i, "ask": ask, "fee": fee, "edge": edge,
                    "p": model["p_cons"][i], "price_ts": prices[i]["ts"]}
    if best is not None and best["edge"] > 0:
        best["triggered"] = True
    elif best is not None:
        best["triggered"] = False
    return best


def boot_ci(values_by_week):
    weeks = sorted(values_by_week)
    if len(weeks) < 2:
        return None, None
    rng = random.Random(SEED)
    means = []
    for _ in range(BOOT_N):
        pick = [weeks[rng.randrange(len(weeks))] for _ in weeks]
        vals = []
        for w in pick:
            vals.extend(values_by_week[w])
        means.append(sum(vals) / len(vals))
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize(rows, trigger_key, share_key, dollar_key, win_key, ts_key):
    """Summarize an explicitly chosen decision-point field set.

    The 75% sensitivity must not silently reuse the 50% fields, so every field
    name (trigger flag, returns, win flag, timestamp) is passed in by the caller.
    """
    sel = [r for r in rows if r.get(trigger_key)]
    vals = [r[share_key] for r in sel]
    dvals = [r[dollar_key] for r in sel]
    wins = [1.0 if r.get(win_key) else 0.0 for r in sel]
    if not vals:
        return {"n": 0}
    by_week = {}
    for r in sel:
        by_week.setdefault(iso_week(r[ts_key]), []).append(r[share_key])
    ci_lo, ci_hi = boot_ci(by_week)
    return {
        "n": len(vals),
        "median_share": float(np.median(vals)),
        "mean_share": float(np.mean(vals)),
        "median_dollar": float(np.median(dvals)),
        "mean_dollar": float(np.mean(dvals)),
        "hit": float(np.mean(wins)),
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "weeks": len(by_week),
    }


def all_event_summary(rows, key, trigger_key):
    vals = [r.get(key, 0.0) if r.get(trigger_key) else 0.0 for r in rows]
    wins = [1.0 if (r.get(trigger_key) and r.get("win_75" if trigger_key == "triggered_75" else "win")) else 0.0 for r in rows]
    return float(np.median(vals)), float(np.mean(vals)), float(np.mean(wins))


def _event_end_ts(r):
    return datetime.fromisoformat(r["window_end_utc"]).timestamp()


def frozen_scope(rows):
    """Frozen entry scope: Elon 48h only, one result per 48h by settlement time."""
    erows = sorted([r for r in rows if r.get("series") == "elon48"], key=_event_end_ts)
    kept_all, last = [], None
    for r in erows:
        e = _event_end_ts(r)
        if last is None or e - last >= 48 * 3600:
            kept_all.append(r)
            last = e
    trig = [r for r in erows if r.get("triggered")]
    kept_trig, last = [], None
    for r in sorted(trig, key=_event_end_ts):
        e = _event_end_ts(r)
        if last is None or e - last >= 48 * 3600:
            kept_trig.append(r)
            last = e
    return erows, kept_all, kept_trig


def main():
    touch_meta()
    meta = get_meta()
    access_date = meta["access_date_utc"]

    print("quant-005 历史可成交价回测")
    print(f"数据访问日期(UTC): {access_date}")
    print("Universe: Gamma closed=true series 10816 (Elon 48h), 10000 (Elon 7d), 11108 (Trump 7d)")
    print(f"Decision: 50% (主), 75% (敏感性); 条件模式={COND_MODE}; 历史窗口步长 {STEP//3600}h; fee rate {FEE_RATE}; ask=trade+{SLIP}; edge buffer {EDGE_BUFFER}")
    print()

    # ---- load event metadata + posts
    events = []
    for sid, cfg in SERIES.items():
        raw = fetch_events(sid)
        evs = {e["id"]: e for e in raw}
        for e in evs.values():
            events.append((sid, cfg, e))
    posts = {h: fetch_posts(h) for h in ["elonmusk", "realDonaldTrump"]}

    print("Universe 抓取：")
    for sid, cfg in SERIES.items():
        evs = [e for s, c, e in events if s == sid]
        resolved = [e for e in evs if any(
            (lambda op: op is not None and max(op) > 0.5)(parse_outcome_prices(m.get("outcomePrices")))
            for m in e.get("markets", []))]
        print(f"  series {sid} {cfg['tag']}: closed={len(evs)}, 有已结算档={len(resolved)}, "
              f"span={min(e['endDate'] for e in evs)[:10]}..{max(e['endDate'] for e in evs)[:10]}, "
              f"posts={len(posts[cfg['handle']])} ({datetime.fromtimestamp(posts[cfg['handle']][0], timezone.utc).strftime('%Y-%m-%d')}"
              f"..{datetime.fromtimestamp(posts[cfg['handle']][-1], timezone.utc).strftime('%Y-%m-%d')})")
    print()

    # ---- build per-event work items
    work = []
    for sid, cfg, e in events:
        end_dt = datetime.fromisoformat(e["endDate"].replace("Z", "+00:00"))
        end_local = end_dt.astimezone(NY)
        start_local = end_local - timedelta(days=cfg["days"])
        start = start_local.timestamp()
        end = end_local.timestamp()
        dur = end - start
        markets = e.get("markets", [])
        brackets = [parse_bracket(m.get("groupItemTitle")) for m in markets]
        if any(b is None for b in brackets):
            continue
        res_idx, res_yes = None, None
        for i, m in enumerate(markets):
            op = parse_outcome_prices(m.get("outcomePrices"))
            if op is None or len(op) < 2:
                continue
            yes = op[0]
            if yes > 0.5:
                if res_idx is not None:
                    res_idx = -999  # ambiguous
                    break
                res_idx, res_yes = i, yes
        if res_idx is None or res_idx == -999 or res_idx < 0:
            continue
        work.append({"sid": sid, "cfg": cfg, "e": e, "dur": dur, "start": start, "end": end,
                     "end_local": end_local, "markets": markets, "brackets": brackets,
                     "res_idx": res_idx, "res_yes": res_yes, "handle": cfg["handle"]})

    # ---- decide which events are model-eligible, then fetch trades for their markets
    eligible = []
    for w in work:
        p = posts[w["handle"]]
        if w["start"] < p[0]:
            continue
        # quick check: at 50% decision, need at least MIN_HIST conditional windows. We cannot
        # know n_elapsed before computing it, so just prefilter by enough total history.
        decision = w["start"] + FRACS[0] * w["dur"]
        if decision - w["dur"] < p[0]:
            continue
        eligible.append(w)

    # per-market cache range uses the event's own decision75 and decision50-6h
    jobs = {}
    for w in eligible:
        d50 = w["start"] + FRACS[0] * w["dur"]
        d75 = w["start"] + FRACS[1] * w["dur"]
        lo, hi = d50 - PRICE_LOOKBACK, d75
        for m in w["markets"]:
            cid = m["conditionId"]
            if cid not in jobs:
                jobs[cid] = (lo, hi)
            else:
                a, b = jobs[cid]
                jobs[cid] = (min(a, lo), max(b, hi))

    # audit old/partial trade caches before fetching: only complete=True entries are reusable
    cache_total = cache_stale = cache_legacy = 0
    for f in TRADE_CACHE.glob("*.json"):
        cache_total += 1
        try:
            c = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            cache_stale += 1
            continue
        if c.get("complete") is not True or c.get("error"):
            cache_stale += 1
            if "complete" not in c:
                cache_legacy += 1
    print(f"可建模候选事件={len(eligible)}；待取成交的 conditionId={len(jobs)}（并发 8，缓存 _cache/trades）")
    print(f"  trades 缓存审计: 已有 {cache_total} 个，需重取的不完整/旧格式 {cache_stale} 个（其中 v1 旧格式 {cache_legacy} 个）")
    trades_by_cid = {}
    incomplete = []
    if jobs:
        done = 0
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(fetch_trades_for_market, cid, lo, hi): cid for cid, (lo, hi) in jobs.items()}
            for f in as_completed(futs):
                cid = futs[f]
                try:
                    tr, ok, err = f.result()
                    trades_by_cid[cid] = tr
                    if not ok:
                        incomplete.append((cid, err))
                except Exception as exc:  # noqa: BLE001
                    trades_by_cid[cid] = []
                    incomplete.append((cid, str(exc)))
                done += 1
                if done % 200 == 0:
                    print(f"  trades fetched {done}/{len(jobs)}")
        print(f"  trades 抓取完整 {len(jobs) - len(incomplete)}/{len(jobs)}；不完整 {len(incomplete)} 个（已从定价中排除，complete=false，下次重取）")
        for cid, err in incomplete[:5]:
            print(f"  WARN trades {cid}: {err}")
    print()

    # ---- run model / pricing / decisions
    out_rows = []
    logloss = {"cons": [], "raw": [], "nb": [], "mkt": [], "n": 0}
    resolver_mismatch = 0
    resolver_checked = 0

    for w in work:
        row = {
            "event_id": w["e"]["id"], "series": w["cfg"]["tag"], "slug": w["e"]["slug"],
            "duration_h": w["dur"] / 3600, "window_start_utc": datetime.fromtimestamp(w["start"], timezone.utc).isoformat(),
            "window_end_utc": datetime.fromtimestamp(w["end"], timezone.utc).isoformat(),
            "n_brackets": len(w["markets"]), "resolved_bracket": w["markets"][w["res_idx"]]["groupItemTitle"].strip(),
            "priced_brackets": "", "triggered": False, "skip_reason": "",
        }
        p = posts[w["handle"]]
        i0 = int(np.searchsorted(p, w["start"], side="left"))
        iend = int(np.searchsorted(p, w["end"], side="left"))
        final_count = iend - i0
        row["final_count_tracker"] = final_count
        row["window_bracket_tracker"] = ""
        for (lo, hi), m in zip(w["brackets"], w["markets"]):
            if in_bracket(final_count, lo, hi):
                row["window_bracket_tracker"] = m["groupItemTitle"].strip()
                break

        if w["start"] < p[0]:
            row["skip_reason"] = "no_post_history_before_window"
            out_rows.append(row)
            continue

        # data-quality guard: tracker feed has no post in a window that resolved above 0.
        # This happens for archived/duplicate slugs; the feed cannot reconstruct the count.
        if final_count == 0 and w["brackets"][w["res_idx"]][0] > 0:
            row["skip_reason"] = "tracker_feed_gap"
            out_rows.append(row)
            continue

        model = None
        for frac in FRACS:
            decision = w["start"] + frac * w["dur"]
            n_elapsed = int(np.searchsorted(p, decision, side="left")) - int(np.searchsorted(p, w["start"], side="left"))
            m = empirical_model(p, w["end_local"], w["cfg"]["days"], frac, n_elapsed, w["brackets"])
            if frac == FRACS[0]:
                model = m
                if m is None:
                    row["skip_reason"] = "insufficient_conditional_history"
                else:
                    row["n_elapsed"] = n_elapsed
                    row["decision_utc"] = datetime.fromtimestamp(m["decision"], timezone.utc).isoformat()
                    row["decision_ts"] = m["decision"]
                    row["n_hist_windows"] = m["n_hist_windows"]
                    row["n_kept"] = m["n_kept"]
                    row["hist_mu"] = round(m["mu_hist"], 4)
                    row["hist_var"] = round(m["var_hist"], 4)
            else:
                row["n_elapsed_75"] = n_elapsed
                if m is not None:
                    row["n_hist_windows_75"] = m["n_hist_windows"]
        if model is None:
            out_rows.append(row)
            continue

        # resolver sanity check (tracker final bracket vs Gamma resolution)
        resolver_checked += 1
        if row["window_bracket_tracker"] and row["window_bracket_tracker"] != row["resolved_bracket"]:
            resolver_mismatch += 1

        prices = price_event(w["markets"], trades_by_cid, model["decision"])
        row["priced_brackets"] = sum(1 for x in prices if x is not None)
        if row["priced_brackets"] == 0:
            row["skip_reason"] = "no_executable_price_in_6h"
            out_rows.append(row)
            continue

        best = decide_trade(model, prices, w["brackets"])
        row["max_edge"] = round(best["edge"], 6) if best else ""
        row["best_idx"] = best["idx"] if best else ""
        row["best_label"] = w["markets"][best["idx"]]["groupItemTitle"].strip() if best else ""
        row["p_bought"] = round(best["p"], 6) if best else ""
        row["ask"] = round(best["ask"], 6) if best else ""
        row["fee"] = round(best["fee"], 6) if best else ""
        row["edge"] = round(best["edge"], 6) if best else ""
        if best and best.get("triggered"):
            row["triggered"] = True
            row["price_ts"] = datetime.fromtimestamp(best["price_ts"], timezone.utc).isoformat()
            payoff = 1.0 if best["idx"] == w["res_idx"] else 0.0
            row["payoff"] = payoff
            row["win"] = bool(payoff == 1.0)
            row["net_per_share"] = payoff - best["ask"] - best["fee"]
            row["net_per_dollar"] = row["net_per_share"] / best["ask"]
        else:
            row["skip_reason"] = "no_positive_edge"

        # log loss on priced brackets (needs realized bracket priced)
        idx = w["res_idx"]
        if prices[idx] is not None:
            avail = [i for i, x in enumerate(prices) if x is not None]
            if len(avail) >= 2:
                pc = [model["p_cons"][i] for i in avail]
                sc = sum(pc)
                q = [prices[i]["yes"] for i in avail]
                sq = sum(q)
                if sc > 0 and sq > 0:
                    pos = avail.index(idx)
                    pcl = max(pc[pos] / sc, 1e-9)
                    ql = max(q[pos] / sq, 1e-9)
                    logloss["cons"].append(-math.log(pcl))
                    logloss["mkt"].append(-math.log(ql))
                    praw = [model["p_raw"][i] for i in avail]
                    sraw = sum(praw)
                    if sraw > 0:
                        logloss["raw"].append(-math.log(max(praw[pos] / sraw, 1e-9)))
                    if model["nb"] is not None:
                        pnb = [model["nb"][i] for i in avail]
                        snb = sum(pnb)
                        if snb > 0:
                            logloss["nb"].append(-math.log(max(pnb[pos] / snb, 1e-9)))
                    logloss["n"] += 1

        # sensitivity at 75%
        model75 = None
        for frac in FRACS[1:]:
            decision75 = w["start"] + frac * w["dur"]
            n75 = int(np.searchsorted(p, decision75, side="left")) - int(np.searchsorted(p, w["start"], side="left"))
            model75 = empirical_model(p, w["end_local"], w["cfg"]["days"], frac, n75, w["brackets"])
        if model75 is not None:
            prices75 = price_event(w["markets"], trades_by_cid, model75["decision"])
            best75 = decide_trade(model75, prices75, w["brackets"])
            row["max_edge_75"] = round(best75["edge"], 6) if best75 else ""
            if best75 and best75.get("triggered"):
                row["triggered_75"] = True
                payoff75 = 1.0 if best75["idx"] == w["res_idx"] else 0.0
                row["net_per_share_75"] = payoff75 - best75["ask"] - best75["fee"]
                row["net_per_dollar_75"] = row["net_per_share_75"] / best75["ask"]
                row["win_75"] = bool(payoff75 == 1.0)
                row["decision_ts_75"] = model75["decision"]
            else:
                row["triggered_75"] = False
        out_rows.append(row)

    # ---- output
    df = pd.DataFrame(out_rows).sort_values(["series", "window_end_utc", "slug"]).reset_index(drop=True)
    csv_path = BASE / "events.csv"
    df.to_csv(csv_path, index=False, float_format="%.6f")

    modeled = [r for r in out_rows if r.get("n_hist_windows") is not None and r.get("skip_reason") != "insufficient_conditional_history"]
    priced = [r for r in out_rows if r.get("priced_brackets") not in ("", 0, None)]
    trig = [r for r in out_rows if r.get("triggered")]
    s50 = summarize(trig, "triggered", "net_per_share", "net_per_dollar", "win", "decision_ts")
    # sensitivity: explicit 75% fields, not the 50% fields
    s75 = summarize(out_rows, "triggered_75", "net_per_share_75", "net_per_dollar_75",
                    "win_75", "decision_ts_75")
    all_med, all_mean, all_hit = all_event_summary(out_rows, "net_per_share", "triggered")
    all_med75, all_mean75, all_hit75 = all_event_summary(out_rows, "net_per_share_75", "triggered_75")

    print("样本漏斗：")
    print(f"  全部 closed 事件={len(work)}；模型可建模={len(modeled)}；有可成交价={len(priced)}；50% 触发={len(trig)}")
    for reason, cnt in pd.Series([r.get("skip_reason", "") for r in out_rows if not r.get("triggered")]).value_counts().items():
        print(f"  skip {reason or '(其他)'}: {cnt}")
    print()

    print("主口径（50% 决策点，保守经验分布，fee=0.05，hold-to-resolution）：")
    if s50["n"] == 0:
        print("  触发事件=0，无法计算。")
    else:
        print(f"  触发事件数 n={s50['n']}，覆盖 ISO 周={s50['weeks']}")
        print(f"  每份净收益: median={s50['median_share']:.6f}, mean={s50['mean_share']:.6f}")
        print(f"  每 $1 本金净收益: median={s50['median_dollar']:.6f}, mean={s50['mean_dollar']:.6f}")
        print(f"  命中率={s50['hit']:.4f} ({int(round(s50['hit']*s50['n']))}/{s50['n']})")
        if s50["ci_lo"] is not None:
            print(f"  ISO 周 block bootstrap 95% CI of mean(每份) = [{s50['ci_lo']:.6f}, {s50['ci_hi']:.6f}] (B={BOOT_N}, seed={SEED})")
        else:
            print("  ISO 周 block bootstrap: 周数不足，未取到")
    print(f"  all-event 口径（未触发=0）: median={all_med:.6f}, mean={all_mean:.6f}, hit={all_hit:.4f}")
    print()

    print("敏感性（75% 决策点，其余口径相同）：")
    if s75["n"] == 0:
        print("  触发事件=0，无法计算。")
    else:
        print(f"  触发事件数 n={s75['n']}，覆盖 ISO 周={s75['weeks']}")
        print(f"  每份净收益: median={s75['median_share']:.6f}, mean={s75['mean_share']:.6f}")
        print(f"  每 $1 本金净收益: median={s75['median_dollar']:.6f}, mean={s75['mean_dollar']:.6f}")
        print(f"  命中率={s75['hit']:.4f} ({int(round(s75['hit']*s75['n']))}/{s75['n']})")
        if s75["ci_lo"] is not None:
            print(f"  ISO 周 block bootstrap 95% CI of mean(每份) = [{s75['ci_lo']:.6f}, {s75['ci_hi']:.6f}]")
        print(f"  all-event 口径: median={all_med75:.6f}, mean={all_mean75:.6f}, hit={all_hit75:.4f}")
    print()

    print("模型 vs 市场 对数损失（priced events，按有价档位重新归一化）：")
    if logloss["n"] == 0:
        print("  未取到可用事件")
    else:
        print(f"  n={logloss['n']}")
        print(f"  保守经验模型: {np.mean(logloss['cons']):.6f}")
        print(f"  原始经验模型: {np.mean(logloss['raw']):.6f}")
        if logloss["nb"]:
            print(f"  NB 平滑检查:  {np.mean(logloss['nb']):.6f}")
        else:
            print("  NB 平滑检查:  未取到")
        print(f"  市场归一化价: {np.mean(logloss['mkt']):.6f}")
    print()

    print("结算源一致性（tracker 最终计数落档 vs Gamma resolved 档）：")
    print(f"  可核对={resolver_checked}, 不一致={resolver_mismatch}")
    print()

    # ---- FROZEN entry scope (PR #16): Elon 48h only, one result per 48h by settlement time
    erows, kept_all, kept_trig = frozen_scope(out_rows)
    e_rows = [r for r in out_rows if r.get("series") == "elon48"]
    s_e = summarize(e_rows, "triggered", "net_per_share", "net_per_dollar", "win", "decision_ts")
    s_ka = summarize(kept_all, "triggered", "net_per_share", "net_per_dollar", "win", "decision_ts")
    s_kt = summarize(kept_trig, "triggered", "net_per_share", "net_per_dollar", "win", "decision_ts")
    print("冻结 q005 口径（entry 原文：主样本仅 Elon 48h；重叠窗口按结算时刻每 48h 去重；50% 决策点）：")
    print(f"  Elon48 事件行={len(e_rows)}；50% 触发（未去重）: n={s_e.get('n',0)}, "
          f"median={s_e.get('median_share',float('nan')):.6f}, mean={s_e.get('mean_share',float('nan')):.6f}, "
          f"hit={s_e.get('hit',float('nan')):.4f}")
    print(f"  去重 A（先对全部 Elon48 事件按 window_end 每 48h 保留 1 个）: 事件={len(kept_all)}, "
          f"触发 n={s_ka.get('n',0)}, median={s_ka.get('median_share',float('nan')):.6f}, "
          f"mean={s_ka.get('mean_share',float('nan')):.6f}, hit={s_ka.get('hit',float('nan')):.4f}")
    print(f"  去重 B（先取触发行，再按 window_end 每 48h 保留 1 个）: n={s_kt.get('n',0)}, "
          f"median={s_kt.get('median_share',float('nan')):.6f}, mean={s_kt.get('mean_share',float('nan')):.6f}, "
          f"hit={s_kt.get('hit',float('nan')):.4f}")
    if s_ka.get("n", 0) < 30:
        frozen_verdict = "INSUFFICIENT"
    elif (s_ka["median_share"] <= 0) or (s_ka["hit"] < 0.5 and s_ka["mean_share"] <= 0):
        frozen_verdict = "FAIL"
    else:
        frozen_verdict = "PASS"
    print(f"  冻结判据（median≤0，或 hit<0.5 且 mean≤0；n≥30）→ {frozen_verdict}"
          f"（A 口径 n={s_ka.get('n',0)}）")
    print()

    # ---- verdict
    print("判定（冻结标准：逐事件买入侧扣费后净收益中位数 ≤0 → FAIL；需 ≥30 个独立事件结果）：")
    if s50["n"] < 30:
        verdict = "INSUFFICIENT"
        print(f"  INSUFFICIENT — 50% 触发样本 {s50['n']} < 30，不能按冻结标准判 PASS/FAIL。")
    elif s50["median_share"] <= 0:
        verdict = "FAIL"
        print(f"  FAIL — 触发样本 n={s50['n']}，每份净收益中位数 {s50['median_share']:.6f} ≤ 0。")
    else:
        verdict = "PASS"
        print(f"  PASS — 触发样本 n={s50['n']}，每份净收益中位数 {s50['median_share']:.6f} > 0。")
    print(f"  VERDICT={verdict}")
    print()
    print(f"输出: {csv_path.name} ({csv_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
